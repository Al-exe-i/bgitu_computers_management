from dataclasses import dataclass

from core.exceptions import (
    RefreshTokenReuseDetectedError,
    RefreshUserNotFoundError,
)
from modules.administration.public import AuditLogger
from modules.identity.contracts import (
    LogoutResult,
    RevokeSessionResult,
    TokenIssueResult,
)
from modules.identity.events import AuthSecurityNotificationEvent, IdentityEvent
from modules.identity.ports import (
    AuthServicePort,
    Transaction,
)
from modules.identity.schemas.user_session import UserSessionOut

LOGIN_EVENT_NAME = "Выполнен вход в аккаунт"
LOGOUT_ALL_EVENT_NAME = "Выполнен выход на всех устройствах"


@dataclass(slots=True, frozen=True)
class IdentityTokenResult:
    tokens: TokenIssueResult
    events: list[IdentityEvent]


@dataclass(slots=True, frozen=True)
class IdentityLogoutResult:
    logout: LogoutResult
    events: list[IdentityEvent]


@dataclass(slots=True, frozen=True)
class IdentityRevokeSessionResult:
    session: RevokeSessionResult
    events: list[IdentityEvent]


class IdentityAuthUseCases:
    def __init__(
        self,
        *,
        auth_service: AuthServicePort,
        transaction: Transaction,
    ) -> None:
        self.auth_service = auth_service
        self.transaction = transaction

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
            # The denial must not roll back the security response and its audit.
            await self.transaction.commit()
            raise
        except RefreshUserNotFoundError:
            await self.transaction.commit()
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
            logout=LogoutResult(user_id=user_id, sid=None),
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
