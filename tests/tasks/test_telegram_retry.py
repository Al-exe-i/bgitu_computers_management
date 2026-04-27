import asyncio
from types import SimpleNamespace

from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError
from services.telegram_delivery_service import TelegramDeliveryService


class FakeBot:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    async def send_message(self, *, chat_id: int, text: str):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_send_message_with_retry_retries_network_errors_before_success() -> None:
    method = SimpleNamespace(chat_id=1001)
    bot = FakeBot(
        [
            TelegramNetworkError(method, "temporary failure"),
            TelegramNetworkError(method, "temporary failure"),
            {"ok": True},
        ]
    )
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    result = asyncio.run(
        TelegramDeliveryService(
            bot,
            max_attempts=3,
            base_delay_seconds=0.5,
            sleep=fake_sleep,
        ).send_message(
            chat_id=1001,
            text="hello",
            notification_id="n1",
            event_type="hardware_fault",
        )
    )

    assert result.delivered is True
    assert result.telegram_id == 1001
    assert result.attempts == 3
    assert result.error_type is None
    assert bot.calls == 3
    assert delays == [0.5, 1.0]


def test_send_message_with_retry_does_not_retry_forbidden_error() -> None:
    method = SimpleNamespace(chat_id=1001)
    bot = FakeBot([TelegramForbiddenError(method, "bot was blocked by the user")])
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    result = asyncio.run(
        TelegramDeliveryService(
            bot,
            max_attempts=3,
            base_delay_seconds=0.5,
            sleep=fake_sleep,
        ).send_message(
            chat_id=1001,
            text="hello",
            notification_id="n2",
            event_type="hardware_fault",
        )
    )

    assert result.delivered is False
    assert result.telegram_id == 1001
    assert result.attempts == 1
    assert result.error_type == "TelegramForbiddenError"
    assert bot.calls == 1
    assert delays == []
