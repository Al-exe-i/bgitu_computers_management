from ipaddress import ip_address
from urllib.parse import urlparse

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

BUTTON_MENU = "📋 Главное меню"
BUTTON_STATUS = "🔗 Мой статус"
BUTTON_SUBSCRIPTIONS = "🔔 Мои подписки"
BUTTON_LINK = "🧭 Как подключить"
BUTTON_HELP = "❓ Помощь"

CALLBACK_MENU = "menu:home"
CALLBACK_STATUS = "menu:status"
CALLBACK_SUBSCRIPTIONS = "menu:subscriptions"
CALLBACK_LINK = "menu:link"
CALLBACK_HELP = "menu:help"


def is_telegram_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False

    hostname = parsed.hostname.lower()
    if hostname == "localhost":
        return False

    try:
        host_ip = ip_address(hostname)
    except ValueError:
        return "." in hostname

    return not (
        host_ip.is_loopback
        or host_ip.is_private
        or host_ip.is_unspecified
        or host_ip.is_reserved
        or host_ip.is_link_local
        or host_ip.is_multicast
    )


def build_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BUTTON_STATUS),
                KeyboardButton(text=BUTTON_SUBSCRIPTIONS),
            ],
            [
                KeyboardButton(text=BUTTON_LINK),
                KeyboardButton(text=BUTTON_HELP),
            ],
            [KeyboardButton(text=BUTTON_MENU)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выберите раздел",
    )


def build_menu_inline_keyboard(*, frontend_url: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🔗 Статус", callback_data=CALLBACK_STATUS),
            InlineKeyboardButton(text="🔔 Подписки", callback_data=CALLBACK_SUBSCRIPTIONS),
        ],
        [
            InlineKeyboardButton(text="🧭 Подключение", callback_data=CALLBACK_LINK),
            InlineKeyboardButton(text="❓ Помощь", callback_data=CALLBACK_HELP),
        ],
    ]
    if is_telegram_safe_url(frontend_url):
        rows.append([InlineKeyboardButton(text="🌐 Открыть сайт", url=frontend_url)])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_status_inline_keyboard(*, frontend_url: str, is_linked: bool) -> InlineKeyboardMarkup:
    first_row = [InlineKeyboardButton(text="🔄 Обновить статус", callback_data=CALLBACK_STATUS)]
    if is_linked:
        first_row.append(
            InlineKeyboardButton(text="🔔 Мои подписки", callback_data=CALLBACK_SUBSCRIPTIONS)
        )

    second_row = [InlineKeyboardButton(text="📋 Меню", callback_data=CALLBACK_MENU)]
    if is_telegram_safe_url(frontend_url):
        second_row.append(InlineKeyboardButton(text="🌐 Сайт", url=frontend_url))

    return InlineKeyboardMarkup(inline_keyboard=[first_row, second_row])


def build_subscriptions_inline_keyboard(*, frontend_url: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data=CALLBACK_SUBSCRIPTIONS),
            InlineKeyboardButton(text="🔗 Статус", callback_data=CALLBACK_STATUS),
        ],
        [InlineKeyboardButton(text="🧭 Как подключить", callback_data=CALLBACK_LINK)],
    ]
    if is_telegram_safe_url(frontend_url):
        rows[1].append(InlineKeyboardButton(text="🌐 Сайт", url=frontend_url))

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_help_inline_keyboard(*, frontend_url: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="📋 Меню", callback_data=CALLBACK_MENU),
            InlineKeyboardButton(text="🧭 Подключение", callback_data=CALLBACK_LINK),
        ]
    ]
    if is_telegram_safe_url(frontend_url):
        rows.append([InlineKeyboardButton(text="🌐 Открыть сайт", url=frontend_url)])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_link_inline_keyboard(*, frontend_url: str) -> InlineKeyboardMarkup:
    first_row = [
        InlineKeyboardButton(text="🔗 Проверить статус", callback_data=CALLBACK_STATUS),
    ]
    if is_telegram_safe_url(frontend_url):
        first_row.insert(0, InlineKeyboardButton(text="🌐 Открыть сайт", url=frontend_url))

    return InlineKeyboardMarkup(
        inline_keyboard=[
            first_row,
            [InlineKeyboardButton(text="📋 Главное меню", callback_data=CALLBACK_MENU)],
        ]
    )
