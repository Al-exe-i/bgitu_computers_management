from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.tg_link_token import TelegramLinkToken


class TelegramLinkTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, token: TelegramLinkToken) -> TelegramLinkToken:
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token

    async def deactivate_active_for_user(self, user_id: int) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(TelegramLinkToken)
            .where(
                TelegramLinkToken.user_id == user_id,
                TelegramLinkToken.used_at.is_(None),
                TelegramLinkToken.expires_at > now,
            )
            .values(used_at=now)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_active_by_token_hash_for_update(
        self,
        token_hash: str,
    ) -> TelegramLinkToken | None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(TelegramLinkToken)
            .where(
                TelegramLinkToken.token_hash == token_hash,
                TelegramLinkToken.used_at.is_(None),
                TelegramLinkToken.expires_at > now,
            )
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_used(self, token: TelegramLinkToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        await self.db.flush()
