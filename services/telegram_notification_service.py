from loguru import logger

from core.exceptions import HTTP404
from repositories.audience_repo import AudienceRepository
from repositories.telegram_subscription_repo import TelegramSubscriptionRepository
from schemas.telegram import TelegramEventType, TelegramScopeType


class TelegramNotificationService:
    def __init__(
        self,
        subscription_repo: TelegramSubscriptionRepository,
        audience_repo: AudienceRepository,
    ) -> None:
        self.subscription_repo = subscription_repo
        self.audience_repo = audience_repo

    async def get_hardware_event_recipient_ids(
        self,
        *,
        audience_id: int,
        event_type: TelegramEventType,
    ) -> list[int]:
        audience = await self.audience_repo.get_by_id(audience_id)
        if audience is None:
            logger.warning(
                "Telegram notification audience not found: audience_id={} event_type={}",
                audience_id,
                event_type.value,
            )
            raise HTTP404("Audience not found")

        scopes = [
            (TelegramScopeType.audience.value, audience_id),
            (TelegramScopeType.office.value, audience.office_id),
        ]
        return await self.subscription_repo.list_recipient_telegram_ids(
            event_type=event_type.value,
            scopes=scopes,
        )

    async def get_user_event_recipient_ids(
        self,
        *,
        user_id: int,
        event_type: TelegramEventType,
    ) -> list[int]:
        return await self.subscription_repo.list_recipient_telegram_ids(
            event_type=event_type.value,
            scopes=[(TelegramScopeType.user.value, user_id)],
        )

    def build_hardware_state_message(
        self,
        *,
        hardware_id: int,
        audience_id: int,
        event_type: TelegramEventType,
        hardware_type: str | None = None,
        title: str | None = None,
        description: str | None = None,
        inv_number: str | None = None,
        x: int | None = None,
        y: int | None = None,
    ) -> str:
        if event_type == TelegramEventType.hardware_fault:
            header = "🚨 Обнаружена неисправность оборудования"
        elif event_type == TelegramEventType.hardware_recovered:
            header = "✅ Оборудование снова отмечено исправным"
        else:
            raise ValueError(f"Unsupported telegram event type: {event_type}")

        lines = [
            header,
            f"🏫 Аудитория: {audience_id}",
            f"🖥 ID оборудования: {hardware_id}",
        ]
        if hardware_type:
            lines.append(f"🧩 Тип: {self._render_hardware_type(hardware_type)}")
        if x is not None and y is not None:
            lines.append(f"📍 Расположение: ряд {y + 1}, место {x + 1}")
        if title:
            lines.append(f"🏷 Название: {title}")
        if description:
            lines.append(f"💬 Комментарий: {description}")
        if inv_number:
            lines.append(f"🔢 Инвентарный номер: {inv_number}")

        return "\n".join(lines)

    def build_auth_security_message(
        self,
        *,
        event_name: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        title, details = self._render_auth_security_event(event_name)
        lines = [title, details]
        if ip:
            lines.append(f"🌐 IP: {ip}")
        if user_agent:
            lines.append(f"💻 Устройство: {user_agent}")

        return "\n".join(lines)

    @staticmethod
    def _render_hardware_type(hardware_type: str) -> str:
        return {
            "computer": "компьютер",
            "tv": "телевизор",
            "projector": "проектор",
            "printer": "принтер",
            "switch": "коммутатор",
            "router": "роутер",
            "server": "сервер",
            "other": "другое",
        }.get(hardware_type, hardware_type)

    @staticmethod
    def _render_auth_security_event(event_name: str) -> tuple[str, str]:
        normalized_name = event_name.strip().lower()
        if normalized_name == "выполнен вход в аккаунт":
            return (
                "🔐 Выполнен вход в аккаунт",
                "В аккаунт выполнен новый вход.",
            )
        if normalized_name == "изменён пароль аккаунта":
            return (
                "🔑 Изменён пароль аккаунта",
                "Пароль вашего аккаунта был изменён.",
            )
        if normalized_name == "выполнен выход на всех устройствах":
            return (
                "🚪 Выполнен выход на всех устройствах",
                "Все активные сессии были завершены.",
            )
        return (
            "🛡 Событие безопасности аккаунта",
            event_name,
        )
