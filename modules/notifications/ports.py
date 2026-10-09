from typing import Protocol

from modules.notifications.schemas import (
    NotificationSubscriptionCreate,
    NotificationSubscriptionResponse,
)


class RealtimeNotificationPublisher(Protocol):
    async def publish_notification(self, *, user_id: int, payload: dict) -> None: ...


class NotificationSubscriptionServicePort(Protocol):
    async def list_for_user(
        self, user_id: int
    ) -> list[NotificationSubscriptionResponse]: ...

    async def create(
        self,
        *,
        user_id: int,
        data: NotificationSubscriptionCreate,
    ) -> NotificationSubscriptionResponse: ...

    async def delete(
        self,
        *,
        user_id: int,
        subscription_id: int,
    ) -> None: ...
