from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message
from loguru import logger

from telegram_bot.services import TelegramBotLinkFacade
from telegram_bot.texts import (
    GENERIC_ERROR_TEXT,
    HELP_TEXT,
    LINK_CONFLICT_TEXT,
    LINK_INVALID_TEXT,
    LINK_SUCCESS_TEXT,
    START_TEXT,
)

router = Router()
_link_facade = TelegramBotLinkFacade()


@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject) -> None:
    args = command.args or ""
    if not args:
        await message.answer(START_TEXT)
        return

    if not args.startswith("link_"):
        await message.answer(START_TEXT)
        return

    if message.from_user is None:
        logger.warning("Telegram /start received without from_user")
        await message.answer(GENERIC_ERROR_TEXT)
        return

    token = args.removeprefix("link_")
    try:
        await _link_facade.confirm_link(
            token=token,
            telegram_id=message.from_user.id,
        )
    except Exception as exc:
        error_kind = _link_facade.classify_error(exc)
        logger.warning(
            "Telegram link confirmation failed: telegram_id={} kind={} error={}",
            message.from_user.id,
            error_kind,
            str(exc),
        )
        if error_kind == "conflict":
            await message.answer(LINK_CONFLICT_TEXT)
            return
        if error_kind == "invalid":
            await message.answer(LINK_INVALID_TEXT)
            return

        logger.exception("Unexpected Telegram link confirmation error")
        await message.answer(GENERIC_ERROR_TEXT)
        return

    logger.info("Telegram link confirmed via bot: telegram_id={}", message.from_user.id)
    await message.answer(LINK_SUCCESS_TEXT)


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT)
