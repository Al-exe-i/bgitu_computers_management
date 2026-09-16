import asyncio
from unittest.mock import AsyncMock

import pytest

from core.exceptions import (
    RefreshTokenReuseDetectedError,
)
from modules.identity.application import IdentityAuthUseCases
from modules.identity.application.auth import LOGIN_EVENT_NAME, LOGOUT_ALL_EVENT_NAME
from modules.identity.contracts import TokenIssueResult
from modules.identity.events import AuthSecurityNotificationEvent


class FakeAuthService:
    async def login(self, **kwargs):
        return TokenIssueResult(
            user_id=7,
            user_email="user@example.com",
            sid="sid-1",
            access_token="access",
            refresh_token="refresh",
        )

    async def refresh(self, **kwargs):
        if kwargs["refresh_token"] == "reused":
            raise RefreshTokenReuseDetectedError(user_id=7, sid="sid-1")
        return TokenIssueResult(
            user_id=7,
            user_email="user@example.com",
            sid="sid-1",
            access_token="new-access",
            refresh_token="new-refresh",
        )

    async def logout_all(self, *, user_id: int) -> None:
        return None


class FakeAudit:
    def __init__(self) -> None:
        self.logs: list[dict] = []

    async def log(self, **kwargs):
        self.logs.append(kwargs)


def make_use_cases(auth_service=None) -> IdentityAuthUseCases:
    return IdentityAuthUseCases(
        auth_service=auth_service or FakeAuthService(),
        transaction=AsyncMock(),
    )


def test_login_writes_audit_and_returns_auth_security_event() -> None:
    async def scenario() -> None:
        audit = FakeAudit()
        use_cases = make_use_cases()

        result = await use_cases.login(
            email="user@example.com",
            password="secret",
            ip="127.0.0.1",
            user_agent="pytest",
            audit=audit,
        )

        assert result.tokens.access_token == "access"
        assert audit.logs == [
            {
                "action": "auth.login",
                "entity_type": "user",
                "entity_id": 7,
                "payload": {"email": "user@example.com", "sid": "sid-1"},
                "user_id": 7,
            }
        ]
        assert result.events == [
            AuthSecurityNotificationEvent(
                user_id=7,
                event_name=LOGIN_EVENT_NAME,
                ip="127.0.0.1",
                user_agent="pytest",
            )
        ]

    asyncio.run(scenario())


def test_refresh_reuse_writes_audit_before_reraising() -> None:
    async def scenario() -> None:
        audit = FakeAudit()
        use_cases = make_use_cases()

        with pytest.raises(RefreshTokenReuseDetectedError):
            await use_cases.refresh(
                refresh_token="reused",
                ip="127.0.0.1",
                user_agent="pytest",
                audit=audit,
            )

        use_cases.transaction.commit.assert_awaited_once()

        assert audit.logs == [
            {
                "action": "auth.refresh_reuse",
                "entity_type": "user_session",
                "entity_id": None,
                "payload": {"sid": "sid-1"},
                "user_id": 7,
            }
        ]

    asyncio.run(scenario())


def test_logout_all_writes_audit_and_returns_auth_security_event() -> None:
    async def scenario() -> None:
        audit = FakeAudit()
        use_cases = make_use_cases()

        result = await use_cases.logout_all(
            user_id=7,
            ip="127.0.0.1",
            user_agent="pytest",
            audit=audit,
        )

        assert result.logout.user_id == 7
        assert result.logout.sid is None
        assert audit.logs == [
            {
                "action": "auth.logout_all",
                "entity_type": "user_session",
                "entity_id": None,
                "payload": {"user_id": 7},
            }
        ]
        assert result.events == [
            AuthSecurityNotificationEvent(
                user_id=7,
                event_name=LOGOUT_ALL_EVENT_NAME,
                ip="127.0.0.1",
                user_agent="pytest",
            )
        ]

    asyncio.run(scenario())
