from aiogram import Router

from telegram_bot.handlers import common_router


def build_router() -> Router:
    router = Router()
    router.include_router(common_router)
    return router
