from fastapi import APIRouter, status

from dependencies.audit_actor import user_audit_actor_dep
from dependencies.notifications import realtime_notification_subscription_use_cases_dep
from schemas.notification import (
    NotificationSubscriptionCreate,
    NotificationSubscriptionResponse,
)

router = APIRouter(prefix="/notifications")


@router.get("/subscriptions", response_model=list[NotificationSubscriptionResponse])
async def list_my_notification_subscriptions(
    audit: user_audit_actor_dep,
    use_cases: realtime_notification_subscription_use_cases_dep,
):
    return await use_cases.list_subscriptions(user_id=audit.user.id)


@router.post(
    "/subscriptions",
    response_model=NotificationSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_notification_subscription(
    data: NotificationSubscriptionCreate,
    audit: user_audit_actor_dep,
    use_cases: realtime_notification_subscription_use_cases_dep,
):
    result = await use_cases.create_subscription(
        user_id=audit.user.id,
        data=data,
        audit=audit,
    )

    return result.subscription


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_notification_subscription(
    subscription_id: int,
    audit: user_audit_actor_dep,
    use_cases: realtime_notification_subscription_use_cases_dep,
):
    await use_cases.delete_subscription(
        user_id=audit.user.id,
        subscription_id=subscription_id,
        audit=audit,
    )
