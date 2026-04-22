from aiogram import Router

from telegram_bot.handlers import menu_router, start_router


def build_router() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(menu_router)
    return router
