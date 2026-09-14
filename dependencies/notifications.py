from typing import Annotated

from fastapi import Depends

from db.session import session_dep
from dependencies.user import user_service_dep
from modules.inventory.adapters.directories import (
    AudienceDirectoryReader,
    OfficeDirectoryReader,
)
from modules.inventory.repositories.audiences import AudienceRepository
from modules.inventory.repositories.offices import OfficeRepository
from modules.notifications.application import RealtimeNotificationSubscriptionUseCases
from modules.notifications.repositories.subscriptions import (
    NotificationSubscriptionRepository,
)
from modules.notifications.services.subscriptions import NotificationSubscriptionService


def get_notification_subscription_service(
    db: session_dep,
    users: user_service_dep,
) -> NotificationSubscriptionService:
    return NotificationSubscriptionService(
        NotificationSubscriptionRepository(db),
        users,
        AudienceDirectoryReader(AudienceRepository(db)),
        OfficeDirectoryReader(OfficeRepository(db)),
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
