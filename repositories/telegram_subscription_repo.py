from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.telegram_subscription import TelegramSubscription
from models.user import User


class TelegramSubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, subscription: TelegramSubscription) -> TelegramSubscription:
        self.db.add(subscription)
        await self.db.flush()
        await self.db.refresh(subscription)
        return subscription

    async def list_by_user(self, user_id: int) -> Sequence[TelegramSubscription]:
        stmt = (
            select(TelegramSubscription)
            .where(TelegramSubscription.user_id == user_id)
            .order_by(TelegramSubscription.created_at.desc(), TelegramSubscription.id.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_user_and_id(
        self,
        *,
        user_id: int,
        subscription_id: int,
    ) -> TelegramSubscription | None:
        stmt = select(TelegramSubscription).where(
            TelegramSubscription.user_id == user_id,
            TelegramSubscription.id == subscription_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_scope_and_event(
        self,
        *,
        user_id: int,
        scope_type: str,
        scope_id: int,
        event_type: str,
    ) -> TelegramSubscription | None:
        stmt = select(TelegramSubscription).where(
            TelegramSubscription.user_id == user_id,
            TelegramSubscription.scope_type == scope_type,
            TelegramSubscription.scope_id == scope_id,
            TelegramSubscription.event_type == event_type,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, subscription: TelegramSubscription) -> None:
        await self.db.delete(subscription)
        await self.db.flush()

    async def list_recipient_telegram_ids(
        self,
        *,
        event_type: str,
        scopes: list[tuple[str, int]],
        delivery_mode: str = "immediate",
        exclude_user_id: int | None = None,
    ) -> list[int]:
        if not scopes:
            return []

        scope_filters = [
            (
                (TelegramSubscription.scope_type == scope_type)
                & (TelegramSubscription.scope_id == scope_id)
            )
            for scope_type, scope_id in scopes
        ]

        stmt = (
            select(User.telegram_id)
            .select_from(TelegramSubscription)
            .join(User, User.id == TelegramSubscription.user_id)
            .where(
                TelegramSubscription.enabled.is_(True),
                TelegramSubscription.event_type == event_type,
                TelegramSubscription.delivery_mode == delivery_mode,
                User.telegram_id.is_not(None),
                User.telegram_id_confirmed.is_(True),
                or_(*scope_filters),
            )
            .distinct()
        )

        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)

        result = await self.db.execute(stmt)
        return [telegram_id for telegram_id in result.scalars().all() if telegram_id is not None]
