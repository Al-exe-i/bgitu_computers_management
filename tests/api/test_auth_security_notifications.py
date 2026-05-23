from dataclasses import dataclass, field
from types import SimpleNamespace

from fastapi.testclient import TestClient

from core.config import settings
from dependencies.audit_actor import get_audit_ctx
from dependencies.events import get_identity_event_dispatcher
from dependencies.user import get_user_service
from dependencies.user_session_service import get_user_session_service
from main import app


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


class DummyUserService:
    def __init__(self, user_by_email) -> None:
        self.user_by_email = user_by_email

    async def get_by_email(self, email: str):
        if self.user_by_email and self.user_by_email.email == email:
            return self.user_by_email
        return None


class DummySessionService:
    created_sessions: list[dict]

    def __init__(self) -> None:
        self.created_sessions = []

    @staticmethod
    def new_sid() -> str:
        return "sid-1"

    async def create_session(self, **kwargs):
        self.created_sessions.append(kwargs)
        return SimpleNamespace(**kwargs)


def clear_dependency_overrides() -> None:
    app.dependency_overrides.clear()


def test_login_endpoint_calls_auth_security_enqueue(monkeypatch) -> None:
    from core.security import get_password_hash

    user = SimpleNamespace(
        id=7,
        email="user@example.com",
        password=get_password_hash("secret123"),
    )
    audit = DummyAudit()
    sessions = DummySessionService()
    calls: list[dict] = []

    monkeypatch.setattr(settings.telegram, "enabled", True)

    class DummyEventDispatcher:
        async def dispatch(self, events) -> None:
            calls.extend(
                {
                    "user_id": event.user_id,
                    "event_name": event.event_name,
                    "ip": event.ip,
                    "user_agent": event.user_agent,
                }
                for event in events
            )

    app.dependency_overrides[get_user_service] = lambda: DummyUserService(user)
    app.dependency_overrides[get_user_session_service] = lambda: sessions
    app.dependency_overrides[get_audit_ctx] = lambda: audit
    app.dependency_overrides[get_identity_event_dispatcher] = lambda: DummyEventDispatcher()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/token",
                data={"username": "user@example.com", "password": "secret123"},
            )

        assert response.status_code == 200
        assert calls == [
            {
                "user_id": 7,
                "event_name": "Выполнен вход в аккаунт",
                "ip": "127.0.0.1",
                "user_agent": "pytest",
            }
        ]
    finally:
        clear_dependency_overrides()
