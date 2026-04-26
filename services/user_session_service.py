from datetime import datetime, timedelta, timezone
from uuid import uuid4

from core.config import settings
from loguru import logger
from models.user_session import UserSession
from repositories.user_session_repo import UserSessionRepository
from utils.tokens import hash_refresh_token


class UserSessionService:
    def __init__(self, repo: UserSessionRepository):
        self.repo = repo

    @staticmethod
    def new_sid() -> str:
        return str(uuid4())

    @staticmethod
    def refresh_expires_at() -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS)

    async def create_session(
        self,
        *,
        user_id: int,
        sid: str,
        refresh_token_hash: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> UserSession:
        session_obj = UserSession(
            user_id=user_id,
            sid=sid,
            refresh_token_hash=refresh_token_hash,
            expires_at=self.refresh_expires_at(),
            ip=ip,
            user_agent=user_agent,
        )
        created = await self.repo.create(session_obj)
        logger.debug(
            "Session created: user_id={} sid={} ip={} user_agent={}",
            user_id,
            sid,
            ip,
            user_agent,
        )
        return created

    async def get_active_by_refresh_token(self, refresh_token: str) -> UserSession | None:
        return await self.repo.get_active_by_refresh_token_hash(hash_refresh_token(refresh_token))

    async def rotate_refresh_token(
        self,
        *,
        sid: str,
        old_refresh_token: str,
        new_refresh_token: str,
    ) -> bool:
        rotated = await self.repo.rotate_refresh_token_hash(
            sid=sid,
            old_hash=hash_refresh_token(old_refresh_token),
            new_hash=hash_refresh_token(new_refresh_token),
        )
        if rotated:
            logger.debug("Refresh token rotated for sid={}", sid)
        else:
            logger.warning("Refresh token rotation failed for sid={}", sid)
        return rotated

    async def get_current_sid(self, refresh_token: str | None) -> str | None:
        if not refresh_token:
            return None

        session = await self.get_active_by_refresh_token(refresh_token)
        return session.sid if session else None

    async def list_by_user(self, user_id: int, include_inactive: bool = False) -> list[UserSession]:
        return await self.repo.list_by_user(user_id, include_inactive=include_inactive)

    async def revoke(self, sid: str) -> None:
        await self.repo.revoke(sid)
        logger.debug("Session revoked: sid={}", sid)

    async def revoke_for_user(self, user_id: int, sid: str) -> bool:
        revoked = await self.repo.revoke_by_sid_and_user(sid=sid, user_id=user_id)
        if revoked:
            logger.debug("Session revoked for user: user_id={} sid={}", user_id, sid)
        else:
            logger.warning("Session revoke failed for user: user_id={} sid={}", user_id, sid)
        return revoked

    async def revoke_all_for_user(self, user_id: int) -> None:
        await self.repo.revoke_all_for_user(user_id)
        logger.info("All sessions revoked for user_id={}", user_id)
