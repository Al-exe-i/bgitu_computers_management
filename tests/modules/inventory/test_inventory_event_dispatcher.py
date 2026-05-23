import asyncio
from types import SimpleNamespace

from core.outbox import OutboxEventType
from modules.inventory.adapters.fastapi_events import InventoryEventDispatcher
from modules.inventory.events import AudienceUpdatedEvent, HardwareStateChangedEvent


class FakeOutboxPublisher:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def publish(self, *, event_type: str, payload: dict) -> None:
        self.events.append({"event_type": event_type, "payload": payload})


def test_inventory_event_dispatcher_writes_events_to_outbox() -> None:
    async def scenario() -> None:
        outbox = FakeOutboxPublisher()
        dispatcher = InventoryEventDispatcher(outbox)
        hardware = SimpleNamespace(
            id=9,
            audience_id=12,
            state=False,
            type=SimpleNamespace(value="computer"),
            title="PC",
            description="Broken",
            inv_number="INV-1",
            x=1,
            y=2,
        )

        await dispatcher.dispatch(
            [
                AudienceUpdatedEvent(audience_id=12),
                HardwareStateChangedEvent(
                    previous_state=True,
                    hardware=hardware,
                    actor_user_id=7,
                ),
            ]
        )

        assert outbox.events == [
            {
                "event_type": OutboxEventType.INVENTORY_AUDIENCE_UPDATED.value,
                "payload": {"audience_id": 12},
            },
            {
                "event_type": OutboxEventType.INVENTORY_HARDWARE_STATE_CHANGED.value,
                "payload": {
                    "previous_state": True,
                    "hardware_id": 9,
                    "audience_id": 12,
                    "state": False,
                    "hardware_type": "computer",
                    "title": "PC",
                    "description": "Broken",
                    "inv_number": "INV-1",
                    "x": 1,
                    "y": 2,
                    "actor_user_id": 7,
                },
            },
        ]

    asyncio.run(scenario())
