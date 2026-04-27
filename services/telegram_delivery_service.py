import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from loguru import logger

TELEGRAM_SEND_MAX_ATTEMPTS = 3
TELEGRAM_SEND_BASE_DELAY_SECONDS = 1.0


class TelegramBotPort(Protocol):
    async def send_message(self, *, chat_id: int, text: str): ...


@dataclass(slots=True)
class TelegramDeliveryResult:
    telegram_id: int
    delivered: bool
    attempts: int
    error_type: str | None = None
    error_message: str | None = None


@dataclass(slots=True)
class TelegramBroadcastDeliveryResult:
    sent: int
    failed: int
    results: list[TelegramDeliveryResult]


def _truncate_error_message(value: str | None, limit: int = 500) -> str | None:
    if value is None:
        return None
    return value[:limit]


class TelegramDeliveryService:
    def __init__(
        self,
        bot: TelegramBotPort,
        *,
        max_attempts: int = TELEGRAM_SEND_MAX_ATTEMPTS,
        base_delay_seconds: float = TELEGRAM_SEND_BASE_DELAY_SECONDS,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.bot = bot
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.sleep = sleep

    async def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        notification_id: str,
        event_type: str,
    ) -> TelegramDeliveryResult:
        for attempt in range(1, self.max_attempts + 1):
            try:
                await self.bot.send_message(chat_id=chat_id, text=text)
                logger.info(
                    "Telegram delivery succeeded: notification_id={} event_type={} chat_id={} attempt={}/{}",
                    notification_id,
                    event_type,
                    chat_id,
                    attempt,
                    self.max_attempts,
                )
                return TelegramDeliveryResult(
                    telegram_id=chat_id,
                    delivered=True,
                    attempts=attempt,
                )
            except TelegramRetryAfter as exc:
                if attempt >= self.max_attempts:
                    logger.warning(
                        "Telegram delivery failed after retry-after exhaustion: notification_id={} event_type={} chat_id={} retry_after={} attempt={}/{} error={}",
                        notification_id,
                        event_type,
                        chat_id,
                        exc.retry_after,
                        attempt,
                        self.max_attempts,
                        str(exc),
                    )
                    return TelegramDeliveryResult(
                        telegram_id=chat_id,
                        delivered=False,
                        attempts=attempt,
                        error_type=type(exc).__name__,
                        error_message=_truncate_error_message(str(exc)),
                    )

                delay = max(float(exc.retry_after), self.base_delay_seconds)
                logger.warning(
                    "Telegram delivery retry scheduled due to rate limit: notification_id={} event_type={} chat_id={} retry_in={}s attempt={}/{} error={}",
                    notification_id,
                    event_type,
                    chat_id,
                    delay,
                    attempt,
                    self.max_attempts,
                    str(exc),
                )
                await self.sleep(delay)
            except TelegramNetworkError as exc:
                if attempt >= self.max_attempts:
                    logger.warning(
                        "Telegram delivery failed after network retries: notification_id={} event_type={} chat_id={} attempt={}/{} error={}",
                        notification_id,
                        event_type,
                        chat_id,
                        attempt,
                        self.max_attempts,
                        str(exc),
                    )
                    return TelegramDeliveryResult(
                        telegram_id=chat_id,
                        delivered=False,
                        attempts=attempt,
                        error_type=type(exc).__name__,
                        error_message=_truncate_error_message(str(exc)),
                    )

                delay = self.base_delay_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "Telegram delivery retry scheduled due to network error: notification_id={} event_type={} chat_id={} retry_in={}s attempt={}/{} error={}",
                    notification_id,
                    event_type,
                    chat_id,
                    delay,
                    attempt,
                    self.max_attempts,
                    str(exc),
                )
                await self.sleep(delay)
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
            attempts=self.max_attempts,
            error_type="UnknownError",
            error_message="Telegram delivery exited without a terminal state",
        )
