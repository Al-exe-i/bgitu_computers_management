from dataclasses import dataclass

from loguru import logger

from core.exceptions import (
    IdentityError,
    InviteAssignedToAnotherEmailError,
    InviteUserAlreadyExistsError,
    RefreshTokenReuseDetectedError,
    UserAlreadyExistsError,
)
from schemas.invite import InvitePreviewResponse, RegisterByInviteRequest, RegisterByInviteResponse
from schemas.user import UserCreate
from schemas.user_session import UserSessionOut
from modules.identity.events import AuthSecurityNotificationEvent, IdentityEvent
from modules.identity.ports import (
    AuditLogger,
    AuthServicePort,
    InviteServicePort,
    LogoutResult,
    RevokeSessionResult,
    TokenIssueResult,
    UserServicePort,
)


LOGIN_EVENT_NAME = "Выполнен вход в аккаунт"
LOGOUT_ALL_EVENT_NAME = "Выполнен выход на всех устройствах"


@dataclass(slots=True, frozen=True)
class IdentityTokenResult:
    tokens: TokenIssueResult
    events: list[IdentityEvent]


@dataclass(slots=True, frozen=True)
class IdentityLogoutState:
    user_id: int | None
    sid: str | None


@dataclass(slots=True, frozen=True)
class IdentityLogoutResult:
    logout: LogoutResult
    events: list[IdentityEvent]


@dataclass(slots=True, frozen=True)
class IdentityRevokeSessionResult:
    session: RevokeSessionResult
    events: list[IdentityEvent]


@dataclass(slots=True, frozen=True)
class IdentityRegisterResult:
    registration: RegisterByInviteResponse
    events: list[IdentityEvent]


class IdentityAuthUseCases:
    def __init__(
        self,
        *,
        auth_service: AuthServicePort,
        invite_service: InviteServicePort,
        user_service: UserServicePort,
    ) -> None:
        self.auth_service = auth_service
        self.invite_service = invite_service
        self.user_service = user_service

    async def login(
        self,
        *,
        email: str,
        password: str,
        ip: str | None,
        user_agent: str | None,
        audit: AuditLogger,
    ) -> IdentityTokenResult:
        result = await self.auth_service.login(
            email=email,
            password=password,
            ip=ip,
            user_agent=user_agent,
        )

        await audit.log(
            action="auth.login",
            entity_type="user",
            entity_id=result.user_id,
            payload={"email": result.user_email, "sid": result.sid},
            user_id=result.user_id,
        )

        return IdentityTokenResult(
            tokens=result,
            events=[
                AuthSecurityNotificationEvent(
                    user_id=result.user_id,
                    event_name=LOGIN_EVENT_NAME,
                    ip=ip,
                    user_agent=user_agent,
                )
            ],
        )

    async def refresh(
        self,
        *,
        refresh_token: str | None,
        ip: str | None,
        user_agent: str | None,
        audit: AuditLogger,
    ) -> IdentityTokenResult:
        try:
            result = await self.auth_service.refresh(
                refresh_token=refresh_token,
                ip=ip,
                user_agent=user_agent,
            )
        except RefreshTokenReuseDetectedError as exc:
            await audit.log(
                action="auth.refresh_reuse",
                entity_type="user_session",
                entity_id=None,
                payload={"sid": exc.sid},
                user_id=exc.user_id,
            )
            raise

        await audit.log(
            action="auth.refresh",
            entity_type="user_session",
            entity_id=None,
            payload={"sid": result.sid},
            user_id=result.user_id,
        )

        return IdentityTokenResult(tokens=result, events=[])

    async def logout(
        self,
        *,
        refresh_token: str | None,
        ip: str | None,
        user_agent: str | None,
        audit: AuditLogger,
    ) -> IdentityLogoutResult:
        result = await self.auth_service.logout(
            refresh_token=refresh_token,
            ip=ip,
            user_agent=user_agent,
        )

        if result.user_id:
            await audit.log(
                action="auth.logout",
                entity_type="user_session",
                entity_id=None,
                payload={"sid": result.sid},
                user_id=result.user_id,
            )

        return IdentityLogoutResult(logout=result, events=[])

    async def logout_all(
        self,
        *,
        user_id: int,
        ip: str | None,
        user_agent: str | None,
        audit: AuditLogger,
    ) -> IdentityLogoutResult:
        await self.auth_service.logout_all(user_id=user_id)

        await audit.log(
            action="auth.logout_all",
            entity_type="user_session",
            entity_id=None,
            payload={"user_id": user_id},
        )

        return IdentityLogoutResult(
            logout=IdentityLogoutState(user_id=user_id, sid=None),
            events=[
                AuthSecurityNotificationEvent(
                    user_id=user_id,
                    event_name=LOGOUT_ALL_EVENT_NAME,
                    ip=ip,
                    user_agent=user_agent,
                )
            ],
        )

    async def list_user_sessions(
        self,
        *,
        user_id: int,
        include_inactive: bool,
        refresh_token: str | None,
    ) -> list[UserSessionOut]:
        return await self.auth_service.list_user_sessions(
            user_id=user_id,
            include_inactive=include_inactive,
            refresh_token=refresh_token,
        )

    async def preview_invite(self, *, token: str) -> InvitePreviewResponse:
        return await self.invite_service.preview(token)

    async def revoke_session(
        self,
        *,
        user_id: int,
        sid: str,
        refresh_token: str | None,
        audit: AuditLogger,
    ) -> IdentityRevokeSessionResult:
        result = await self.auth_service.revoke_session(
            user_id=user_id,
            sid=sid,
            refresh_token=refresh_token,
        )

        await audit.log(
            action="auth.session_revoke",
            entity_type="user_session",
            entity_id=None,
            payload={"sid": sid},
        )

        return IdentityRevokeSessionResult(session=result, events=[])

    async def register_by_invite(
        self,
        *,
        data: RegisterByInviteRequest,
        audit: AuditLogger,
    ) -> IdentityRegisterResult:
        invite = await self.invite_service.get_active_for_registration(data.token)

        if invite.target_email and invite.target_email.lower() != str(data.email).lower():
            logger.warning(
                "Register by invite failed: invite_id={} assigned to another email target_email={} requested_email={}",
                invite.id,
                invite.target_email,
                data.email,
            )
            raise InviteAssignedToAnotherEmailError()

        existing_user = await self.user_service.get_by_email(str(data.email))
        if existing_user is not None:
            logger.warning(
                "Register by invite failed: email already exists invite_id={} email={}",
                invite.id,
                data.email,
            )
            raise InviteUserAlreadyExistsError()

        try:
            created_user = await self.user_service.create(
                UserCreate(
                    name=data.name,
                    surname=data.surname,
                    email=str(data.email),
                    password=data.password,
                    role=invite.target_role,
                )
            )
        except UserAlreadyExistsError as exc:
            raise InviteUserAlreadyExistsError() from exc
        if created_user is None:
            raise IdentityError("User was not created")

        await self.invite_service.mark_used(
            invite.id,
            used_by_user_id=created_user.id,
        )
        logger.info(
            "Invite consumed: invite_id={} user_id={} email={}",
            invite.id,
            created_user.id,
            created_user.email,
        )

        result = RegisterByInviteResponse(
            user_id=created_user.id,
            email=created_user.email,
            role=str(created_user.role.value if hasattr(created_user.role, "value") else created_user.role),
        )

        await audit.log(
            action="auth.register_by_invite",
            entity_type="user",
            entity_id=result.user_id,
            payload={"email": result.email, "role": result.role},
            user_id=result.user_id,
        )

        return IdentityRegisterResult(registration=result, events=[])
