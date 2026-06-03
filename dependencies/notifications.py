from typing import Annotated

from fastapi import Depends

from db.session import session_dep
from dependencies.cache import user_cache_dep
from modules.notifications.application import RealtimeNotificationSubscriptionUseCases
from repositories.audience_repo import AudienceRepository
from repositories.notification_subscription_repo import NotificationSubscriptionRepository
from repositories.office_repo import OfficeRepository
from repositories.user_repo import UserRepository
from services.notification_subscription_service import NotificationSubscriptionService


def get_notification_subscription_service(
    db: session_dep,
    user_cache: user_cache_dep,
) -> NotificationSubscriptionService:
    return NotificationSubscriptionService(
        NotificationSubscriptionRepository(db),
        UserRepository(db, user_cache),
        AudienceRepository(db),
        OfficeRepository(db),
    )


notification_subscription_service_dep = Annotated[
    NotificationSubscriptionService,
    Depends(get_notification_subscription_service),
]


def get_realtime_notification_subscription_use_cases(
    subscription_service: notification_subscription_service_dep,
) -> RealtimeNotificationSubscriptionUseCases:
    return RealtimeNotificationSubscriptionUseCases(subscription_service=subscription_service)


realtime_notification_subscription_use_cases_dep = Annotated[
    RealtimeNotificationSubscriptionUseCases,
    Depends(get_realtime_notification_subscription_use_cases),
]
