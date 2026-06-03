from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.notification_subscription import NotificationSubscription


class NotificationSubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, subscription: NotificationSubscription) -> NotificationSubscription:
        self.db.add(subscription)
        await self.db.flush()
        await self.db.refresh(subscription)
        return subscription

    async def list_by_user(self, user_id: int) -> Sequence[NotificationSubscription]:
        stmt = (
            select(NotificationSubscription)
            .where(NotificationSubscription.user_id == user_id)
            .order_by(NotificationSubscription.created_at.desc(), NotificationSubscription.id.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_user_and_id(
        self,
        *,
        user_id: int,
        subscription_id: int,
    ) -> NotificationSubscription | None:
        stmt = select(NotificationSubscription).where(
            NotificationSubscription.user_id == user_id,
            NotificationSubscription.id == subscription_id,
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
    ) -> NotificationSubscription | None:
        stmt = select(NotificationSubscription).where(
            NotificationSubscription.user_id == user_id,
            NotificationSubscription.scope_type == scope_type,
            NotificationSubscription.scope_id == scope_id,
            NotificationSubscription.event_type == event_type,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, subscription: NotificationSubscription) -> None:
        await self.db.delete(subscription)
        await self.db.flush()

    async def list_recipient_user_ids(
        self,
        *,
        event_type: str,
        scopes: list[tuple[str, int]],
        exclude_user_id: int | None = None,
    ) -> list[int]:
        if not scopes:
            return []

        scope_filters = [
            (
                (NotificationSubscription.scope_type == scope_type)
                & (NotificationSubscription.scope_id == scope_id)
            )
            for scope_type, scope_id in scopes
        ]

        stmt = (
            select(NotificationSubscription.user_id)
            .where(
                NotificationSubscription.enabled.is_(True),
                NotificationSubscription.event_type == event_type,
                or_(*scope_filters),
            )
            .distinct()
        )

        if exclude_user_id is not None:
            stmt = stmt.where(NotificationSubscription.user_id != exclude_user_id)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
