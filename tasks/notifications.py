import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from loguru import logger

from celery_app import celery_app
from core.config import settings
from core.exceptions import HTTP404
from models.telegram_notification_delivery_log import TelegramNotificationDeliveryLog
from repositories.audience_repo import AudienceRepository
from repositories.telegram_notification_delivery_log_repo import (
    TelegramNotificationDeliveryLogRepository,
)
from repositories.telegram_subscription_repo import TelegramSubscriptionRepository
from schemas.telegram import TelegramEventType
from services.telegram_notification_service import TelegramNotificationService
from tasks.sessions import open_task_session

TELEGRAM_SEND_MAX_ATTEMPTS = 3
TELEGRAM_SEND_BASE_DELAY_SECONDS = 1.0


@dataclass(slots=True)
class TelegramDeliveryResult:
    telegram_id: int
    delivered: bool
    attempts: int
    error_type: str | None = None
    error_message: str | None = None


def _truncate_error_message(value: str | None, limit: int = 500) -> str | None:
    if value is None:
        return None
    return value[:limit]


async def _send_message_with_retry(
    bot: Bot,
    *,
    chat_id: int,
    text: str,
    notification_id: str,
    event_type: str,
    max_attempts: int = TELEGRAM_SEND_MAX_ATTEMPTS,
    base_delay_seconds: float = TELEGRAM_SEND_BASE_DELAY_SECONDS,
) -> TelegramDeliveryResult:
    for attempt in range(1, max_attempts + 1):
        try:
            await bot.send_message(chat_id=chat_id, text=text)
            logger.info(
                "Telegram delivery succeeded: notification_id={} event_type={} chat_id={} attempt={}/{}",
                notification_id,
                event_type,
                chat_id,
                attempt,
                max_attempts,
            )
            return TelegramDeliveryResult(
                telegram_id=chat_id,
                delivered=True,
                attempts=attempt,
            )
        except TelegramRetryAfter as exc:
            if attempt >= max_attempts:
                logger.warning(
                    "Telegram delivery failed after retry-after exhaustion: notification_id={} event_type={} chat_id={} retry_after={} attempt={}/{} error={}",
                    notification_id,
                    event_type,
                    chat_id,
                    exc.retry_after,
                    attempt,
                    max_attempts,
                    str(exc),
                )
                return TelegramDeliveryResult(
                    telegram_id=chat_id,
                    delivered=False,
                    attempts=attempt,
                    error_type=type(exc).__name__,
                    error_message=_truncate_error_message(str(exc)),
                )

            delay = max(float(exc.retry_after), base_delay_seconds)
            logger.warning(
                "Telegram delivery retry scheduled due to rate limit: notification_id={} event_type={} chat_id={} retry_in={}s attempt={}/{} error={}",
                notification_id,
                event_type,
                chat_id,
                delay,
                attempt,
                max_attempts,
                str(exc),
            )
            await asyncio.sleep(delay)
        except TelegramNetworkError as exc:
            if attempt >= max_attempts:
                logger.warning(
                    "Telegram delivery failed after network retries: notification_id={} event_type={} chat_id={} attempt={}/{} error={}",
                    notification_id,
                    event_type,
                    chat_id,
                    attempt,
                    max_attempts,
                    str(exc),
                )
                return TelegramDeliveryResult(
                    telegram_id=chat_id,
                    delivered=False,
                    attempts=attempt,
                    error_type=type(exc).__name__,
                    error_message=_truncate_error_message(str(exc)),
                )

            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Telegram delivery retry scheduled due to network error: notification_id={} event_type={} chat_id={} retry_in={}s attempt={}/{} error={}",
                notification_id,
                event_type,
                chat_id,
                delay,
                attempt,
                max_attempts,
                str(exc),
            )
            await asyncio.sleep(delay)
        except (TelegramForbiddenError, TelegramBadRequest) as exc:
            logger.warning(
                "Telegram delivery permanently failed: notification_id={} event_type={} chat_id={} error={}",
                notification_id,
                event_type,
                chat_id,
                str(exc),
            )
            return TelegramDeliveryResult(
                telegram_id=chat_id,
                delivered=False,
                attempts=attempt,
                error_type=type(exc).__name__,
                error_message=_truncate_error_message(str(exc)),
            )
        except Exception:
            logger.exception(
                "Telegram delivery failed with unexpected error: notification_id={} event_type={} chat_id={}",
                notification_id,
                event_type,
                chat_id,
            )
            return TelegramDeliveryResult(
                telegram_id=chat_id,
                delivered=False,
                attempts=attempt,
                error_type="UnexpectedError",
                error_message=None,
            )

    return TelegramDeliveryResult(
        telegram_id=chat_id,
        delivered=False,
        attempts=max_attempts,
        error_type="UnknownError",
        error_message="Telegram delivery exited without a terminal state",
    )


async def _persist_delivery_results(
    *,
    notification_id: str,
    event_type: str,
    payload: dict,
    results: list[TelegramDeliveryResult],
) -> None:
    if not results:
        return

    logged_at = datetime.now(timezone.utc)
    delivery_logs = [
        TelegramNotificationDeliveryLog(
            notification_id=notification_id,
            event_type=event_type,
            telegram_id=result.telegram_id,
            status="delivered" if result.delivered else "failed",
            attempts=result.attempts,
            error_type=result.error_type,
            error_message=result.error_message,
            delivered_at=logged_at if result.delivered else None,
            payload=dict(payload),
        )
        for result in results
    ]

    async with open_task_session() as session:
        repo = TelegramNotificationDeliveryLogRepository(session)
        await repo.create_many(delivery_logs)
        await session.commit()


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

    async with open_task_session() as session:
        service = TelegramNotificationService(
            TelegramSubscriptionRepository(session),
            AudienceRepository(session),
        )
        try:
            recipient_ids = await service.get_hardware_event_recipient_ids(
                audience_id=audience_id,
                event_type=telegram_event_type,
                exclude_user_id=actor_user_id,
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
            hardware_type=hardware_type,
            title=title,
            description=description,
            inv_number=inv_number,
            x=x,
            y=y,
        )

    bot = Bot(
        token=settings.telegram.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    sent = 0
    failed = 0
    notification_id = uuid4().hex
    delivery_results: list[TelegramDeliveryResult] = []
    try:
        logger.info(
            "Telegram hardware notification started: notification_id={} event_type={} hardware_id={} audience_id={}",
            notification_id,
            event_type,
            hardware_id,
            audience_id,
        )
        for telegram_id in recipient_ids:
            delivery_result = await _send_message_with_retry(
                bot,
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
        await bot.session.close()

    try:
        await _persist_delivery_results(
            notification_id=notification_id,
            event_type=event_type,
            payload={
                "hardware_id": hardware_id,
                "audience_id": audience_id,
                "hardware_type": hardware_type,
                "title": title,
                "description": description,
                "inv_number": inv_number,
                "x": x,
                "y": y,
                "actor_user_id": actor_user_id,
            },
            results=delivery_results,
        )
    except Exception:
        logger.exception(
            "Telegram delivery log persistence failed: notification_id={} event_type={} hardware_id={} audience_id={}",
            notification_id,
            event_type,
            hardware_id,
            audience_id,
        )

    logger.info(
        "Telegram notification processed: notification_id={} event_type={} hardware_id={} audience_id={} recipients={} sent={} failed={}",
        notification_id,
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

    async with open_task_session() as session:
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

    bot = Bot(
        token=settings.telegram.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    sent = 0
    failed = 0
    notification_id = uuid4().hex
    delivery_results: list[TelegramDeliveryResult] = []
    try:
        logger.info(
            "Telegram auth security notification started: notification_id={} user_id={} event_name={}",
            notification_id,
            user_id,
            event_name,
        )
        for telegram_id in recipient_ids:
            delivery_result = await _send_message_with_retry(
                bot,
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
        await bot.session.close()

    try:
        await _persist_delivery_results(
            notification_id=notification_id,
            event_type=event_type,
            payload={
                "user_id": user_id,
                "event_name": event_name,
                "ip": ip,
                "user_agent": user_agent,
            },
            results=delivery_results,
        )
    except Exception:
        logger.exception(
            "Telegram delivery log persistence failed: notification_id={} event_type={} user_id={} event_name={}",
            notification_id,
            event_type,
            user_id,
            event_name,
        )

    logger.info(
        "Telegram auth security notification processed: notification_id={} user_id={} event_name={} recipients={} sent={} failed={}",
        notification_id,
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
