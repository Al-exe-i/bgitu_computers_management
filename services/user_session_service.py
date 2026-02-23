from datetime import datetime, timezone, timedelta
from uuid import uuid4
from models.user_session import UserSession
from repositories.user_session_repo import UserSessionRepository
from core.config import settings


class UserSessionService:
    def __init__(self, repo: UserSessionRepository):
        self.repo = repo

    @staticmethod
    def new_sid() -> str:
        return str(uuid4())

    @staticmethod
    def new_jti() -> str:
        return str(uuid4())

    @staticmethod
    def refresh_expires_at() -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS)

    async def create_session(
        self,
        *,
        user_id: int,
        sid: str,
        refresh_jti: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> UserSession:
        session_obj = UserSession(
            user_id=user_id,
            sid=sid,
            refresh_jti=refresh_jti,
            expires_at=self.refresh_expires_at(),
            ip=ip,
            user_agent=user_agent,
        )
        return await self.repo.create(session_obj)

    async def validate(self, *, sid: str, user_id: int, jti: str) -> bool:
        return await self.repo.validate(sid=sid, user_id=user_id, jti=jti)

    async def rotate(self, *, sid: str, old_jti: str, new_jti: str) -> bool:
        return await self.repo.rotate_jti(sid=sid, old_jti=old_jti, new_jti=new_jti)

    async def revoke(self, sid: str) -> None:
        await self.repo.revoke(sid)

    async def revoke_for_user(self, user_id: int, sid: str) -> bool:
        sess = await self.repo.get_by_sid(sid)
        if not sess or sess.user_id != user_id:
            return False
        await self.repo.revoke(sid)
        return True

    async def revoke_all_for_user(self, user_id: int) -> None:
        await self.repo.revoke_all_for_user(user_id)