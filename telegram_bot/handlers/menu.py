from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from core.config import settings
from telegram_bot.keyboards import (
    BUTTON_HELP,
    BUTTON_LINK,
    BUTTON_MENU,
    BUTTON_STATUS,
    BUTTON_SUBSCRIPTIONS,
    build_main_menu_keyboard,
)
from telegram_bot.services import TelegramBotAccountFacade
from telegram_bot.texts import (
    FALLBACK_TEXT,
    HELP_TEXT,
    MENU_TEXT,
    GENERIC_ERROR_TEXT,
    render_link_instructions_text,
    render_status_text,
    render_subscriptions_text,
)

router = Router(name="menu")
account_facade = TelegramBotAccountFacade()


@router.message(Command("menu"))
@router.message(F.text == BUTTON_MENU)
async def menu_handler(message: Message) -> None:
    await message.answer(MENU_TEXT, reply_markup=build_main_menu_keyboard())


@router.message(Command("help"))
@router.message(F.text == BUTTON_HELP)
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=build_main_menu_keyboard())


@router.message(F.text == BUTTON_LINK)
async def link_help_handler(message: Message) -> None:
    await message.answer(
        render_link_instructions_text(
            frontend_url=settings.frontend_url,
            bot_username=settings.telegram.bot_username,
        ),
        reply_markup=build_main_menu_keyboard(),
    )


@router.message(Command("status"))
@router.message(F.text == BUTTON_STATUS)
async def status_handler(message: Message) -> None:
    if message.from_user is None:
        logger.warning("Telegram status request received without from_user")
        await message.answer(GENERIC_ERROR_TEXT, reply_markup=build_main_menu_keyboard())
        return

    snapshot = await account_facade.get_snapshot(telegram_id=message.from_user.id)
    await message.answer(
        render_status_text(snapshot),
        reply_markup=build_main_menu_keyboard(),
    )


@router.message(Command("subscriptions"))
@router.message(F.text == BUTTON_SUBSCRIPTIONS)
async def subscriptions_handler(message: Message) -> None:
    if message.from_user is None:
        logger.warning("Telegram subscriptions request received without from_user")
        await message.answer(GENERIC_ERROR_TEXT, reply_markup=build_main_menu_keyboard())
        return

    snapshot = await account_facade.get_snapshot(telegram_id=message.from_user.id)
    await message.answer(
        render_subscriptions_text(snapshot),
        reply_markup=build_main_menu_keyboard(),
    )


@router.message()
async def fallback_handler(message: Message) -> None:
    await message.answer(FALLBACK_TEXT, reply_markup=build_main_menu_keyboard())
