from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from core.config import settings
from telegram_bot.handlers.common import safe_edit_text
from telegram_bot.keyboards import (
    BUTTON_HELP,
    BUTTON_LINK,
    BUTTON_MENU,
    BUTTON_STATUS,
    CALLBACK_HELP,
    CALLBACK_LINK,
    CALLBACK_MENU,
    CALLBACK_STATUS,
    build_help_inline_keyboard,
    build_link_inline_keyboard,
    build_main_menu_keyboard,
    build_menu_inline_keyboard,
    build_status_inline_keyboard,
)
from telegram_bot.services import TelegramBotAccountFacade
from telegram_bot.texts import (
    FALLBACK_TEXT,
    GENERIC_ERROR_TEXT,
    HELP_TEXT,
    MENU_HINT_TEXT,
    MENU_TEXT,
    render_link_instructions_text,
    render_status_text,
)

router = Router(name="menu")
account_facade = TelegramBotAccountFacade()


async def _show_menu(message: Message) -> None:
    await message.answer(
        MENU_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )
    await message.answer(
        MENU_HINT_TEXT,
        reply_markup=build_menu_inline_keyboard(frontend_url=settings.frontend_url),
    )


async def _edit_menu(call: CallbackQuery) -> None:
    await safe_edit_text(
        call,
        text=MENU_TEXT,
        reply_markup=build_menu_inline_keyboard(frontend_url=settings.frontend_url),
    )


async def _show_help(message: Message) -> None:
    await message.answer(
        HELP_TEXT,
        reply_markup=build_help_inline_keyboard(frontend_url=settings.frontend_url),
    )


async def _edit_help(call: CallbackQuery) -> None:
    await safe_edit_text(
        call,
        text=HELP_TEXT,
        reply_markup=build_help_inline_keyboard(frontend_url=settings.frontend_url),
    )


async def _show_link_help(message: Message) -> None:
    await message.answer(
        render_link_instructions_text(
            frontend_url=settings.frontend_url,
            bot_username=settings.telegram.bot_username,
        ),
        reply_markup=build_link_inline_keyboard(frontend_url=settings.frontend_url),
    )


async def _edit_link_help(call: CallbackQuery) -> None:
    await safe_edit_text(
        call,
        text=render_link_instructions_text(
            frontend_url=settings.frontend_url,
            bot_username=settings.telegram.bot_username,
        ),
        reply_markup=build_link_inline_keyboard(frontend_url=settings.frontend_url),
    )


async def _show_status(message: Message) -> None:
    if message.from_user is None:
        logger.warning("Telegram status request received without from_user")
        await message.answer(GENERIC_ERROR_TEXT, reply_markup=build_main_menu_keyboard())
        return

    snapshot = await account_facade.get_snapshot(telegram_id=message.from_user.id)
    await message.answer(
        render_status_text(snapshot),
        reply_markup=build_status_inline_keyboard(
            frontend_url=settings.frontend_url,
            is_linked=snapshot.is_linked,
        ),
    )


async def _edit_status(call: CallbackQuery) -> None:
    if call.from_user is None:
        await call.answer()
        return

    snapshot = await account_facade.get_snapshot(telegram_id=call.from_user.id)
    await safe_edit_text(
        call,
        text=render_status_text(snapshot),
        reply_markup=build_status_inline_keyboard(
            frontend_url=settings.frontend_url,
            is_linked=snapshot.is_linked,
        ),
        success_answer="Статус обновлён",
    )


@router.message(Command("menu"))
@router.message(F.text == BUTTON_MENU)
async def menu_handler(message: Message) -> None:
    await _show_menu(message)


@router.message(Command("help"))
@router.message(F.text == BUTTON_HELP)
async def help_handler(message: Message) -> None:
    await _show_help(message)


@router.message(F.text == BUTTON_LINK)
async def link_help_handler(message: Message) -> None:
    await _show_link_help(message)


@router.message(Command("status"))
@router.message(F.text == BUTTON_STATUS)
async def status_handler(message: Message) -> None:
    await _show_status(message)


@router.callback_query(F.data == CALLBACK_MENU)
async def menu_callback(call: CallbackQuery) -> None:
    await _edit_menu(call)


@router.callback_query(F.data == CALLBACK_HELP)
async def help_callback(call: CallbackQuery) -> None:
    await _edit_help(call)


@router.callback_query(F.data == CALLBACK_LINK)
async def link_callback(call: CallbackQuery) -> None:
    await _edit_link_help(call)


@router.callback_query(F.data == CALLBACK_STATUS)
async def status_callback(call: CallbackQuery) -> None:
    await _edit_status(call)


@router.message()
async def fallback_handler(message: Message) -> None:
    await message.answer(FALLBACK_TEXT, reply_markup=build_main_menu_keyboard())
