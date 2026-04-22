import asyncio

from aiogram import Bot, Dispatcher
from loguru import logger

from core.config import settings
from telegram_bot.commands import build_default_commands
from telegram_bot.router import build_router


async def run_polling() -> None:
    if not settings.telegram.enabled:
        raise RuntimeError("Telegram bot is disabled in config")

    if not settings.telegram.bot_token:
        raise RuntimeError("Telegram bot token is not configured")

    bot = Bot(token=settings.telegram.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router())
    await bot.set_my_commands(build_default_commands())

    logger.info("Telegram bot polling started")
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Telegram bot polling stopped")


def main() -> None:
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()
