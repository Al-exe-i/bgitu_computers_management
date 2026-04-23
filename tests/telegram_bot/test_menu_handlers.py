import asyncio
from types import SimpleNamespace

from aiogram.exceptions import TelegramBadRequest

from telegram_bot.handlers.menu import _safe_edit_text
from telegram_bot.keyboards.main_menu import build_help_inline_keyboard


class FakeMessage:
    def __init__(self, exc: Exception | None = None) -> None:
        self.exc = exc
        self.calls: list[dict] = []

    async def edit_text(self, text: str, reply_markup):
        self.calls.append({"text": text, "reply_markup": reply_markup})
        if self.exc is not None:
            raise self.exc


class FakeCallback:
    def __init__(self, message, *, data: str = "menu:status") -> None:
        self.message = message
        self.data = data
        self.from_user = SimpleNamespace(id=7)
        self.answers: list[str | None] = []

    async def answer(self, text: str | None = None) -> None:
        self.answers.append(text)


def test_safe_edit_text_swallows_message_not_modified() -> None:
    method = SimpleNamespace(chat_id=1001)
    callback = FakeCallback(
        FakeMessage(TelegramBadRequest(method, "message is not modified")),
    )

    asyncio.run(
        _safe_edit_text(
            callback,
            text="status",
            reply_markup=build_help_inline_keyboard(frontend_url="https://example.com"),
        )
    )

    assert callback.answers == ["Уже актуально"]
    assert len(callback.message.calls) == 1


def test_safe_edit_text_keeps_success_answer() -> None:
    callback = FakeCallback(FakeMessage())

    asyncio.run(
        _safe_edit_text(
            callback,
            text="status",
            reply_markup=build_help_inline_keyboard(frontend_url="https://example.com"),
            success_answer="Статус обновлён",
        )
    )

    assert callback.answers == ["Статус обновлён"]
    assert len(callback.message.calls) == 1
