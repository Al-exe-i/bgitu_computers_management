from ipaddress import ip_address
from urllib.parse import urlparse

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from telegram_bot.services import TelegramBotScopeOption, TelegramBotSubscriptionSnapshot

BUTTON_MENU = "📋 Меню"
BUTTON_STATUS = "🔗 Статус"
BUTTON_SUBSCRIPTIONS = "🔔 Подписки"
BUTTON_LINK = "🧭 Подключение"
BUTTON_HELP = "❓ Помощь"

CALLBACK_MENU = "menu:home"
CALLBACK_STATUS = "menu:status"
CALLBACK_SUBSCRIPTIONS = "subs:home"
CALLBACK_LINK = "menu:link"
CALLBACK_HELP = "menu:help"

CALLBACK_SUBS_ADD_AUDIENCE = "subs:add:aud"
CALLBACK_SUBS_ADD_OFFICE = "subs:add:off"
CALLBACK_SUBS_DELETE_MENU = "subs:delete:1"
CALLBACK_SUBS_TOGGLE_SECURITY = "subs:sec"


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
    first_row = [InlineKeyboardButton(text="🔄 Обновить", callback_data=CALLBACK_STATUS)]
    if is_linked:
        first_row.append(
            InlineKeyboardButton(text="🔔 Подписки", callback_data=CALLBACK_SUBSCRIPTIONS)
        )

    second_row = [InlineKeyboardButton(text="📋 Меню", callback_data=CALLBACK_MENU)]
    if is_telegram_safe_url(frontend_url):
        second_row.append(InlineKeyboardButton(text="🌐 Сайт", url=frontend_url))

    return InlineKeyboardMarkup(inline_keyboard=[first_row, second_row])


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


def build_subscriptions_inline_keyboard(*, auth_security_enabled: bool) -> InlineKeyboardMarkup:
    security_text = (
        "🛡 Безопасность: включена"
        if auth_security_enabled
        else "🛡 Безопасность: выключена"
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data=CALLBACK_SUBSCRIPTIONS),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=CALLBACK_SUBS_DELETE_MENU),
            ],
            [
                InlineKeyboardButton(text="➕ Аудитория", callback_data=CALLBACK_SUBS_ADD_AUDIENCE),
                InlineKeyboardButton(text="➕ Корпус", callback_data=CALLBACK_SUBS_ADD_OFFICE),
            ],
            [InlineKeyboardButton(text=security_text, callback_data=CALLBACK_SUBS_TOGGLE_SECURITY)],
            [
                InlineKeyboardButton(text="🔗 Статус", callback_data=CALLBACK_STATUS),
                InlineKeyboardButton(text="📋 Меню", callback_data=CALLBACK_MENU),
            ],
        ]
    )


def build_subscription_event_keyboard(*, scope_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚨 Неисправность",
                    callback_data=f"subs:event:{scope_code}:f",
                ),
                InlineKeyboardButton(
                    text="✅ Восстановление",
                    callback_data=f"subs:event:{scope_code}:r",
                ),
            ],
            [InlineKeyboardButton(text="← Назад", callback_data=CALLBACK_SUBSCRIPTIONS)],
        ]
    )


def build_subscription_scope_keyboard(
    *,
    options: list[TelegramBotScopeOption],
    scope_code: str,
    event_code: str,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=option.label,
                callback_data=f"subs:create:{scope_code}:{event_code}:{option.id}",
            )
        ]
        for option in options
    ]

    nav_row: list[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="←",
                callback_data=f"subs:page:{scope_code}:{event_code}:{page - 1}",
            )
        )
    if page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text="→",
                callback_data=f"subs:page:{scope_code}:{event_code}:{page + 1}",
            )
        )
    if nav_row:
        rows.append(nav_row)

    rows.append(
        [
            InlineKeyboardButton(
                text="← К выбору события",
                callback_data=f"subs:add:{'aud' if scope_code == 'a' else 'off'}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_subscription_delete_keyboard(
    *,
    subscriptions: list[TelegramBotSubscriptionSnapshot],
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for subscription in subscriptions:
        if subscription.id is None:
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=_render_delete_label(subscription),
                    callback_data=f"subs:del:{subscription.id}",
                )
            ]
        )

    nav_row: list[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton(text="←", callback_data=f"subs:delete:{page - 1}")
        )
    if page < total_pages:
        nav_row.append(
            InlineKeyboardButton(text="→", callback_data=f"subs:delete:{page + 1}")
        )
    if nav_row:
        rows.append(nav_row)

    rows.append([InlineKeyboardButton(text="← К подпискам", callback_data=CALLBACK_SUBSCRIPTIONS)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _render_delete_label(subscription: TelegramBotSubscriptionSnapshot) -> str:
    scope_label = {
        "audience": f"Ауд. {subscription.scope_id}",
        "office": f"Корпус {subscription.scope_id}",
        "user": "Безопасность",
    }.get(subscription.scope_type, f"{subscription.scope_type} {subscription.scope_id}")
    event_label = {
        "hardware_fault": "неисправность",
        "hardware_recovered": "восстановление",
        "audience_changed": "изменения",
        "auth_security": "безопасность",
    }.get(subscription.event_type, subscription.event_type)
    text = f"✕ {scope_label} · {event_label}"
    if len(text) <= 40:
        return text
    return text[:39].rstrip() + "…"
