from dataclasses import dataclass

from modules.notifications.ports import AuditLogger, NotificationSubscriptionServicePort
from schemas.notification import (
    NotificationSubscriptionCreate,
    NotificationSubscriptionResponse,
)


@dataclass(slots=True, frozen=True)
class NotificationSubscriptionCreateResult:
    subscription: NotificationSubscriptionResponse


@dataclass(slots=True, frozen=True)
class NotificationSubscriptionDeleteResult:
    pass


class RealtimeNotificationSubscriptionUseCases:
    def __init__(self, *, subscription_service: NotificationSubscriptionServicePort) -> None:
        self.subscription_service = subscription_service

    async def list_subscriptions(self, *, user_id: int) -> list[NotificationSubscriptionResponse]:
        return await self.subscription_service.list_for_user(user_id)

    async def create_subscription(
        self,
        *,
        user_id: int,
        data: NotificationSubscriptionCreate,
        audit: AuditLogger,
    ) -> NotificationSubscriptionCreateResult:
        result = await self.subscription_service.create(user_id=user_id, data=data)

        await audit.log(
            action="notification.subscription_create",
            entity_type="user",
            entity_id=user_id,
            payload={
                "subscription_id": result.id,
                "scope_type": result.scope_type.value,
                "scope_id": result.scope_id,
                "event_type": result.event_type.value,
            },
        )

        return NotificationSubscriptionCreateResult(subscription=result)

    async def delete_subscription(
        self,
        *,
        user_id: int,
        subscription_id: int,
        audit: AuditLogger,
    ) -> NotificationSubscriptionDeleteResult:
        await self.subscription_service.delete(
            user_id=user_id,
            subscription_id=subscription_id,
        )

        await audit.log(
            action="notification.subscription_delete",
            entity_type="user",
            entity_id=user_id,
            payload={"subscription_id": subscription_id},
        )

        return NotificationSubscriptionDeleteResult()
