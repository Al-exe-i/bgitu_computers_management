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

    def build_hardware_state_message(
        self,
        *,
        hardware_id: int,
        audience_id: int,
        event_type: TelegramEventType,
        title: str | None = None,
        inv_number: str | None = None,
    ) -> str:
        if event_type == TelegramEventType.hardware_fault:
            header = "Изменение по оборудованию: отмечена неисправность"
        elif event_type == TelegramEventType.hardware_recovered:
            header = "Изменение по оборудованию: оборудование отмечено исправным"
        else:
            raise ValueError(f"Unsupported telegram event type: {event_type}")

        lines = [
            header,
            f"Аудитория: {audience_id}",
            f"ID оборудования: {hardware_id}",
        ]
        if title:
            lines.append(f"Название: {title}")
        if inv_number:
            lines.append(f"Инвентарный номер: {inv_number}")

        return "\n".join(lines)
