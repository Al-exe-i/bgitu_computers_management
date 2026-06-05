from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from dependencies.audit_actor import get_audit_ctx
from dependencies.audit_actor import get_user_audit_actor
from dependencies.events import get_identity_event_dispatcher
from dependencies.user import get_user_service
from dependencies.user_session_service import get_user_session_service
from main import app
from utils.tokens import hash_refresh_token


@dataclass(slots=True)
class DummyAudit:
    meta: dict = field(
        default_factory=lambda: {
            "ip": "127.0.0.1",
            "user_agent": "pytest",
            "path": "/api/v1/token",
            "method": "POST",
        }
    )
    logs: list[dict] = field(default_factory=list)

    async def log(self, **kwargs) -> None:
        self.logs.append(kwargs)


@dataclass(slots=True)
class DummyUserAudit:
    user: SimpleNamespace
    meta: dict = field(
        default_factory=lambda: {
            "ip": "127.0.0.1",
            "user_agent": "pytest",
            "path": "/api/v1/sessions",
            "method": "GET",
        }
    )
    logs: list[dict] = field(default_factory=list)

    async def log(self, **kwargs) -> None:
        self.logs.append(kwargs)


class DummyUserService:
    def __init__(self, *, user_by_email=None, user_by_id=None) -> None:
        self.user_by_email = user_by_email
        self.user_by_id = user_by_id
        self.bumped_user_ids: list[int] = []

    async def get_by_email(self, email: str):
        if self.user_by_email and self.user_by_email.email == email:
            return self.user_by_email
        return None

    async def get(self, user_id: int):
        if self.user_by_id and self.user_by_id.id == user_id:
            return self.user_by_id
        return None

    async def bump_access_token_version(self, user_id: int) -> int:
        self.bumped_user_ids.append(user_id)
        return 1


class DummySessionRepo:
    def __init__(self, rows=None) -> None:
        self.rows = rows or []
        self.list_calls: list[dict] = []

    async def list_by_user(self, user_id: int, include_inactive: bool = False):
        self.list_calls.append(
            {"user_id": user_id, "include_inactive": include_inactive}
        )
        return list(self.rows)


class DummySessionService:
    def __init__(self, *, current_session=None, repo_rows=None, current_sid=None) -> None:
        self.current_session = current_session
        self.current_sid = current_sid
        self.created_sessions: list[dict] = []
        self.rotated_tokens: list[dict] = []
        self.revoked_sids: list[str] = []
        self.revoked_user_ids: list[int] = []
        self.repo = DummySessionRepo(repo_rows)

    @property
    def list_calls(self) -> list[dict]:
        return self.repo.list_calls

    @staticmethod
    def new_sid() -> str:
        return "sid-1"

    async def create_session(self, **kwargs):
        self.created_sessions.append(kwargs)
        return SimpleNamespace(**kwargs)

    async def get_active_by_refresh_token(self, refresh_token: str):
        if self.current_session and refresh_token == "old-refresh-token":
            return self.current_session
        return None

    async def rotate_refresh_token(self, **kwargs) -> bool:
        self.rotated_tokens.append(kwargs)
        return True

    async def get_current_sid(self, refresh_token: str | None):
        if not refresh_token:
            return None
        if self.current_sid is not None:
            return self.current_sid
        if self.current_session is not None:
            return self.current_session.sid
        return None

    async def list_by_user(self, user_id: int, include_inactive: bool = False):
        return await self.repo.list_by_user(user_id, include_inactive=include_inactive)

    async def revoke(self, sid: str) -> None:
        self.revoked_sids.append(sid)

    async def revoke_all_for_user(self, user_id: int) -> None:
        self.revoked_user_ids.append(user_id)


class DummyEventDispatcher:
    async def dispatch(self, events) -> None:
        return None


def override_dependencies(*, user_service, session_service, audit=None, user_audit=None):
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_user_session_service] = lambda: session_service
    app.dependency_overrides[get_identity_event_dispatcher] = lambda: DummyEventDispatcher()
    if audit is not None:
        app.dependency_overrides[get_audit_ctx] = lambda: audit
    if user_audit is not None:
        app.dependency_overrides[get_user_audit_actor] = lambda: user_audit


def clear_dependency_overrides() -> None:
    app.dependency_overrides.clear()


def test_login_endpoint_returns_tokens_and_creates_session() -> None:
    from core.security import get_password_hash

    user = SimpleNamespace(
        id=7,
        email="user@example.com",
        password=get_password_hash("secret123"),
    )
    sessions = DummySessionService()
    audit = DummyAudit()
    override_dependencies(
        user_service=DummyUserService(user_by_email=user),
        session_service=sessions,
        audit=audit,
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/token",
                data={"username": "user@example.com", "password": "secret123"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
        assert sessions.created_sessions == [
            {
                "user_id": 7,
                "sid": "sid-1",
                "refresh_token_hash": hash_refresh_token(response.cookies["refresh_token"]),
                "ip": "127.0.0.1",
                "user_agent": "pytest",
            }
        ]
        assert audit.logs[0]["action"] == "auth.login"
        assert audit.logs[0]["payload"]["sid"] == "sid-1"
    finally:
        clear_dependency_overrides()


def test_login_endpoint_rejects_invalid_credentials() -> None:
    from core.security import get_password_hash

    user = SimpleNamespace(
        id=7,
        email="user@example.com",
        password=get_password_hash("correct-password"),
    )
    sessions = DummySessionService()
    audit = DummyAudit()
    override_dependencies(
        user_service=DummyUserService(user_by_email=user),
        session_service=sessions,
        audit=audit,
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/token",
                data={"username": "user@example.com", "password": "wrong-password"},
            )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"
        assert sessions.created_sessions == []
        assert audit.logs == []
    finally:
        clear_dependency_overrides()


def test_refresh_endpoint_rotates_refresh_token() -> None:
    current_session = SimpleNamespace(user_id=7, sid="sid-1")
    user = SimpleNamespace(id=7, email="user@example.com")
    sessions = DummySessionService(current_session=current_session)
    audit = DummyAudit()
    override_dependencies(
        user_service=DummyUserService(user_by_id=user),
        session_service=sessions,
        audit=audit,
    )

    try:
        with TestClient(app) as client:
            client.cookies.set("refresh_token", "old-refresh-token")
            response = client.post("/api/v1/refresh")

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.cookies["refresh_token"] != "old-refresh-token"
        assert len(sessions.rotated_tokens) == 1
        assert sessions.rotated_tokens[0]["sid"] == "sid-1"
        assert sessions.rotated_tokens[0]["old_refresh_token"] == "old-refresh-token"
        assert sessions.rotated_tokens[0]["new_refresh_token"] == response.cookies["refresh_token"]
        assert audit.logs[0]["action"] == "auth.refresh"
    finally:
        clear_dependency_overrides()


def test_logout_endpoint_revokes_current_session_and_clears_cookies() -> None:
    sessions = DummySessionService(current_session=SimpleNamespace(user_id=7, sid="sid-1"))
    audit = DummyAudit()
    users = DummyUserService()
    override_dependencies(
        user_service=users,
        session_service=sessions,
        audit=audit,
    )

    try:
        with TestClient(app) as client:
            client.cookies.set("access_token", "access-token")
            client.cookies.set("refresh_token", "old-refresh-token")
            response = client.post("/api/v1/logout")

        assert response.status_code == 200
        assert response.json() == {"message": "Successfully logged out"}
        assert sessions.revoked_sids == ["sid-1"]
        assert users.bumped_user_ids == [7]
        assert audit.logs[0]["action"] == "auth.logout"
        assert audit.logs[0]["payload"]["sid"] == "sid-1"

        cookies = response.headers.get_list("set-cookie")
        assert any("access_token=\"\"" in cookie and "Max-Age=0" in cookie for cookie in cookies)
        assert any("refresh_token=\"\"" in cookie and "Max-Age=0" in cookie for cookie in cookies)
    finally:
        clear_dependency_overrides()


def test_logout_all_endpoint_revokes_all_user_sessions() -> None:
    sessions = DummySessionService()
    user_audit = DummyUserAudit(user=SimpleNamespace(id=7))
    users = DummyUserService()
    override_dependencies(
        user_service=users,
        session_service=sessions,
        user_audit=user_audit,
    )

    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/logout_all")

        assert response.status_code == 200
        assert response.json() == {"message": "Successfully logged out"}
        assert sessions.revoked_user_ids == [7]
        assert users.bumped_user_ids == [7]
        assert user_audit.logs[0]["action"] == "auth.logout_all"
        assert user_audit.logs[0]["payload"]["user_id"] == 7
    finally:
        clear_dependency_overrides()


def test_sessions_endpoint_marks_current_and_active_flags() -> None:
    now = datetime.now(timezone.utc)
    repo_rows = [
        SimpleNamespace(
            sid="sid-1",
            created_at=now - timedelta(days=2),
            last_used_at=now - timedelta(hours=1),
            expires_at=now + timedelta(days=1),
            revoked_at=None,
            ip="127.0.0.1",
            user_agent="pytest",
        ),
        SimpleNamespace(
            sid="sid-2",
            created_at=now - timedelta(days=3),
            last_used_at=None,
            expires_at=now + timedelta(days=1),
            revoked_at=now,
            ip=None,
            user_agent=None,
        ),
    ]
    sessions = DummySessionService(repo_rows=repo_rows, current_sid="sid-1")
    user_audit = DummyUserAudit(user=SimpleNamespace(id=7))
    override_dependencies(
        user_service=DummyUserService(),
        session_service=sessions,
        user_audit=user_audit,
    )

    try:
        with TestClient(app) as client:
            client.cookies.set("refresh_token", "old-refresh-token")
            response = client.get("/api/v1/sessions?include_inactive=true")

        assert response.status_code == 200
        assert sessions.list_calls == [
            {"user_id": 7, "include_inactive": True}
        ]

        payload = response.json()
        assert payload[0]["sid"] == "sid-1"
        assert payload[0]["is_current"] is True
        assert payload[0]["is_active"] is True
        assert payload[1]["sid"] == "sid-2"
        assert payload[1]["is_current"] is False
        assert payload[1]["is_active"] is False
    finally:
        clear_dependency_overrides()
