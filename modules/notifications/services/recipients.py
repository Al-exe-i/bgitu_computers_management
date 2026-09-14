from loguru import logger

from core.exceptions import NotificationAudienceNotFoundError
from modules.inventory.public import AudienceDirectory
from modules.notifications.repositories.subscriptions import (
    NotificationSubscriptionRepository,
)
from modules.notifications.schemas import NotificationEventType, NotificationScopeType


class RealtimeNotificationRecipientService:
    def __init__(
        self,
        subscription_repo: NotificationSubscriptionRepository,
        audiences: AudienceDirectory,
    ) -> None:
        self.subscription_repo = subscription_repo
        self.audiences = audiences

    async def get_hardware_event_recipient_user_ids(
        self,
        *,
        audience_id: int,
        event_type: NotificationEventType,
        exclude_user_id: int | None = None,
    ) -> list[int]:
        scopes = await self._audience_and_office_scopes(
            audience_id=audience_id,
            event_type=event_type,
        )
        return await self.subscription_repo.list_recipient_user_ids(
            event_type=event_type.value,
            scopes=scopes,
            exclude_user_id=exclude_user_id,
        )

    async def get_audience_event_recipient_user_ids(
        self,
        *,
        audience_id: int,
        event_type: NotificationEventType,
    ) -> list[int]:
        scopes = await self._audience_and_office_scopes(
            audience_id=audience_id,
            event_type=event_type,
        )
        return await self.subscription_repo.list_recipient_user_ids(
            event_type=event_type.value,
            scopes=scopes,
        )

    async def get_user_event_recipient_user_ids(
        self,
        *,
        user_id: int,
        event_type: NotificationEventType,
    ) -> list[int]:
        return await self.subscription_repo.list_recipient_user_ids(
            event_type=event_type.value,
            scopes=[(NotificationScopeType.user.value, user_id)],
        )

    async def _audience_and_office_scopes(
        self,
        *,
        audience_id: int,
        event_type: NotificationEventType,
    ) -> list[tuple[str, int]]:
        audience = await self.get_audience_context(audience_id=audience_id, event_type=event_type)

        return [
            (NotificationScopeType.audience.value, audience_id),
            (NotificationScopeType.office.value, audience.office_id),
        ]

    async def get_audience_context(
        self,
        *,
        audience_id: int,
        event_type: NotificationEventType,
    ):
        audience = await self.audiences.get_one_short(audience_id)
        if audience is None:
            logger.warning(
                "Realtime notification audience not found: audience_id={} event_type={}",
                audience_id,
                event_type.value,
            )
            raise NotificationAudienceNotFoundError()

        return audience
