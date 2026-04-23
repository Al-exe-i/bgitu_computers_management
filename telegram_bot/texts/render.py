from telegram_bot.services import TelegramBotAccountSnapshot, TelegramBotSubscriptionSnapshot


def render_welcome_text() -> str:
    return (
        "👋 Это Telegram-бот системы учёта оборудования БГИТУ.\n\n"
        "Если вы открыли его из профиля на сайте, привязка аккаунта подтверждается "
        "через команду /start с токеном. После этого бот сможет присылать важные "
        "уведомления по оборудованию и безопасности аккаунта."
    )


def render_link_instructions_text(*, frontend_url: str, bot_username: str | None) -> str:
    lines = [
        "🧭 Как подключить Telegram к аккаунту:",
        "1. Откройте профиль на сайте.",
        "2. Нажмите кнопку подключения Telegram.",
        "3. Откройте ссылку из профиля или отправьте боту команду /start link_<token>.",
        "",
        f"🌐 Сайт: {frontend_url}",
    ]
    if bot_username:
        lines.append(f"🤖 Бот: https://t.me/{bot_username}")
    return "\n".join(lines)


def render_status_text(snapshot: TelegramBotAccountSnapshot) -> str:
    if not snapshot.is_linked:
        return (
            "🔌 Telegram пока не подключён.\n\n"
            "Откройте профиль на сайте, сгенерируйте ссылку для привязки и вернитесь в бот."
        )

    active_count = sum(1 for item in snapshot.subscriptions if item.enabled)
    lines = [
        "✅ Telegram подключён",
        f"📧 Email: {snapshot.email or 'не указан'}",
        f"👤 Пользователь: {snapshot.full_name or 'не указан'}",
        f"🛡 Роль: {_render_role(snapshot.role)}",
        f"🔔 Активных подписок: {active_count}",
    ]
    return "\n".join(lines)


def render_subscriptions_text(snapshot: TelegramBotAccountSnapshot) -> str:
    if not snapshot.is_linked:
        return (
            "🔌 Сначала привяжите Telegram к аккаунту на сайте. "
            "После этого здесь появятся ваши уведомления."
        )

    active_subscriptions = [item for item in snapshot.subscriptions if item.enabled]
    if not active_subscriptions:
        return (
            "🔕 Активных Telegram-подписок пока нет.\n\n"
            "Создайте первую подписку кнопками ниже."
        )

    lines = ["🔔 Активные подписки:"]
    for index, item in enumerate(active_subscriptions, start=1):
        lines.append(
            f"{index}. {_render_scope(item)}\n"
            f"   {_render_event(item.event_type)} • {_render_delivery_mode(item.delivery_mode)}"
        )
    lines.append("")
    lines.append("⚙️ Управлять подписками можно кнопками ниже.")
    return "\n".join(lines)


def render_subscription_event_choice_text(*, scope_label: str) -> str:
    return (
        f"➕ Новая подписка: {scope_label}\n\n"
        "Выберите тип уведомления."
    )


def render_subscription_scope_choice_text(
    *,
    scope_label: str,
    event_label: str,
    page: int,
    total_pages: int,
) -> str:
    return (
        f"➕ {scope_label}: {event_label}\n\n"
        f"Выберите объект из списка.\n"
        f"Страница {page} из {total_pages}."
    )


def render_subscription_delete_text(
    *,
    active_count: int,
    page: int,
    total_pages: int,
) -> str:
    if active_count == 0:
        return "🗑 Активных подписок для удаления нет."

    return (
        "🗑 Удаление подписки\n\n"
        "Выберите подписку, которую нужно отключить.\n"
        f"Страница {page} из {total_pages}."
    )


def render_subscription_result_text(result: str) -> str:
    return {
        "created": "Подписка добавлена",
        "exists": "Такая подписка уже есть",
        "deleted": "Подписка удалена",
        "enabled": "Уведомления безопасности включены",
        "disabled": "Уведомления безопасности выключены",
        "not_linked": "Сначала привяжите Telegram к аккаунту",
        "not_found": "Подписка уже отсутствует",
        "invalid": "Не удалось выполнить действие",
    }.get(result, "Не удалось выполнить действие")


def render_scope_label(scope_type: str) -> str:
    return {
        "audience": "Подписка на аудиторию",
        "office": "Подписка на корпус",
    }.get(scope_type, scope_type)


def render_event_label(event_type: str) -> str:
    return {
        "hardware_fault": "неисправность оборудования",
        "hardware_recovered": "восстановление оборудования",
        "auth_security": "события безопасности аккаунта",
    }.get(event_type, event_type)


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
        return "👤 Безопасность аккаунта"
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
