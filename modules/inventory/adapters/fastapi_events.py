from fastapi import BackgroundTasks

from modules.inventory.events import (
    AudienceUpdatedEvent,
    HardwareStateChangedEvent,
    InventoryEvent,
)
from utils.broadcast import broadcast_audience_updated
from utils.telegram_notifications import enqueue_hardware_state_notification
from websocket.service import RealtimeService


def dispatch_inventory_events(
    background_tasks: BackgroundTasks,
    realtime: RealtimeService,
    events: list[InventoryEvent],
) -> None:
    for event in events:
        if isinstance(event, AudienceUpdatedEvent):
            broadcast_audience_updated(background_tasks, realtime, event.audience_id)
        elif isinstance(event, HardwareStateChangedEvent):
            enqueue_hardware_state_notification(
                background_tasks,
                previous_state=event.previous_state,
                hardware=event.hardware,
                actor_user_id=event.actor_user_id,
            )
