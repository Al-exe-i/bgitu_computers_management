from fastapi import APIRouter, status

from dependencies.audit_actor import user_audit_actor_dep
from dependencies.telegram import (
    telegram_link_service_dep,
    telegram_subscription_service_dep,
)
from schemas.telegram import (
    TelegramLinkStartResponse,
    TelegramLinkStatusResponse,
    TelegramSubscriptionCreate,
    TelegramSubscriptionResponse,
)

router = APIRouter(prefix="/telegram")


@router.get("/me", response_model=TelegramLinkStatusResponse)
async def get_my_telegram_status(
    audit: user_audit_actor_dep,
    link_service: telegram_link_service_dep,
):
    return await link_service.get_link_status(audit.user.id)


@router.post("/link-token", response_model=TelegramLinkStartResponse, status_code=status.HTTP_201_CREATED)
async def create_my_telegram_link_token(
    audit: user_audit_actor_dep,
    link_service: telegram_link_service_dep,
):
    result = await link_service.create_link_token(audit.user.id)
    await audit.log(
        action="telegram.link_token_create",
        entity_type="user",
        entity_id=audit.user.id,
        payload={"expires_at": result.expires_at.isoformat()},
    )
    return result


@router.delete("/link", response_model=TelegramLinkStatusResponse)
async def unlink_my_telegram_account(
    audit: user_audit_actor_dep,
    link_service: telegram_link_service_dep,
):
    had_telegram_id = audit.user.telegram_id is not None
    result = await link_service.unlink_user(audit.user.id)
    await audit.log(
        action="telegram.unlink",
        entity_type="user",
        entity_id=audit.user.id,
        payload={"had_telegram_id": had_telegram_id},
    )
    return result


@router.get("/subscriptions", response_model=list[TelegramSubscriptionResponse])
async def list_my_telegram_subscriptions(
    audit: user_audit_actor_dep,
    subscription_service: telegram_subscription_service_dep,
):
    return await subscription_service.list_for_user(audit.user.id)


@router.post(
    "/subscriptions",
    response_model=TelegramSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_telegram_subscription(
    data: TelegramSubscriptionCreate,
    audit: user_audit_actor_dep,
    subscription_service: telegram_subscription_service_dep,
):
    result = await subscription_service.create(user_id=audit.user.id, data=data)
    await audit.log(
        action="telegram.subscription_create",
        entity_type="user",
        entity_id=audit.user.id,
        payload={
            "subscription_id": result.id,
            "scope_type": result.scope_type.value,
            "scope_id": result.scope_id,
            "event_type": result.event_type.value,
            "delivery_mode": result.delivery_mode.value,
        },
    )
    return result


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_telegram_subscription(
    subscription_id: int,
    audit: user_audit_actor_dep,
    subscription_service: telegram_subscription_service_dep,
):
    await subscription_service.delete(
        user_id=audit.user.id,
        subscription_id=subscription_id,
    )
    await audit.log(
        action="telegram.subscription_delete",
        entity_type="user",
        entity_id=audit.user.id,
        payload={"subscription_id": subscription_id},
    )
