from typing import Annotated

from fastapi import Depends

from db.session import session_dep
from dependencies.realtime import realtime_dep
from modules.identity.adapters.fastapi_events import IdentityEventDispatcher
from modules.inventory.adapters.fastapi_events import InventoryEventDispatcher
from repositories.audience_repo import AudienceRepository
from repositories.notification_subscription_repo import NotificationSubscriptionRepository
from services.realtime_notification_service import (
    RealtimeNotificationDispatcher,
    RealtimeNotificationRecipientService,
    RealtimeNotificationRenderer,
)


def get_realtime_notification_dispatcher(
    session: session_dep,
    realtime: realtime_dep,
) -> RealtimeNotificationDispatcher:
    return RealtimeNotificationDispatcher(
        recipients=RealtimeNotificationRecipientService(
            NotificationSubscriptionRepository(session),
            AudienceRepository(session),
        ),
        renderer=RealtimeNotificationRenderer(),
        publisher=realtime,
    )


realtime_notification_dispatcher_dep = Annotated[
    RealtimeNotificationDispatcher,
    Depends(get_realtime_notification_dispatcher),
]


def get_identity_event_dispatcher(
    session: session_dep,
    notifications: realtime_notification_dispatcher_dep,
) -> IdentityEventDispatcher:
    return IdentityEventDispatcher(session, notifications)


identity_event_dispatcher_dep = Annotated[
    IdentityEventDispatcher,
    Depends(get_identity_event_dispatcher),
]


def get_inventory_event_dispatcher(
    session: session_dep,
    realtime: realtime_dep,
    notifications: realtime_notification_dispatcher_dep,
) -> InventoryEventDispatcher:
    return InventoryEventDispatcher(session, realtime, notifications)


inventory_event_dispatcher_dep = Annotated[
    InventoryEventDispatcher,
    Depends(get_inventory_event_dispatcher),
]
