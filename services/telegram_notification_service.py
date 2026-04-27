from loguru import logger

from core.exceptions import TelegramNotificationAudienceNotFoundError
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
        exclude_user_id: int | None = None,
    ) -> list[int]:
        audience = await self.audience_repo.get_by_id(audience_id)
        if audience is None:
            logger.warning(
                "Telegram notification audience not found: audience_id={} event_type={}",
                audience_id,
                event_type.value,
            )
            raise TelegramNotificationAudienceNotFoundError()

        scopes = [
            (TelegramScopeType.audience.value, audience_id),
            (TelegramScopeType.office.value, audience.office_id),
        ]
        return await self.subscription_repo.list_recipient_telegram_ids(
            event_type=event_type.value,
            scopes=scopes,
            exclude_user_id=exclude_user_id,
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
