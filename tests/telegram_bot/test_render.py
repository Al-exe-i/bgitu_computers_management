from telegram_bot.services.account import (
    TelegramBotAccountSnapshot,
    TelegramBotSubscriptionSnapshot,
)
from telegram_bot.texts.render import (
    render_link_instructions_text,
    render_status_text,
    render_subscriptions_text,
)


def test_render_status_text_for_linked_account() -> None:
    snapshot = TelegramBotAccountSnapshot(
        is_linked=True,
        email="teacher@example.com",
        full_name="Иванов Иван",
        role="teacher",
        subscriptions=[
            TelegramBotSubscriptionSnapshot(
                scope_type="audience",
                scope_id=215,
                event_type="hardware_fault",
                delivery_mode="immediate",
                enabled=True,
            )
        ],
    )

    text = render_status_text(snapshot)

    assert "✅ Telegram привязан." in text
    assert "teacher@example.com" in text
    assert "Иванов Иван" in text
    assert "преподаватель" in text
    assert "🔔 Активных подписок: 1" in text


def test_render_subscriptions_text_lists_human_readable_items() -> None:
    snapshot = TelegramBotAccountSnapshot(
        is_linked=True,
        subscriptions=[
            TelegramBotSubscriptionSnapshot(
                scope_type="office",
                scope_id=3,
                event_type="hardware_recovered",
                delivery_mode="daily_digest",
                enabled=True,
            )
        ],
    )

    text = render_subscriptions_text(snapshot)

    assert "🔔 Активные подписки:" in text
    assert "🏢 Корпус 3" in text
    assert "восстановление оборудования" in text
    assert "дневная сводка" in text


def test_render_link_instructions_text_includes_site_and_bot() -> None:
    text = render_link_instructions_text(
        frontend_url="http://localhost:5173",
        bot_username="bgitu_test_bot",
    )

    assert "http://localhost:5173" in text
    assert "https://t.me/bgitu_test_bot" in text
