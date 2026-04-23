import asyncio

from aiogram import Bot
from loguru import logger

from celery_app import celery_app
from core.config import settings
from core.exceptions import HTTP404
from db.session import session_factory
from repositories.audience_repo import AudienceRepository
from repositories.telegram_subscription_repo import TelegramSubscriptionRepository
from schemas.telegram import TelegramEventType
from services.telegram_notification_service import TelegramNotificationService


async def _send_hardware_state_notification_async(
    *,
    hardware_id: int,
    audience_id: int,
    event_type: str,
    title: str | None = None,
    inv_number: str | None = None,
    x: int | None = None,
    y: int | None = None,
) -> dict[str, int | str]:
    if not settings.telegram.enabled:
        logger.info(
            "Telegram notification skipped: telegram disabled event_type={} hardware_id={}",
            event_type,
            hardware_id,
        )
        return {"sent": 0, "failed": 0, "event_type": event_type}

    if not settings.telegram.bot_token:
        logger.warning(
            "Telegram notification skipped: bot token is not configured event_type={} hardware_id={}",
            event_type,
            hardware_id,
        )
        return {"sent": 0, "failed": 0, "event_type": event_type}

    try:
        telegram_event_type = TelegramEventType(event_type)
    except ValueError:
        logger.warning(
            "Telegram notification skipped: unsupported event type {} for hardware_id={}",
            event_type,
            hardware_id,
        )
        return {"sent": 0, "failed": 0, "event_type": event_type}

    async with session_factory() as session:
        service = TelegramNotificationService(
            TelegramSubscriptionRepository(session),
            AudienceRepository(session),
        )
        try:
            recipient_ids = await service.get_hardware_event_recipient_ids(
                audience_id=audience_id,
                event_type=telegram_event_type,
            )
        except HTTP404:
            logger.warning(
                "Telegram notification skipped: audience not found audience_id={} hardware_id={}",
                audience_id,
                hardware_id,
            )
            return {"sent": 0, "failed": 0, "event_type": event_type}

        if not recipient_ids:
            logger.info(
                "Telegram notification skipped: no subscribers audience_id={} event_type={} hardware_id={}",
                audience_id,
                event_type,
                hardware_id,
            )
            return {"sent": 0, "failed": 0, "event_type": event_type}

        message = service.build_hardware_state_message(
            hardware_id=hardware_id,
            audience_id=audience_id,
            event_type=telegram_event_type,
            title=title,
            inv_number=inv_number,
            x=x,
            y=y,
        )

    bot = Bot(token=settings.telegram.bot_token)
    sent = 0
    failed = 0
    try:
        for telegram_id in recipient_ids:
            try:
                await bot.send_message(chat_id=telegram_id, text=message)
                sent += 1
            except Exception:
                failed += 1
                logger.exception(
                    "Telegram notification send failed: telegram_id={} event_type={} hardware_id={}",
                    telegram_id,
                    event_type,
                    hardware_id,
                )
    finally:
        await bot.session.close()

    logger.info(
        "Telegram notification processed: event_type={} hardware_id={} audience_id={} recipients={} sent={} failed={}",
        event_type,
        hardware_id,
        audience_id,
        len(recipient_ids),
        sent,
        failed,
    )
    return {"sent": sent, "failed": failed, "event_type": event_type}


@celery_app.task(name="tasks.notifications.send_hardware_state_notification")
def send_hardware_state_notification(
    hardware_id: int,
    audience_id: int,
    event_type: str,
    title: str | None = None,
    inv_number: str | None = None,
    x: int | None = None,
    y: int | None = None,
) -> dict[str, int | str]:
    return asyncio.run(
        _send_hardware_state_notification_async(
            hardware_id=hardware_id,
            audience_id=audience_id,
            event_type=event_type,
            title=title,
            inv_number=inv_number,
            x=x,
            y=y,
        )
    )


async def _send_auth_security_notification_async(
    *,
    user_id: int,
    event_name: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> dict[str, int | str]:
    event_type = TelegramEventType.auth_security.value

    if not settings.telegram.enabled:
        logger.info(
            "Telegram auth security notification skipped: telegram disabled user_id={} event_name={}",
            user_id,
            event_name,
        )
        return {"sent": 0, "failed": 0, "event_type": event_type}

    if not settings.telegram.bot_token:
        logger.warning(
            "Telegram auth security notification skipped: bot token is not configured user_id={} event_name={}",
            user_id,
            event_name,
        )
        return {"sent": 0, "failed": 0, "event_type": event_type}

    async with session_factory() as session:
        service = TelegramNotificationService(
            TelegramSubscriptionRepository(session),
            AudienceRepository(session),
        )
        recipient_ids = await service.get_user_event_recipient_ids(
            user_id=user_id,
            event_type=TelegramEventType.auth_security,
        )
        if not recipient_ids:
            logger.info(
                "Telegram auth security notification skipped: no subscribers user_id={} event_name={}",
                user_id,
                event_name,
            )
            return {"sent": 0, "failed": 0, "event_type": event_type}

        message = service.build_auth_security_message(
            event_name=event_name,
            ip=ip,
            user_agent=user_agent,
        )

    bot = Bot(token=settings.telegram.bot_token)
    sent = 0
    failed = 0
    try:
        for telegram_id in recipient_ids:
            try:
                await bot.send_message(chat_id=telegram_id, text=message)
                sent += 1
            except Exception:
                failed += 1
                logger.exception(
                    "Telegram auth security notification send failed: telegram_id={} user_id={} event_name={}",
                    telegram_id,
                    user_id,
                    event_name,
                )
    finally:
        await bot.session.close()

    logger.info(
        "Telegram auth security notification processed: user_id={} event_name={} recipients={} sent={} failed={}",
        user_id,
        event_name,
        len(recipient_ids),
        sent,
        failed,
    )
    return {"sent": sent, "failed": failed, "event_type": event_type}


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
