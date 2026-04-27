from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode


def build_telegram_bot(*, token: str, request_timeout_seconds: float) -> Bot:
    session = AiohttpSession(timeout=request_timeout_seconds)
    return Bot(
        token=token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
