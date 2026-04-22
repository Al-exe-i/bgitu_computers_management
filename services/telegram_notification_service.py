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
        title: str | None = None,
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
        if x is not None and y is not None:
            lines.append(f"📍 Расположение: ряд {y + 1}, место {x + 1}")
        if title:
            lines.append(f"🏷 Название: {title}")
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
        lines = [
            "🛡 Событие безопасности аккаунта",
            event_name,
        ]
        if ip:
            lines.append(f"🌐 IP: {ip}")
        if user_agent:
            lines.append(f"💻 User-Agent: {user_agent}")

        return "\n".join(lines)
