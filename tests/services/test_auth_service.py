import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from core.exceptions import InvalidCredentialsError
from core.security import get_password_hash
from services.auth_service import AuthService
from utils.tokens import hash_refresh_token


class FakeUserService:
    def __init__(self, users: list[SimpleNamespace]) -> None:
        self.users = users

    async def get_by_email(self, email: str):
        return next((user for user in self.users if user.email == email), None)

    async def get(self, user_id: int):
        return next((user for user in self.users if user.id == user_id), None)


class FakeSessionService:
    def __init__(self, rows: list[SimpleNamespace] | None = None) -> None:
        self.rows = rows or []
        self.created_sessions: list[dict] = []
        self.list_calls: list[dict] = []
        self.current_sid: str | None = None

    @staticmethod
    def new_sid() -> str:
        return "sid-1"

    async def create_session(self, **kwargs):
        self.created_sessions.append(kwargs)
        return SimpleNamespace(**kwargs)

    async def get_current_sid(self, refresh_token: str | None):
        return self.current_sid if refresh_token else None

    async def list_by_user(self, user_id: int, include_inactive: bool = False):
        self.list_calls.append(
            {"user_id": user_id, "include_inactive": include_inactive}
        )
        return self.rows


def test_login_creates_session_and_returns_token_pair() -> None:
    async def scenario() -> None:
        user = SimpleNamespace(
            id=7,
            email="user@example.com",
            password=get_password_hash("secret123"),
        )
        sessions = FakeSessionService()
        service = AuthService(FakeUserService([user]), sessions)

        result = await service.login(
            email="user@example.com",
            password="secret123",
            ip="127.0.0.1",
            user_agent="pytest",
        )

        assert result.user_id == 7
        assert result.sid == "sid-1"
        assert result.access_token
        assert sessions.created_sessions == [
            {
                "user_id": 7,
                "sid": "sid-1",
                "refresh_token_hash": hash_refresh_token(result.refresh_token),
                "ip": "127.0.0.1",
                "user_agent": "pytest",
            }
        ]

    asyncio.run(scenario())


def test_login_rejects_invalid_password() -> None:
    async def scenario() -> None:
        user = SimpleNamespace(
            id=7,
            email="user@example.com",
            password=get_password_hash("secret123"),
        )
        service = AuthService(FakeUserService([user]), FakeSessionService())

        with pytest.raises(InvalidCredentialsError):
            await service.login(
                email="user@example.com",
                password="wrong-password",
            )

    asyncio.run(scenario())


def test_list_user_sessions_marks_current_and_active_sessions() -> None:
    async def scenario() -> None:
        now = datetime.now(timezone.utc)
        sessions = FakeSessionService(
            rows=[
                SimpleNamespace(
                    sid="sid-1",
                    created_at=now,
                    last_used_at=now,
                    expires_at=now + timedelta(days=1),
                    revoked_at=None,
                    ip="127.0.0.1",
                    user_agent="pytest",
                ),
                SimpleNamespace(
                    sid="sid-2",
                    created_at=now,
                    last_used_at=None,
                    expires_at=now + timedelta(days=1),
                    revoked_at=now,
                    ip=None,
                    user_agent=None,
                ),
            ]
        )
        sessions.current_sid = "sid-1"
        service = AuthService(FakeUserService([]), sessions)

        result = await service.list_user_sessions(
            user_id=7,
            include_inactive=True,
            refresh_token="refresh-token",
        )

        assert sessions.list_calls == [{"user_id": 7, "include_inactive": True}]
        assert [session.sid for session in result] == ["sid-1", "sid-2"]
        assert result[0].is_current is True
        assert result[0].is_active is True
        assert result[1].is_current is False
        assert result[1].is_active is False

    asyncio.run(scenario())
