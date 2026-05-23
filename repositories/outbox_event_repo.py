from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.outbox import OutboxEventStatus
from models.outbox_event import OutboxEvent


class OutboxEventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, *, event_type: str, payload: dict) -> OutboxEvent:
        event = OutboxEvent(event_type=event_type, payload=payload)
        self.db.add(event)
        await self.db.flush()
        return event

    async def claim_batch(
        self,
        *,
        limit: int,
        max_attempts: int,
        stale_after_seconds: int,
    ) -> Sequence[OutboxEvent]:
        now = datetime.now(timezone.utc)
        stale_before = now - timedelta(seconds=stale_after_seconds)

        statement = (
            select(OutboxEvent)
            .where(
                or_(
                    and_(
                        OutboxEvent.status == OutboxEventStatus.PENDING.value,
                        OutboxEvent.available_at <= now,
                        OutboxEvent.attempts < max_attempts,
                    ),
                    and_(
                        OutboxEvent.status == OutboxEventStatus.PROCESSING.value,
                        OutboxEvent.locked_at < stale_before,
                    ),
                )
            )
            .order_by(OutboxEvent.created_at, OutboxEvent.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(statement)
        events = result.scalars().all()

        for event in events:
            event.status = OutboxEventStatus.PROCESSING.value
            event.locked_at = now
            event.attempts += 1

        await self.db.flush()
        return events

    async def mark_processed(self, event_id: int) -> None:
        event = await self.db.get(OutboxEvent, event_id)
        if event is None:
            return

        event.status = OutboxEventStatus.PROCESSED.value
        event.processed_at = datetime.now(timezone.utc)
        event.locked_at = None
        await self.db.flush()

    async def mark_failed(
        self,
        event_id: int,
        *,
        error: str,
        retry_delay_seconds: int,
        max_attempts: int,
    ) -> None:
        event = await self.db.get(OutboxEvent, event_id)
        if event is None:
            return

        event.last_error = error[:5000]
        event.locked_at = None

        if event.attempts >= max_attempts:
            event.status = OutboxEventStatus.FAILED.value
        else:
            event.status = OutboxEventStatus.PENDING.value
            event.available_at = datetime.now(timezone.utc) + timedelta(seconds=retry_delay_seconds)

        await self.db.flush()
