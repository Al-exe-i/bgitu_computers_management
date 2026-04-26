from fastapi import APIRouter, status

from core.exceptions import (
    HTTP400,
    HTTP404,
    HTTP409,
    TelegramAccountNotLinkedError,
    TelegramScopeInvalidError,
    TelegramScopeNotFoundError,
    TelegramSubscriptionAlreadyExistsError,
    TelegramSubscriptionNotFoundError,
    TelegramUserNotFoundError,
)
from dependencies.audit_actor import user_audit_actor_dep
from dependencies.telegram import telegram_integration_use_cases_dep
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
    use_cases: telegram_integration_use_cases_dep,
):
    try:
        return await use_cases.get_link_status(user_id=audit.user.id)
    except TelegramUserNotFoundError as exc:
        raise HTTP404(exc.detail)


@router.post("/link-token", response_model=TelegramLinkStartResponse, status_code=status.HTTP_201_CREATED)
async def create_my_telegram_link_token(
    audit: user_audit_actor_dep,
    use_cases: telegram_integration_use_cases_dep,
):
    try:
        result = await use_cases.create_link_token(
            user_id=audit.user.id,
            audit=audit,
        )
    except TelegramUserNotFoundError as exc:
        raise HTTP404(exc.detail)

    return result.token


@router.delete("/link", response_model=TelegramLinkStatusResponse)
async def unlink_my_telegram_account(
    audit: user_audit_actor_dep,
    use_cases: telegram_integration_use_cases_dep,
):
    try:
        result = await use_cases.unlink_account(
            actor=audit.user,
            audit=audit,
        )
    except TelegramUserNotFoundError as exc:
        raise HTTP404(exc.detail)

    return result.status


@router.get("/subscriptions", response_model=list[TelegramSubscriptionResponse])
async def list_my_telegram_subscriptions(
    audit: user_audit_actor_dep,
    use_cases: telegram_integration_use_cases_dep,
):
    try:
        return await use_cases.list_subscriptions(user_id=audit.user.id)
    except TelegramUserNotFoundError as exc:
        raise HTTP404(exc.detail)


@router.post(
    "/subscriptions",
    response_model=TelegramSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_telegram_subscription(
    data: TelegramSubscriptionCreate,
    audit: user_audit_actor_dep,
    use_cases: telegram_integration_use_cases_dep,
):
    try:
        result = await use_cases.create_subscription(
            user_id=audit.user.id,
            data=data,
            audit=audit,
        )
    except (TelegramAccountNotLinkedError, TelegramScopeInvalidError) as exc:
        raise HTTP400(exc.detail)
    except (TelegramUserNotFoundError, TelegramScopeNotFoundError) as exc:
        raise HTTP404(exc.detail)
    except TelegramSubscriptionAlreadyExistsError as exc:
        raise HTTP409(exc.detail)

    return result.subscription


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_telegram_subscription(
    subscription_id: int,
    audit: user_audit_actor_dep,
    use_cases: telegram_integration_use_cases_dep,
):
    try:
        await use_cases.delete_subscription(
            user_id=audit.user.id,
            subscription_id=subscription_id,
            audit=audit,
        )
    except TelegramSubscriptionNotFoundError as exc:
        raise HTTP404(exc.detail)
