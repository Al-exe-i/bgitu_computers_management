from typing import Any, Protocol

from schemas.notification import (
    NotificationSubscriptionCreate,
    NotificationSubscriptionResponse,
)


class AuditLogger(Protocol):
    async def log(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        payload: dict | None = None,
        user_id: int | None = None,
    ) -> Any: ...


class NotificationSubscriptionServicePort(Protocol):
    async def list_for_user(self, user_id: int) -> list[NotificationSubscriptionResponse]: ...

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
