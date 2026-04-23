from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from loguru import logger

from core.config import settings
from telegram_bot.keyboards import (
    BUTTON_HELP,
    BUTTON_LINK,
    BUTTON_MENU,
    BUTTON_STATUS,
    BUTTON_SUBSCRIPTIONS,
    CALLBACK_HELP,
    CALLBACK_LINK,
    CALLBACK_MENU,
    CALLBACK_STATUS,
    CALLBACK_SUBSCRIPTIONS,
    build_help_inline_keyboard,
    build_link_inline_keyboard,
    build_main_menu_keyboard,
    build_menu_inline_keyboard,
    build_status_inline_keyboard,
    build_subscriptions_inline_keyboard,
)
from telegram_bot.services import TelegramBotAccountFacade
from telegram_bot.texts import (
    FALLBACK_TEXT,
    GENERIC_ERROR_TEXT,
    HELP_TEXT,
    MENU_TEXT,
    render_link_instructions_text,
    render_status_text,
    render_subscriptions_text,
)

router = Router(name="menu")
account_facade = TelegramBotAccountFacade()


async def _safe_edit_text(
    call: CallbackQuery,
    *,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    success_answer: str | None = None,
    unchanged_answer: str = "Уже актуально",
) -> None:
    if call.message is None:
        await call.answer()
        return

    try:
        await call.message.edit_text(
            text,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            logger.debug(
                "Telegram callback ignored unchanged edit: data={} user_id={}",
                call.data,
                call.from_user.id if call.from_user else None,
            )
            await call.answer(unchanged_answer)
            return
        raise

    await call.answer(success_answer)


async def _show_menu(message: Message) -> None:
    await message.answer(
        MENU_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )
    await message.answer(
        "Быстрые действия доступны на кнопках ниже.",
        reply_markup=build_menu_inline_keyboard(frontend_url=settings.frontend_url),
    )


async def _edit_menu(call: CallbackQuery) -> None:
    await _safe_edit_text(
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
    await _safe_edit_text(
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
    await _safe_edit_text(
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
    await _safe_edit_text(
        call,
        text=render_status_text(snapshot),
        reply_markup=build_status_inline_keyboard(
            frontend_url=settings.frontend_url,
            is_linked=snapshot.is_linked,
        ),
        success_answer="Статус обновлён",
    )


async def _show_subscriptions(message: Message) -> None:
    if message.from_user is None:
        logger.warning("Telegram subscriptions request received without from_user")
        await message.answer(GENERIC_ERROR_TEXT, reply_markup=build_main_menu_keyboard())
        return

    snapshot = await account_facade.get_snapshot(telegram_id=message.from_user.id)
    await message.answer(
        render_subscriptions_text(snapshot),
        reply_markup=build_subscriptions_inline_keyboard(frontend_url=settings.frontend_url),
    )


async def _edit_subscriptions(call: CallbackQuery) -> None:
    if call.from_user is None:
        await call.answer()
        return

    snapshot = await account_facade.get_snapshot(telegram_id=call.from_user.id)
    await _safe_edit_text(
        call,
        text=render_subscriptions_text(snapshot),
        reply_markup=build_subscriptions_inline_keyboard(frontend_url=settings.frontend_url),
        success_answer="Список обновлён",
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


@router.message(Command("subscriptions"))
@router.message(F.text == BUTTON_SUBSCRIPTIONS)
async def subscriptions_handler(message: Message) -> None:
    await _show_subscriptions(message)


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


@router.callback_query(F.data == CALLBACK_SUBSCRIPTIONS)
async def subscriptions_callback(call: CallbackQuery) -> None:
    await _edit_subscriptions(call)


@router.message()
async def fallback_handler(message: Message) -> None:
    await message.answer(FALLBACK_TEXT, reply_markup=build_main_menu_keyboard())
