import asyncio

from loguru import logger

from celery_app import celery_app
from core.config import settings
from core.outbox import OutboxEventType
from repositories.audience_repo import AudienceRepository
from repositories.notification_subscription_repo import NotificationSubscriptionRepository
from repositories.outbox_event_repo import OutboxEventRepository
from services.realtime_notification_service import (
    AudienceChangedNotification,
    AuthSecurityNotification,
    HardwareStateNotification,
    RealtimeNotificationDispatcher,
    RealtimeNotificationRecipientService,
    RealtimeNotificationRenderer,
)
from tasks.sessions import open_task_session
from utils.broadcast import publish_audience_updated
from websocket.service import RealtimeService


async def _process_outbox_events_async(limit: int | None = None) -> dict[str, int]:
    batch_size = limit or settings.outbox.batch_size
    claimed = await _claim_events(batch_size)
    processed = 0
    failed = 0

    for event in claimed:
        try:
            await _dispatch_event(event["event_type"], event["payload"])
        except Exception as exc:
            failed += 1
            await _mark_failed(event["id"], exc)
        else:
            processed += 1
            await _mark_processed(event["id"])

    return {
        "claimed": len(claimed),
        "processed": processed,
        "failed": failed,
    }


async def _claim_events(limit: int) -> list[dict]:
    async with open_task_session() as session:
        repo = OutboxEventRepository(session)
        events = await repo.claim_batch(
            limit=limit,
            max_attempts=settings.outbox.max_attempts,
            stale_after_seconds=settings.outbox.stale_after_seconds,
        )
        claimed = [
            {
                "id": event.id,
                "event_type": event.event_type,
                "payload": event.payload,
            }
            for event in events
        ]
        await session.commit()
        return claimed


async def _mark_processed(event_id: int) -> None:
    async with open_task_session() as session:
        repo = OutboxEventRepository(session)
        await repo.mark_processed(event_id)
        await session.commit()


async def _mark_failed(event_id: int, exc: Exception) -> None:
    logger.exception("Outbox event dispatch failed: event_id={}", event_id)
    async with open_task_session() as session:
        repo = OutboxEventRepository(session)
        await repo.mark_failed(
            event_id,
            error=f"{type(exc).__name__}: {exc}",
            retry_delay_seconds=settings.outbox.retry_delay_seconds,
            max_attempts=settings.outbox.max_attempts,
        )
        await session.commit()


async def _dispatch_event(event_type: str, payload: dict) -> None:
    if event_type == OutboxEventType.IDENTITY_AUTH_SECURITY.value:
        await _send_realtime_auth_security_notification(payload)
        return

    if event_type == OutboxEventType.INVENTORY_HARDWARE_STATE_CHANGED.value:
        await _send_realtime_hardware_state_notification(payload)
        return

    if event_type == OutboxEventType.INVENTORY_AUDIENCE_UPDATED.value:
        await _publish_audience_updated(payload["audience_id"])
        await _send_realtime_audience_changed_notification(payload)
        return

    raise ValueError(f"Unsupported outbox event type: {event_type}")


async def _publish_audience_updated(audience_id: int) -> None:
    realtime = RealtimeService(settings.websocket)
    try:
        await publish_audience_updated(realtime, audience_id)
    finally:
        if realtime.bus is not None:
            await realtime.bus.close()
        if realtime.registry is not None:
            await realtime.registry.close()


async def _send_realtime_hardware_state_notification(payload: dict) -> dict[str, int | str]:
    async def dispatch(dispatcher: RealtimeNotificationDispatcher):
        return await dispatcher.send_hardware_state(HardwareStateNotification(**payload))

    return await _dispatch_realtime_notification(dispatch)


async def _send_realtime_auth_security_notification(payload: dict) -> dict[str, int | str]:
    async def dispatch(dispatcher: RealtimeNotificationDispatcher):
        return await dispatcher.send_auth_security(AuthSecurityNotification(**payload))

    return await _dispatch_realtime_notification(dispatch)


async def _send_realtime_audience_changed_notification(payload: dict) -> dict[str, int | str]:
    async def dispatch(dispatcher: RealtimeNotificationDispatcher):
        return await dispatcher.send_audience_changed(
            AudienceChangedNotification(audience_id=payload["audience_id"])
        )

    return await _dispatch_realtime_notification(dispatch)


async def _dispatch_realtime_notification(dispatch) -> dict[str, int | str]:
    realtime = RealtimeService(settings.websocket)
    try:
        async with open_task_session() as session:
            dispatcher = RealtimeNotificationDispatcher(
                recipients=RealtimeNotificationRecipientService(
                    NotificationSubscriptionRepository(session),
                    AudienceRepository(session),
                ),
                renderer=RealtimeNotificationRenderer(),
                publisher=realtime,
            )
            result = await dispatch(dispatcher)
            return result.as_task_result()
    finally:
        if realtime.bus is not None:
            await realtime.bus.close()
        if realtime.registry is not None:
            await realtime.registry.close()


@celery_app.task(name="tasks.outbox.process_outbox_events")
def process_outbox_events(limit: int | None = None) -> dict[str, int]:
    return asyncio.run(_process_outbox_events_async(limit))
