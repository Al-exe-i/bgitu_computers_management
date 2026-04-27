import asyncio

from services.telegram_bot_factory import build_telegram_bot


def test_build_telegram_bot_configures_session_timeout() -> None:
    bot = build_telegram_bot(
        token="123:abc",
        request_timeout_seconds=3.5,
    )

    try:
        assert bot.session.timeout == 3.5
    finally:
        asyncio.run(bot.session.close())
