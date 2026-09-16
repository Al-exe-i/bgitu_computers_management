from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from api.v1.endpoints.auth import router as auth_router
from core.exception_handlers import register_exception_handlers
from db import session as db_session
from db.post_commit import add_post_commit_hook
from db.session import session_dep
from db.transaction import SessionTransaction
from dependencies.audit_actor import get_audit_ctx
from dependencies.identity import get_identity_auth_use_cases
from dependencies.user import get_user_service
from modules.identity.application.auth import IdentityAuthUseCases
from modules.identity.services.auth import AuthService
from utils.tokens import issue_access_token
from websocket.routes import router as sse_router


class RecordingSession:
    def __init__(self):
        self.info = {}
        self.calls = []
        self.pending = {}
        self.saved = {}
        self.closed = False
        self.fail_commit = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.closed = True
        self.calls.append("close")

    async def commit(self):
        self.calls.append("commit")
        if self.fail_commit:
            raise RuntimeError("commit failed")
        self.saved = self.pending.copy()

    async def rollback(self):
        self.calls.append("rollback")
        self.pending = self.saved.copy()


@pytest.fixture
def session(monkeypatch):
    session = RecordingSession()
    monkeypatch.setattr(db_session, "session_factory", lambda: session)
    return session


@pytest.mark.parametrize("fail_commit", [False, True])
def test_commit_finishes_before_success_response_and_cookie(session, fail_commit):
    app = FastAPI()
    session.fail_commit = fail_commit

    @app.post("/")
    async def endpoint(db: session_dep, response: Response):
        db.pending["changed"] = True
        add_post_commit_hook(db, lambda: db.calls.append("hook"))
        response.set_cookie("access_token", "must-not-leak-on-failure")
        return {"ok": True}

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/")

    assert session.closed
    assert session.info == {}
    if fail_commit:
        assert response.status_code == 500
        assert "set-cookie" not in response.headers
        assert session.saved == {}
        assert session.calls == ["commit", "rollback", "close"]
    else:
        assert response.status_code == 200
        assert "access_token" in response.cookies
        assert session.saved == {"changed": True}
        assert session.calls == ["commit", "hook", "close"]


@pytest.mark.parametrize("fail_commit", [False, True])
def test_notifications_sse_releases_db_before_connecting(session, fail_commit):
    app = FastAPI()
    app.include_router(sse_router)
    session.fail_commit = fail_commit
    user = SimpleNamespace(id=7, access_token_version=0)

    def user_service(db: session_dep):
        return SimpleNamespace(get_for_authentication=AsyncMock(return_value=user))

    async def connect(connection, **kwargs):
        assert session.closed
        await connection.close()
        return "connection-1"

    realtime = SimpleNamespace(
        config=SimpleNamespace(enabled=True, heartbeat_interval_seconds=1),
        connect=AsyncMock(side_effect=connect),
        disconnect=AsyncMock(),
    )
    app.state.realtime = realtime
    app.dependency_overrides[get_user_service] = user_service

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            "/events/notifications",
            headers={"Authorization": f"Bearer {issue_access_token(7)}"},
        )

    if fail_commit:
        assert response.status_code == 500
        realtime.connect.assert_not_awaited()
    else:
        assert response.status_code == 200
        assert "retry: 3000" in response.text
        realtime.connect.assert_awaited_once()
        realtime.disconnect.assert_awaited_once_with("connection-1")


@pytest.mark.parametrize("replayed", [False, True])
@pytest.mark.parametrize("failure", [None, "audit", "commit"])
def test_refresh_denial_commits_security_changes_but_not_partial_failures(session, replayed, failure):
    app = FastAPI()
    app.include_router(auth_router)
    register_exception_handlers(app)
    session.fail_commit = failure == "commit"
    user_session = SimpleNamespace(user_id=7, sid="sid-1")

    async def revoke(sid):
        session.pending["revoked"] = sid

    async def bump(user_id):
        session.pending["version"] = 1

    async def log(**kwargs):
        if failure == "audit":
            raise RuntimeError("audit failed")
        session.pending["audit"] = kwargs["action"]

    sessions = SimpleNamespace(
        get_active_by_refresh_token=AsyncMock(return_value=None if replayed else user_session),
        get_active_by_used_refresh_token=AsyncMock(return_value=user_session),
        rotate_refresh_token=AsyncMock(return_value=False),
        revoke=AsyncMock(side_effect=revoke),
    )
    users = SimpleNamespace(
        get=AsyncMock(return_value=SimpleNamespace(id=7)),
        bump_access_token_version=AsyncMock(side_effect=bump),
    )

    def use_cases(db: session_dep):
        return IdentityAuthUseCases(
            auth_service=AuthService(users, sessions),
            transaction=SessionTransaction(db),
        )

    app.dependency_overrides[get_identity_auth_use_cases] = use_cases
    app.dependency_overrides[get_audit_ctx] = lambda: SimpleNamespace(meta={}, log=log)
    with TestClient(app, raise_server_exceptions=False) as client:
        client.cookies.set("refresh_token", "previous-token")
        response = client.post("/refresh")

    assert "set-cookie" not in response.headers
    if failure:
        assert response.status_code == 500
        assert session.saved == {}
    else:
        assert response.status_code == 401
        assert session.saved == {"revoked": "sid-1", "version": 1, "audit": "auth.refresh_reuse"}
    assert session.closed
