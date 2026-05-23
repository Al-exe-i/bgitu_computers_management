from dataclasses import dataclass

from schemas.telegram import (
    TelegramLinkStartResponse,
    TelegramLinkStatusResponse,
    TelegramSubscriptionCreate,
    TelegramSubscriptionResponse,
)
from modules.notifications.ports import (
    AuditLogger,
    TelegramActor,
    TelegramLinkServicePort,
    TelegramSubscriptionServicePort,
)


@dataclass(slots=True, frozen=True)
class TelegramLinkTokenResult:
    token: TelegramLinkStartResponse


@dataclass(slots=True, frozen=True)
class TelegramUnlinkResult:
    status: TelegramLinkStatusResponse


@dataclass(slots=True, frozen=True)
class TelegramSubscriptionCreateResult:
    subscription: TelegramSubscriptionResponse


@dataclass(slots=True, frozen=True)
class TelegramSubscriptionDeleteResult:
    pass


class TelegramIntegrationUseCases:
    def __init__(
        self,
        *,
        link_service: TelegramLinkServicePort,
        subscription_service: TelegramSubscriptionServicePort,
    ) -> None:
        self.link_service = link_service
        self.subscription_service = subscription_service

    async def get_link_status(self, *, user_id: int) -> TelegramLinkStatusResponse:
        return await self.link_service.get_link_status(user_id)

    async def create_link_token(
        self,
        *,
        user_id: int,
        audit: AuditLogger,
    ) -> TelegramLinkTokenResult:
        result = await self.link_service.create_link_token(user_id)

        await audit.log(
            action="telegram.link_token_create",
            entity_type="user",
            entity_id=user_id,
            payload={"expires_at": result.expires_at.isoformat()},
        )

        return TelegramLinkTokenResult(token=result)

    async def unlink_account(
        self,
        *,
        actor: TelegramActor,
        audit: AuditLogger,
    ) -> TelegramUnlinkResult:
        had_telegram_id = actor.telegram_id is not None
        result = await self.link_service.unlink_user(actor.id)

        await audit.log(
            action="telegram.unlink",
            entity_type="user",
            entity_id=actor.id,
            payload={"had_telegram_id": had_telegram_id},
        )

        return TelegramUnlinkResult(status=result)

    async def list_subscriptions(self, *, user_id: int) -> list[TelegramSubscriptionResponse]:
        return await self.subscription_service.list_for_user(user_id)

    async def create_subscription(
        self,
        *,
        user_id: int,
        data: TelegramSubscriptionCreate,
        audit: AuditLogger,
    ) -> TelegramSubscriptionCreateResult:
        result = await self.subscription_service.create(user_id=user_id, data=data)

        await audit.log(
            action="telegram.subscription_create",
            entity_type="user",
            entity_id=user_id,
            payload={
                "subscription_id": result.id,
                "scope_type": result.scope_type.value,
                "scope_id": result.scope_id,
                "event_type": result.event_type.value,
                "delivery_mode": result.delivery_mode.value,
            },
        )

        return TelegramSubscriptionCreateResult(subscription=result)

    async def delete_subscription(
        self,
        *,
        user_id: int,
        subscription_id: int,
        audit: AuditLogger,
    ) -> TelegramSubscriptionDeleteResult:
        await self.subscription_service.delete(
            user_id=user_id,
            subscription_id=subscription_id,
        )

        await audit.log(
            action="telegram.subscription_delete",
            entity_type="user",
            entity_id=user_id,
            payload={"subscription_id": subscription_id},
        )

        return TelegramSubscriptionDeleteResult()
