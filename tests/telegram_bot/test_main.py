import asyncio

from aiogram.exceptions import TelegramNetworkError
from aiogram.methods import GetMe
import pytest

from core.config import settings
from telegram_bot.main import _set_default_commands_with_retry, main, run_polling


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class FakeBot:
    def __init__(self, *, command_failures: list[Exception] | None = None) -> None:
        self.session = FakeSession()
        self.command_failures = list(command_failures or [])
        self.command_calls = 0

    async def set_my_commands(self, commands) -> None:
        self.command_calls += 1
        if self.command_failures:
            raise self.command_failures.pop(0)


class FakeDispatcher:
    def __init__(self) -> None:
        self.routers = []
        self.polling_started = False

    def include_router(self, router) -> None:
        self.routers.append(router)

    async def start_polling(self, bot) -> None:
        self.polling_started = True


def make_network_error() -> TelegramNetworkError:
    return TelegramNetworkError(method=GetMe(), message="Request timeout error")


def test_run_polling_closes_bot_when_polling_fails(monkeypatch) -> None:
    fake_bot = FakeBot()

    monkeypatch.setattr(settings.telegram, "enabled", True)
    monkeypatch.setattr(settings.telegram, "bot_token", "123:abc")
    monkeypatch.setattr(
        "telegram_bot.main.build_telegram_bot",
        lambda **_kwargs: fake_bot,
    )
    class FailingDispatcher(FakeDispatcher):
        async def start_polling(self, bot) -> None:
            raise RuntimeError("telegram unavailable")

    monkeypatch.setattr("telegram_bot.main.Dispatcher", FailingDispatcher)
    monkeypatch.setattr("telegram_bot.main.build_router", lambda: object())
    monkeypatch.setattr("telegram_bot.main.build_default_commands", lambda: [])

    with pytest.raises(RuntimeError, match="telegram unavailable"):
        asyncio.run(run_polling())

    assert fake_bot.session.closed is True


def test_set_default_commands_retries_network_errors_and_continues() -> None:
    async def scenario() -> None:
        delays: list[float] = []
        bot = FakeBot(command_failures=[make_network_error()])

        result = await _set_default_commands_with_retry(
            bot,
            attempts=2,
            delay_seconds=0.5,
            sleep=lambda delay: delays.append(delay) or asyncio.sleep(0),
        )

        assert result is True
        assert bot.command_calls == 2
        assert delays == [0.5]

    asyncio.run(scenario())


def test_set_default_commands_skips_after_network_retries() -> None:
    async def scenario() -> None:
        bot = FakeBot(command_failures=[make_network_error(), make_network_error()])

        result = await _set_default_commands_with_retry(
            bot,
            attempts=2,
            delay_seconds=0,
            sleep=lambda _delay: asyncio.sleep(0),
        )

        assert result is False
        assert bot.command_calls == 2

    asyncio.run(scenario())


def test_main_converts_network_error_to_system_exit(monkeypatch) -> None:
    async def fake_run_polling() -> None:
        raise make_network_error()

    monkeypatch.setattr("telegram_bot.main.run_polling", fake_run_polling)

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 1
