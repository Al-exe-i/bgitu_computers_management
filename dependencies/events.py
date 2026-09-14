from typing import Annotated

from fastapi import Depends

from db.session import session_dep
from dependencies.realtime import realtime_dep
from modules.identity.adapters.fastapi_events import IdentityEventDispatcher
from modules.inventory.adapters.directories import AudienceDirectoryReader
from modules.inventory.adapters.fastapi_events import InventoryEventDispatcher
from modules.inventory.repositories.audiences import AudienceRepository
from modules.notifications.repositories.subscriptions import (
    NotificationSubscriptionRepository,
)
from modules.notifications.services.delivery import RealtimeNotificationDispatcher
from modules.notifications.services.recipients import (
    RealtimeNotificationRecipientService,
)
from modules.notifications.services.renderer import RealtimeNotificationRenderer


def get_realtime_notification_dispatcher(
    session: session_dep,
    realtime: realtime_dep,
) -> RealtimeNotificationDispatcher:
    return RealtimeNotificationDispatcher(
        recipients=RealtimeNotificationRecipientService(
            NotificationSubscriptionRepository(session),
            AudienceDirectoryReader(AudienceRepository(session)),
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
