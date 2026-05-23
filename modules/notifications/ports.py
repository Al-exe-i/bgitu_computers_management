from typing import Any, Protocol

from schemas.telegram import (
    TelegramLinkStartResponse,
    TelegramLinkStatusResponse,
    TelegramSubscriptionCreate,
    TelegramSubscriptionResponse,
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


class TelegramActor(Protocol):
    id: int
    telegram_id: int | None


class TelegramLinkServicePort(Protocol):
    async def get_link_status(self, user_id: int) -> TelegramLinkStatusResponse: ...
    async def create_link_token(self, user_id: int) -> TelegramLinkStartResponse: ...
    async def unlink_user(self, user_id: int) -> TelegramLinkStatusResponse: ...


class TelegramSubscriptionServicePort(Protocol):
    async def list_for_user(self, user_id: int) -> list[TelegramSubscriptionResponse]: ...

    async def create(
        self,
        *,
        user_id: int,
        data: TelegramSubscriptionCreate,
    ) -> TelegramSubscriptionResponse: ...

    async def delete(
        self,
        *,
        user_id: int,
        subscription_id: int,
    ) -> None: ...
