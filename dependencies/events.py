from typing import Annotated

from fastapi import Depends

from db.session import session_dep
from repositories.outbox_event_repo import OutboxEventRepository
from services.outbox_service import OutboxPublisher
from modules.identity.adapters.fastapi_events import IdentityEventDispatcher
from modules.inventory.adapters.fastapi_events import InventoryEventDispatcher


def get_outbox_publisher(session: session_dep) -> OutboxPublisher:
    return OutboxPublisher(OutboxEventRepository(session))


outbox_publisher_dep = Annotated[
    OutboxPublisher,
    Depends(get_outbox_publisher),
]


def get_identity_event_dispatcher(outbox: outbox_publisher_dep) -> IdentityEventDispatcher:
    return IdentityEventDispatcher(outbox)


identity_event_dispatcher_dep = Annotated[
    IdentityEventDispatcher,
    Depends(get_identity_event_dispatcher),
]


def get_inventory_event_dispatcher(
    outbox: outbox_publisher_dep,
) -> InventoryEventDispatcher:
    return InventoryEventDispatcher(outbox)


inventory_event_dispatcher_dep = Annotated[
    InventoryEventDispatcher,
    Depends(get_inventory_event_dispatcher),
]
