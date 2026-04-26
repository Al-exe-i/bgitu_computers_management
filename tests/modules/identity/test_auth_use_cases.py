import asyncio
from types import SimpleNamespace

import pytest

from core.exceptions import (
    InviteAssignedToAnotherEmailError,
    InviteUserAlreadyExistsError,
    RefreshTokenReuseDetectedError,
)
from models.user import UserRole
from modules.identity.application import IdentityAuthUseCases
from modules.identity.application.auth import LOGIN_EVENT_NAME, LOGOUT_ALL_EVENT_NAME
from modules.identity.events import AuthSecurityNotificationEvent
from schemas.invite import RegisterByInviteRequest
from services.invite_service import InviteRegistrationData
from services.auth_service import LogoutResult, TokenIssueResult


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


class FakeInviteService:
    def __init__(
        self,
        invite: InviteRegistrationData | None = None,
    ) -> None:
        self.invite = invite or InviteRegistrationData(
            id=5,
            target_email=None,
            target_role=UserRole.teacher,
        )
        self.tokens: list[str] = []
        self.marked_used: list[dict] = []

    async def get_active_for_registration(self, token: str) -> InviteRegistrationData:
        self.tokens.append(token)
        return self.invite

    async def mark_used(self, invite_id: int, *, used_by_user_id: int) -> None:
        self.marked_used.append(
            {
                "invite_id": invite_id,
                "used_by_user_id": used_by_user_id,
            }
        )


class FakeUserService:
    def __init__(self, existing_user=None) -> None:
        self.existing_user = existing_user
        self.created: list[object] = []
        self.lookup_emails: list[str] = []

    async def get_by_email(self, email: str):
        self.lookup_emails.append(email)
        return self.existing_user

    async def create(self, data):
        self.created.append(data)
        return SimpleNamespace(
            id=7,
            email=data.email,
            role=data.role,
        )


def make_use_cases(auth_service=None, invite_service=None, user_service=None) -> IdentityAuthUseCases:
    return IdentityAuthUseCases(
        auth_service=auth_service or FakeAuthService(),
        invite_service=invite_service,
        user_service=user_service,
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

        assert isinstance(result.logout, LogoutResult)
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


def test_register_by_invite_creates_user_marks_invite_used_and_writes_audit() -> None:
    async def scenario() -> None:
        audit = FakeAudit()
        invite_service = FakeInviteService()
        user_service = FakeUserService()
        use_cases = make_use_cases(
            invite_service=invite_service,
            user_service=user_service,
        )

        result = await use_cases.register_by_invite(
            data=RegisterByInviteRequest(
                token="invite-token",
                name="Alex",
                surname="Ivanov",
                email="new@example.com",
                password="secret123",
            ),
            audit=audit,
        )

        assert result.registration.user_id == 7
        assert result.registration.email == "new@example.com"
        assert result.registration.role == str(UserRole.teacher.value)
        assert invite_service.tokens == ["invite-token"]
        assert invite_service.marked_used == [{"invite_id": 5, "used_by_user_id": 7}]
        assert user_service.lookup_emails == ["new@example.com"]
        assert user_service.created[0].email == "new@example.com"
        assert user_service.created[0].role == UserRole.teacher
        assert audit.logs == [
            {
                "action": "auth.register_by_invite",
                "entity_type": "user",
                "entity_id": 7,
                "payload": {"email": "new@example.com", "role": str(UserRole.teacher.value)},
                "user_id": 7,
            }
        ]

    asyncio.run(scenario())


def test_register_by_invite_rejects_email_mismatch_before_user_create() -> None:
    async def scenario() -> None:
        audit = FakeAudit()
        invite_service = FakeInviteService(
            InviteRegistrationData(
                id=5,
                target_email="target@example.com",
                target_role=UserRole.teacher,
            )
        )
        user_service = FakeUserService()
        use_cases = make_use_cases(
            invite_service=invite_service,
            user_service=user_service,
        )

        with pytest.raises(InviteAssignedToAnotherEmailError):
            await use_cases.register_by_invite(
                data=RegisterByInviteRequest(
                    token="invite-token",
                    email="other@example.com",
                    password="secret123",
                ),
                audit=audit,
            )

        assert user_service.lookup_emails == []
        assert user_service.created == []
        assert invite_service.marked_used == []
        assert audit.logs == []

    asyncio.run(scenario())


def test_register_by_invite_rejects_existing_user_before_marking_invite_used() -> None:
    async def scenario() -> None:
        audit = FakeAudit()
        invite_service = FakeInviteService()
        user_service = FakeUserService(existing_user=SimpleNamespace(id=9))
        use_cases = make_use_cases(
            invite_service=invite_service,
            user_service=user_service,
        )

        with pytest.raises(InviteUserAlreadyExistsError):
            await use_cases.register_by_invite(
                data=RegisterByInviteRequest(
                    token="invite-token",
                    email="new@example.com",
                    password="secret123",
                ),
                audit=audit,
            )

        assert user_service.lookup_emails == ["new@example.com"]
        assert user_service.created == []
        assert invite_service.marked_used == []
        assert audit.logs == []

    asyncio.run(scenario())
