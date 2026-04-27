import asyncio
from collections.abc import Awaitable, Callable

from aiogram import Dispatcher
from aiogram.exceptions import TelegramNetworkError
from loguru import logger

from core.config import settings
from services.telegram_bot_factory import build_telegram_bot
from telegram_bot.commands import build_default_commands
from telegram_bot.router import build_router


async def _set_default_commands_with_retry(
    bot,
    *,
    attempts: int,
    delay_seconds: float,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> bool:
    safe_attempts = max(attempts, 1)

    for attempt in range(1, safe_attempts + 1):
        try:
            await bot.set_my_commands(build_default_commands())
            return True
        except TelegramNetworkError as exc:
            if attempt >= safe_attempts:
                logger.warning(
                    "Telegram bot command setup skipped after network retries: attempt={}/{} error={}",
                    attempt,
                    safe_attempts,
                    str(exc),
                )
                return False

            logger.warning(
                "Telegram bot command setup retry scheduled: attempt={}/{} retry_in={}s error={}",
                attempt,
                safe_attempts,
                delay_seconds,
                str(exc),
            )
            await sleep(delay_seconds)


async def run_polling() -> None:
    if not settings.telegram.enabled:
        raise RuntimeError("Telegram bot is disabled in config")

    if not settings.telegram.bot_token:
        raise RuntimeError("Telegram bot token is not configured")

    bot = build_telegram_bot(
        token=settings.telegram.bot_token,
        request_timeout_seconds=settings.telegram.request_timeout_seconds,
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router())

    try:
        await _set_default_commands_with_retry(
            bot,
            attempts=settings.telegram.startup_retry_attempts,
            delay_seconds=settings.telegram.startup_retry_delay_seconds,
        )
        logger.info("Telegram bot polling started")
        await dispatcher.start_polling(bot)
    finally:
        await asyncio.shield(bot.session.close())
        logger.info("Telegram bot polling stopped")


def main() -> None:
    try:
        asyncio.run(run_polling())
    except TelegramNetworkError as exc:
        logger.error(
            "Telegram bot stopped: Telegram API is unavailable or timed out. "
            "Check network access to api.telegram.org, proxy/VPN/firewall settings, "
            "or increase BGITU__TELEGRAM__REQUEST_TIMEOUT_SECONDS. error={}",
            str(exc),
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
