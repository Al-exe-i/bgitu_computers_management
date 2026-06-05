from core.outbox import OutboxEventType
from modules.inventory.events import (
    AudienceUpdatedEvent,
    HardwareStateChangedEvent,
    InventoryEvent,
)
from services.outbox_service import OutboxPublisher


class InventoryEventDispatcher:
    def __init__(self, outbox: OutboxPublisher) -> None:
        self.outbox = outbox

    async def dispatch(self, events: list[InventoryEvent]) -> None:
        for event in events:
            if isinstance(event, AudienceUpdatedEvent):
                await self.outbox.publish(
                    event_type=OutboxEventType.INVENTORY_AUDIENCE_UPDATED.value,
                    payload={
                        "audience_id": event.audience_id,
                        "notify_subscribers": event.notify_subscribers,
                    },
                )
            elif isinstance(event, HardwareStateChangedEvent):
                await self._dispatch_hardware_state_changed(event)

    async def _dispatch_hardware_state_changed(self, event: HardwareStateChangedEvent) -> None:
        hardware = event.hardware
        payload = {
            "previous_state": event.previous_state,
            "hardware_id": hardware.id,
            "audience_id": hardware.audience_id,
            "state": hardware.state,
            "hardware_type": getattr(hardware.type, "value", hardware.type),
            "title": hardware.title,
            "description": hardware.description,
            "inv_number": hardware.inv_number,
            "x": hardware.x,
            "y": hardware.y,
            "actor_user_id": event.actor_user_id,
        }

        await self.outbox.publish(
            event_type=OutboxEventType.INVENTORY_HARDWARE_STATE_CHANGED.value,
            payload=payload,
        )
