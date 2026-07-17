import asyncio
from types import SimpleNamespace

from db.post_commit import run_post_commit_hooks
from modules.inventory.adapters.fastapi_events import InventoryEventDispatcher
from modules.inventory.events import AudienceUpdatedEvent, HardwareStateChangedEvent
from services.realtime_notification_service import (
    AudienceChangedNotification,
    HardwareStateNotification,
)


class FakeSession:
    def __init__(self) -> None:
        self.info = {}


class FakeRealtime:
    def __init__(self, calls: list[tuple[str, object]]) -> None:
        self.calls = calls

    async def publish_audience_updated(self, audience_id: int) -> None:
        self.calls.append(("audience_updated", audience_id))


class FakeNotifications:
    def __init__(self, calls: list[tuple[str, object]]) -> None:
        self.calls = calls

    async def send_audience_changed(self, notification: AudienceChangedNotification) -> None:
        self.calls.append(("audience_notification", notification))

    async def send_hardware_state(self, notification: HardwareStateNotification) -> None:
        self.calls.append(("hardware_notification", notification))


def test_inventory_event_dispatcher_sends_events_after_commit() -> None:
    async def scenario() -> None:
        calls: list[tuple[str, object]] = []
        session = FakeSession()
        dispatcher = InventoryEventDispatcher(
            session,
            FakeRealtime(calls),
            FakeNotifications(calls),
        )
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

        assert calls == []

        await run_post_commit_hooks(session)

        assert calls == [
            ("audience_updated", 12),
            ("audience_notification", AudienceChangedNotification(audience_id=12)),
            (
                "hardware_notification",
                HardwareStateNotification(
                    previous_state=True,
                    hardware_id=9,
                    audience_id=12,
                    state=False,
                    hardware_type="computer",
                    title="PC",
                    description="Broken",
                    inv_number="INV-1",
                    x=1,
                    y=2,
                    actor_user_id=7,
                ),
            ),
        ]

    asyncio.run(scenario())


def test_inventory_event_dispatcher_can_skip_audience_notification() -> None:
    async def scenario() -> None:
        calls: list[tuple[str, object]] = []
        session = FakeSession()
        dispatcher = InventoryEventDispatcher(
            session,
            FakeRealtime(calls),
            FakeNotifications(calls),
        )

        await dispatcher.dispatch(
            [AudienceUpdatedEvent(audience_id=12, notify_subscribers=False)]
        )
        await run_post_commit_hooks(session)

        assert calls == [("audience_updated", 12)]

    asyncio.run(scenario())
