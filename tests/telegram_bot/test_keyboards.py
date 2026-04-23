from telegram_bot.keyboards.main_menu import (
    build_subscriptions_inline_keyboard,
    build_link_inline_keyboard,
    build_status_inline_keyboard,
    is_telegram_safe_url,
)


def test_is_telegram_safe_url_rejects_local_addresses() -> None:
    assert is_telegram_safe_url("http://localhost:5173") is False
    assert is_telegram_safe_url("http://127.0.0.1:5173") is False
    assert is_telegram_safe_url("http://192.168.1.5:5173") is False


def test_is_telegram_safe_url_accepts_public_urls() -> None:
    assert is_telegram_safe_url("https://example.com") is True
    assert is_telegram_safe_url("https://demo.example.com/app") is True


def test_build_status_inline_keyboard_omits_invalid_site_button() -> None:
    keyboard = build_status_inline_keyboard(
        frontend_url="http://localhost:5173",
        is_linked=True,
    )

    buttons = [button for row in keyboard.inline_keyboard for button in row]

    assert all(button.url is None for button in buttons)
    assert any(button.callback_data == "menu:status" for button in buttons)
    assert any(button.callback_data == "subs:home" for button in buttons)


def test_build_link_inline_keyboard_keeps_public_site_button() -> None:
    keyboard = build_link_inline_keyboard(frontend_url="https://example.com")

    buttons = [button for row in keyboard.inline_keyboard for button in row]

    assert any(button.url == "https://example.com" for button in buttons)


def test_build_subscriptions_inline_keyboard_reflects_security_state() -> None:
    keyboard = build_subscriptions_inline_keyboard(auth_security_enabled=True)
    buttons = [button for row in keyboard.inline_keyboard for button in row]

    assert any(button.callback_data == "subs:sec" and "включена" in button.text for button in buttons)
