import asyncio
from collections.abc import Sequence

from celery_app import celery_app
from core.config import settings
from repositories.audience_repo import AudienceRepository
from repositories.telegram_notification_delivery_log_repo import (
    TelegramNotificationDeliveryLogRepository,
)
from repositories.telegram_subscription_repo import TelegramSubscriptionRepository
from schemas.telegram import TelegramEventType
from services.telegram_delivery_log_service import TelegramDeliveryLogService
from services.telegram_delivery_service import (
    TelegramBroadcastDeliveryResult,
    TelegramDeliveryResult,
    TelegramDeliveryService,
)
from services.telegram_bot_factory import build_telegram_bot
from services.telegram_notification_dispatcher import (
    AuthSecurityNotification,
    HardwareStateNotification,
    TelegramNotificationDispatcher,
)
from services.telegram_notification_renderer import TelegramNotificationRenderer
from services.telegram_notification_service import TelegramNotificationService
from tasks.sessions import open_task_session


async def _persist_delivery_results(
    *,
    notification_id: str,
    event_type: str,
    payload: dict,
    results: Sequence[TelegramDeliveryResult],
) -> None:
    if not results:
        return

    async with open_task_session() as session:
        service = TelegramDeliveryLogService(TelegramNotificationDeliveryLogRepository(session))
        await service.save_results(
            notification_id=notification_id,
            event_type=event_type,
            payload=payload,
            results=results,
        )
        await session.commit()


async def _deliver_message_to_recipients(
    *,
    recipient_ids: list[int],
    message: str,
    notification_id: str,
    event_type: str,
) -> TelegramBroadcastDeliveryResult:
    bot = build_telegram_bot(
        token=settings.telegram.bot_token,
        request_timeout_seconds=settings.telegram.request_timeout_seconds,
    )
    sent = 0
    failed = 0
    delivery_results: list[TelegramDeliveryResult] = []
    delivery_service = TelegramDeliveryService(bot)

    try:
        for telegram_id in recipient_ids:
            delivery_result = await delivery_service.send_message(
                chat_id=telegram_id,
                text=message,
                notification_id=notification_id,
                event_type=event_type,
            )
            delivery_results.append(delivery_result)
            if delivery_result.delivered:
                sent += 1
            else:
                failed += 1
    finally:
        await asyncio.shield(bot.session.close())

    return TelegramBroadcastDeliveryResult(
        sent=sent,
        failed=failed,
        results=delivery_results,
    )


class _TaskTelegramRecipientProvider:
    async def get_hardware_event_recipient_ids(
        self,
        *,
        audience_id: int,
        event_type: TelegramEventType,
        exclude_user_id: int | None = None,
    ) -> list[int]:
        async with open_task_session() as session:
            service = TelegramNotificationService(
                TelegramSubscriptionRepository(session),
                AudienceRepository(session),
            )
            return await service.get_hardware_event_recipient_ids(
                audience_id=audience_id,
                event_type=event_type,
                exclude_user_id=exclude_user_id,
            )

    async def get_user_event_recipient_ids(
        self,
        *,
        user_id: int,
        event_type: TelegramEventType,
    ) -> list[int]:
        async with open_task_session() as session:
            service = TelegramNotificationService(
                TelegramSubscriptionRepository(session),
                AudienceRepository(session),
            )
            return await service.get_user_event_recipient_ids(
                user_id=user_id,
                event_type=event_type,
            )


class _TaskTelegramDelivery:
    async def deliver_to_recipients(
        self,
        *,
        recipient_ids: list[int],
        message: str,
        notification_id: str,
        event_type: str,
    ) -> TelegramBroadcastDeliveryResult:
        return await _deliver_message_to_recipients(
            recipient_ids=recipient_ids,
            message=message,
            notification_id=notification_id,
            event_type=event_type,
        )


class _TaskTelegramDeliveryLogs:
    async def save_results(
        self,
        *,
        notification_id: str,
        event_type: str,
        payload: dict,
        results: Sequence[TelegramDeliveryResult],
    ) -> None:
        await _persist_delivery_results(
            notification_id=notification_id,
            event_type=event_type,
            payload=payload,
            results=results,
        )


def _build_dispatcher() -> TelegramNotificationDispatcher:
    return TelegramNotificationDispatcher(
        recipients=_TaskTelegramRecipientProvider(),
        renderer=TelegramNotificationRenderer(),
        delivery=_TaskTelegramDelivery(),
        delivery_logs=_TaskTelegramDeliveryLogs(),
        enabled=settings.telegram.enabled,
        bot_token_configured=bool(settings.telegram.bot_token),
    )


async def _send_hardware_state_notification_async(
    *,
    hardware_id: int,
    audience_id: int,
    event_type: str,
    hardware_type: str | None = None,
    title: str | None = None,
    description: str | None = None,
    inv_number: str | None = None,
    x: int | None = None,
    y: int | None = None,
    actor_user_id: int | None = None,
) -> dict[str, int | str]:
    result = await _build_dispatcher().send_hardware_state(
        HardwareStateNotification(
            hardware_id=hardware_id,
            audience_id=audience_id,
            event_type=event_type,
            hardware_type=hardware_type,
            title=title,
            description=description,
            inv_number=inv_number,
            x=x,
            y=y,
            actor_user_id=actor_user_id,
        )
    )
    return result.as_task_result()


@celery_app.task(name="tasks.notifications.send_hardware_state_notification")
def send_hardware_state_notification(
    hardware_id: int,
    audience_id: int,
    event_type: str,
    hardware_type: str | None = None,
    title: str | None = None,
    description: str | None = None,
    inv_number: str | None = None,
    x: int | None = None,
    y: int | None = None,
    actor_user_id: int | None = None,
) -> dict[str, int | str]:
    return asyncio.run(
        _send_hardware_state_notification_async(
            hardware_id=hardware_id,
            audience_id=audience_id,
            event_type=event_type,
            hardware_type=hardware_type,
            title=title,
            description=description,
            inv_number=inv_number,
            x=x,
            y=y,
            actor_user_id=actor_user_id,
        )
    )


async def _send_auth_security_notification_async(
    *,
    user_id: int,
    event_name: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> dict[str, int | str]:
    result = await _build_dispatcher().send_auth_security(
        AuthSecurityNotification(
            user_id=user_id,
            event_name=event_name,
            ip=ip,
            user_agent=user_agent,
        )
    )
    return result.as_task_result()


@celery_app.task(name="tasks.notifications.send_auth_security_notification")
def send_auth_security_notification(
    user_id: int,
    event_name: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> dict[str, int | str]:
    return asyncio.run(
        _send_auth_security_notification_async(
            user_id=user_id,
            event_name=event_name,
            ip=ip,
            user_agent=user_agent,
        )
    )
