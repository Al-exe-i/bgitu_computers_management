from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.user_session import UserSession


class UserSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session_obj: UserSession) -> UserSession:
        self.db.add(session_obj)
        await self.db.flush()
        await self.db.refresh(session_obj)
        return session_obj

    async def get_by_sid(self, sid: str) -> UserSession | None:
        stmt = select(UserSession).where(UserSession.sid == sid)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def list_by_user(self, user_id: int, include_inactive: bool = False) -> list[UserSession]:
        now = datetime.now(timezone.utc)
        stmt = select(UserSession).where(UserSession.user_id == user_id)

        if not include_inactive:
            stmt = stmt.where(
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )

        stmt = stmt.order_by(UserSession.last_used_at.desc().nullslast(), UserSession.created_at.desc())
        return (await self.db.execute(stmt)).scalars().all()


    async def validate(self, *, sid: str, user_id: int, jti: str) -> bool:
        now = datetime.now(timezone.utc)
        stmt = select(UserSession.id).where(
            UserSession.sid == sid,
            UserSession.user_id == user_id,
            UserSession.refresh_jti == jti,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def rotate_jti(self, *, sid: str, old_jti: str, new_jti: str) -> bool:
        """
        Атомарная ротация: обновится только если old_jti совпадает.
        Это защищает от гонок и reuse.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(UserSession)
            .where(
                UserSession.sid == sid,
                UserSession.refresh_jti == old_jti,
                UserSession.revoked_at.is_(None),
            )
            .values(refresh_jti=new_jti, last_used_at=now)
            .returning(UserSession.id)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def revoke(self, sid: str) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(UserSession)
            .where(UserSession.sid == sid, UserSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self.db.execute(stmt)

    async def revoke_all_for_user(self, user_id: int) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self.db.execute(stmt)