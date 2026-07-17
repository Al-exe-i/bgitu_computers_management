from dataclasses import dataclass
from datetime import datetime, timezone

from loguru import logger

from core.exceptions.auth import (
    InvalidCredentialsError,
    RefreshSessionNotFoundError,
    RefreshTokenMissingError,
    RefreshTokenReuseDetectedError,
    RefreshUserNotFoundError,
    SessionNotFoundError,
)
from core.security import get_password_hash, verify_password
from schemas.user_session import UserSessionOut
from services.user_service import UserService
from services.user_session_service import UserSessionService
from utils.tokens import (
    hash_refresh_token,
    issue_access_token,
    new_refresh_token,
)


_DUMMY_PASSWORD_HASH = get_password_hash("timing-normalization-password")
MAX_LOGIN_EMAIL_LENGTH = 254
MAX_LOGIN_PASSWORD_LENGTH = 128


@dataclass(slots=True)
class TokenIssueResult:
    user_id: int
    user_email: str | None
    sid: str
    access_token: str
    refresh_token: str


@dataclass(slots=True)
class LogoutResult:
    user_id: int | None
    sid: str | None


@dataclass(slots=True)
class RevokeSessionResult:
    revoked_current_session: bool


class AuthService:
    def __init__(
        self,
        user_service: UserService,
        session_service: UserSessionService,
    ) -> None:
        self.user_service = user_service
        self.session_service = session_service

    async def login(
        self,
        *,
        email: str,
        password: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenIssueResult:
        if len(email) > MAX_LOGIN_EMAIL_LENGTH or len(password) > MAX_LOGIN_PASSWORD_LENGTH:
            verify_password("invalid-login-input", _DUMMY_PASSWORD_HASH)
            logger.warning(
                "Login rejected due to oversized credentials ip={} user_agent={}",
                ip,
                user_agent,
            )
            raise InvalidCredentialsError()

        user = await self.user_service.get_by_email(email)
        password_hash = user.password if user is not None else _DUMMY_PASSWORD_HASH
        password_matches = verify_password(password, password_hash)
        if user is None or not password_matches:
            logger.warning(
                "Login failed for email={} ip={} user_agent={}",
                email,
                ip,
                user_agent,
            )
            raise InvalidCredentialsError()

        sid = self.session_service.new_sid()
        refresh_token = new_refresh_token()

        await self.session_service.create_session(
            user_id=user.id,
            sid=sid,
            refresh_token_hash=hash_refresh_token(refresh_token),
            ip=ip,
            user_agent=user_agent,
        )

        logger.info("Login succeeded for user_id={} sid={} ip={}", user.id, sid, ip)
        return TokenIssueResult(
            user_id=user.id,
            user_email=getattr(user, "email", None),
            sid=sid,
            access_token=issue_access_token(
                user.id,
                await self._access_token_version(user),
            ),
            refresh_token=refresh_token,
        )

    async def refresh(
        self,
        *,
        refresh_token: str | None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenIssueResult:
        if not refresh_token:
            logger.warning(
                "Refresh rejected: no refresh token provided ip={} user_agent={}",
                ip,
                user_agent,
            )
            raise RefreshTokenMissingError()

        session = await self.session_service.get_active_by_refresh_token(refresh_token)
        if not session:
            logger.warning(
                "Refresh rejected: session not found ip={} user_agent={}",
                ip,
                user_agent,
            )
            raise RefreshSessionNotFoundError()

        user = await self.user_service.get(session.user_id)
        if not user:
            await self.session_service.revoke(session.sid)
            logger.warning(
                "Refresh rejected: user_id={} not found for sid={}",
                session.user_id,
                session.sid,
            )
            raise RefreshUserNotFoundError(user_id=session.user_id, sid=session.sid)

        new_token = new_refresh_token()
        rotated = await self.session_service.rotate_refresh_token(
            sid=session.sid,
            old_refresh_token=refresh_token,
            new_refresh_token=new_token,
        )
        if not rotated:
            await self.session_service.revoke(session.sid)
            await self.user_service.bump_access_token_version(user.id)
            logger.warning(
                "Refresh token reuse detected for user_id={} sid={}",
                user.id,
                session.sid,
            )
            raise RefreshTokenReuseDetectedError(user_id=user.id, sid=session.sid)

        logger.info("Refresh succeeded for user_id={} sid={}", user.id, session.sid)
        return TokenIssueResult(
            user_id=user.id,
            user_email=getattr(user, "email", None),
            sid=session.sid,
            access_token=issue_access_token(
                user.id,
                await self._access_token_version(user),
            ),
            refresh_token=new_token,
        )

    async def logout(
        self,
        *,
        refresh_token: str | None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> LogoutResult:
        if not refresh_token:
            logger.debug(
                "Logout requested without refresh token ip={} user_agent={}",
                ip,
                user_agent,
            )
            return LogoutResult(user_id=None, sid=None)

        session = await self.session_service.get_active_by_refresh_token(refresh_token)
        if not session:
            logger.warning(
                "Logout requested with unknown refresh token ip={} user_agent={}",
                ip,
                user_agent,
            )
            return LogoutResult(user_id=None, sid=None)

        await self.session_service.revoke(session.sid)
        await self.user_service.bump_access_token_version(session.user_id)
        logger.info("Logout succeeded for user_id={} sid={}", session.user_id, session.sid)
        return LogoutResult(user_id=session.user_id, sid=session.sid)

    async def logout_all(self, *, user_id: int) -> None:
        await self.session_service.revoke_all_for_user(user_id)
        await self.user_service.bump_access_token_version(user_id)
        logger.info("Logout all sessions for user_id={}", user_id)

    async def list_user_sessions(
        self,
        *,
        user_id: int,
        include_inactive: bool,
        refresh_token: str | None,
    ) -> list[UserSessionOut]:
        current_sid = await self.session_service.get_current_sid(refresh_token)
        now = datetime.now(timezone.utc)
        rows = await self.session_service.list_by_user(
            user_id,
            include_inactive=include_inactive,
        )

        return [
            UserSessionOut.model_validate(
                {
                    **session.__dict__,
                    "is_active": (session.revoked_at is None) and (session.expires_at > now),
                    "is_current": current_sid is not None and session.sid == current_sid,
                }
            )
            for session in rows
        ]

    async def revoke_session(
        self,
        *,
        user_id: int,
        sid: str,
        refresh_token: str | None,
    ) -> RevokeSessionResult:
        current_sid = await self.session_service.get_current_sid(refresh_token)
        revoked = await self.session_service.revoke_for_user(user_id, sid)
        if not revoked:
            logger.warning("Session revoke failed for user_id={} sid={}", user_id, sid)
            raise SessionNotFoundError()

        await self.user_service.bump_access_token_version(user_id)
        logger.info("Session revoked for user_id={} sid={}", user_id, sid)
        return RevokeSessionResult(revoked_current_session=current_sid == sid)

    async def _access_token_version(self, user: object) -> int:
        get_version = getattr(self.user_service, "get_access_token_version", None)
        if get_version is not None:
            version = await get_version(user.id)
            if version is not None:
                return int(version)

        return int(getattr(user, "access_token_version", 0) or 0)
