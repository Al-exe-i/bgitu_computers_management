from telegram_bot.services import TelegramBotAccountSnapshot, TelegramBotSubscriptionSnapshot


def render_welcome_text() -> str:
    return (
        "👋 Это Telegram-бот системы учёта оборудования БГИТУ.\n\n"
        "Если вы открыли его из сайта, привязка аккаунта подтверждается автоматически. "
        "После этого можно получать уведомления о важных изменениях.\n\n"
        "Откройте меню ниже, чтобы посмотреть доступные действия."
    )


def render_link_instructions_text(*, frontend_url: str, bot_username: str | None) -> str:
    lines = [
        "🧭 Как подключить Telegram к аккаунту:",
        "1. Войдите на сайт и откройте профиль.",
        "2. Сгенерируйте ссылку для привязки Telegram.",
        "3. Откройте её или отправьте боту команду /start link_<token>.",
        "",
        f"🌐 Сайт: {frontend_url}",
    ]
    if bot_username:
        lines.append(f"🤖 Бот: https://t.me/{bot_username}")
    return "\n".join(lines)


def render_status_text(snapshot: TelegramBotAccountSnapshot) -> str:
    if not snapshot.is_linked:
        return (
            "🔌 Этот Telegram-аккаунт пока не привязан.\n\n"
            "Откройте сайт, перейдите в профиль и сгенерируйте ссылку для привязки."
        )

    lines = [
        "✅ Telegram привязан.",
        f"📧 Email: {snapshot.email or 'не указан'}",
        f"👤 Пользователь: {snapshot.full_name or 'не указан'}",
        f"🛡 Роль: {_render_role(snapshot.role)}",
        f"🔔 Активных подписок: {sum(1 for item in snapshot.subscriptions if item.enabled)}",
    ]
    return "\n".join(lines)


def render_subscriptions_text(snapshot: TelegramBotAccountSnapshot) -> str:
    if not snapshot.is_linked:
        return (
            "🔌 Сначала привяжите Telegram к аккаунту на сайте, "
            "после этого здесь появятся ваши подписки."
        )

    active_subscriptions = [item for item in snapshot.subscriptions if item.enabled]
    if not active_subscriptions:
        return (
            "🔕 У вас пока нет активных Telegram-подписок.\n\n"
            "Их можно создать в профиле на сайте."
        )

    lines = ["🔔 Активные подписки:"]
    for index, item in enumerate(active_subscriptions, start=1):
        lines.append(
            f"{index}. {_render_scope(item)} -> {_render_event(item.event_type)} "
            f"({_render_delivery_mode(item.delivery_mode)})"
        )
    lines.append("")
    lines.append("⚙ Управление подписками пока доступно на сайте.")
    return "\n".join(lines)


def _render_role(role: str | None) -> str:
    return {
        "admin": "администратор",
        "teacher": "преподаватель",
    }.get(role or "", role or "не указана")


def _render_scope(subscription: TelegramBotSubscriptionSnapshot) -> str:
    if subscription.scope_type == "audience":
        return f"🏫 Аудитория {subscription.scope_id}"
    if subscription.scope_type == "office":
        return f"🏢 Корпус {subscription.scope_id}"
    if subscription.scope_type == "user":
        return "👤 Личные уведомления"
    return f"{subscription.scope_type} {subscription.scope_id}"


def _render_event(event_type: str) -> str:
    return {
        "audience_changed": "изменения в аудитории",
        "hardware_fault": "неисправность оборудования",
        "hardware_recovered": "восстановление оборудования",
        "auth_security": "события безопасности аккаунта",
    }.get(event_type, event_type)


def _render_delivery_mode(delivery_mode: str) -> str:
    return {
        "immediate": "сразу",
        "daily_digest": "дневная сводка",
    }.get(delivery_mode, delivery_mode)
