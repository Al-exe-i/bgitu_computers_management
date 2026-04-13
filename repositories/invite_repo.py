from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.invite_link import InviteLink


class InviteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, invite: InviteLink) -> InviteLink:
        self.db.add(invite)
        await self.db.flush()
        await self.db.refresh(invite)
        return invite

    async def list_all(self) -> Sequence[InviteLink]:
        stmt = select(InviteLink).order_by(InviteLink.created_at.desc(), InviteLink.id.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, invite_id: int) -> InviteLink | None:
        stmt = select(InviteLink).where(InviteLink.id == invite_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> InviteLink | None:
        stmt = select(InviteLink).where(InviteLink.token_hash == token_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_token_hash_for_update(self, token_hash: str) -> InviteLink | None:
        now = datetime.now(timezone.utc)

        stmt = (
            select(InviteLink)
            .where(
                InviteLink.token_hash == token_hash,
                InviteLink.used_at.is_(None),
                InviteLink.revoked_at.is_(None),
                InviteLink.expires_at > now,
            )
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, invite: InviteLink) -> InviteLink:
        invite.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(invite)
        return invite

    async def delete(self, invite: InviteLink) -> None:
        await self.db.delete(invite)
        await self.db.flush()