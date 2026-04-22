from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message
from loguru import logger

from telegram_bot.keyboards import build_main_menu_keyboard
from telegram_bot.services import TelegramBotLinkFacade
from telegram_bot.texts import (
    GENERIC_ERROR_TEXT,
    LINK_CONFLICT_TEXT,
    LINK_INVALID_TEXT,
    LINK_SUCCESS_TEXT,
    render_welcome_text,
)

router = Router(name="start")
link_facade = TelegramBotLinkFacade()


@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject) -> None:
    args = command.args or ""
    if not args or not args.startswith("link_"):
        await message.answer(
            render_welcome_text(),
            reply_markup=build_main_menu_keyboard(),
        )
        return

    if message.from_user is None:
        logger.warning("Telegram /start received without from_user")
        await message.answer(GENERIC_ERROR_TEXT, reply_markup=build_main_menu_keyboard())
        return

    token = args.removeprefix("link_")
    try:
        await link_facade.confirm_link(
            token=token,
            telegram_id=message.from_user.id,
        )
    except Exception as exc:
        error_kind = link_facade.classify_error(exc)
        logger.warning(
            "Telegram link confirmation failed: telegram_id={} kind={} error={}",
            message.from_user.id,
            error_kind,
            str(exc),
        )
        if error_kind == "conflict":
            await message.answer(LINK_CONFLICT_TEXT, reply_markup=build_main_menu_keyboard())
            return
        if error_kind == "invalid":
            await message.answer(LINK_INVALID_TEXT, reply_markup=build_main_menu_keyboard())
            return

        logger.exception("Unexpected Telegram link confirmation error")
        await message.answer(GENERIC_ERROR_TEXT, reply_markup=build_main_menu_keyboard())
        return

    logger.info("Telegram link confirmed via bot: telegram_id={}", message.from_user.id)
    await message.answer(LINK_SUCCESS_TEXT, reply_markup=build_main_menu_keyboard())
