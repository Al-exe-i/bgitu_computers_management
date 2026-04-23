from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from loguru import logger


async def safe_edit_text(
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
