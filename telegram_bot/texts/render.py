from telegram_bot.services import TelegramBotAccountSnapshot, TelegramBotSubscriptionSnapshot
from utils.telegram_format import bold, code, h


def render_welcome_text() -> str:
    return (
        "👋 <b>BGITU Hardware</b>\n\n"
        "Это Telegram-бот системы учёта оборудования БГИТУ. Он помогает получать уведомления "
        "о неисправностях, восстановлении оборудования и важных событиях аккаунта.\n\n"
        "Чтобы подключить уведомления, откройте профиль на сайте и создайте ссылку привязки."
    )


def render_link_instructions_text(*, frontend_url: str, bot_username: str | None) -> str:
    lines = [
        "🧭 <b>Как подключить Telegram</b>",
        "",
        "1. Откройте профиль на сайте.",
        "2. Нажмите кнопку подключения Telegram.",
        "3. Перейдите по ссылке из профиля.",
        "",
        f"Сайт: {h(frontend_url)}",
    ]
    if bot_username:
        lines.append(f"Бот: https://t.me/{h(bot_username)}")
    lines.append("")
    lines.append(f"Технический формат команды: {code('/start link_<token>')}")
    return "\n".join(lines)


def render_status_text(snapshot: TelegramBotAccountSnapshot) -> str:
    if not snapshot.is_linked:
        return (
            "🔌 <b>Telegram не подключён</b>\n\n"
            "Создайте ссылку привязки в профиле на сайте и вернитесь в бот."
        )

    active_count = sum(1 for item in snapshot.subscriptions if item.enabled)
    lines = [
        "✅ <b>Telegram подключён</b>",
        "",
        f"Email: {code(snapshot.email)}",
        f"Пользователь: {h(snapshot.full_name)}",
        f"Роль: {h(_render_role(snapshot.role))}",
        f"Активных подписок: {bold(active_count)}",
    ]
    return "\n".join(lines)


def render_subscriptions_text(snapshot: TelegramBotAccountSnapshot) -> str:
    if not snapshot.is_linked:
        return (
            "🔌 <b>Сначала подключите Telegram</b>\n\n"
            "После привязки аккаунта здесь появятся ваши уведомления."
        )

    active_subscriptions = [item for item in snapshot.subscriptions if item.enabled]
    if not active_subscriptions:
        return (
            "🔕 <b>Активных подписок нет</b>\n\n"
            "Создайте первую подписку кнопками ниже."
        )

    lines = [
        "🔔 <b>Активные подписки</b>",
        "",
    ]
    for index, item in enumerate(active_subscriptions, start=1):
        lines.extend(
            [
                f"{index}. {bold(_render_scope(item))}",
                f"   Событие: {h(_render_event(item.event_type))}",
                f"   Доставка: {h(_render_delivery_mode(item.delivery_mode))}",
            ]
        )
    lines.extend(["", "Управляйте подписками кнопками ниже."])
    return "\n".join(lines)


def render_subscription_event_choice_text(*, scope_label: str) -> str:
    return (
        f"➕ <b>{h(scope_label)}</b>\n\n"
        "Выберите событие, по которому нужно получать уведомления."
    )


def render_subscription_scope_choice_text(
    *,
    scope_label: str,
    event_label: str,
    page: int,
    total_pages: int,
) -> str:
    return (
        f"➕ <b>{h(scope_label)}</b>\n"
        f"Событие: {h(event_label)}\n\n"
        "Выберите объект из списка.\n"
        f"Страница {page} из {total_pages}."
    )


def render_subscription_delete_text(
    *,
    active_count: int,
    page: int,
    total_pages: int,
) -> str:
    if active_count == 0:
        return "🗑 <b>Удалять нечего</b>\n\nАктивных подписок пока нет."

    return (
        "🗑 <b>Удаление подписки</b>\n\n"
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
        "not_linked": "Сначала подключите Telegram",
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
        return f"Аудитория ID {subscription.scope_id}"
    if subscription.scope_type == "office":
        return f"Корпус {subscription.scope_id}"
    if subscription.scope_type == "user":
        return "Безопасность аккаунта"
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
