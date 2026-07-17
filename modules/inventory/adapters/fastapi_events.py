from functools import partial

from sqlalchemy.ext.asyncio import AsyncSession

from db.post_commit import add_post_commit_hook
from modules.inventory.events import (
    AudienceUpdatedEvent,
    HardwareStateChangedEvent,
    InventoryEvent,
)
from services.realtime_notification_service import (
    AudienceChangedNotification,
    HardwareStateNotification,
    RealtimeNotificationDispatcher,
)
from websocket.service import RealtimeService


class InventoryEventDispatcher:
    def __init__(
        self,
        session: AsyncSession,
        realtime: RealtimeService,
        notifications: RealtimeNotificationDispatcher,
    ) -> None:
        self.session = session
        self.realtime = realtime
        self.notifications = notifications

    async def dispatch(self, events: list[InventoryEvent]) -> None:
        for event in events:
            if isinstance(event, AudienceUpdatedEvent):
                self._register_audience_updated(event)
            elif isinstance(event, HardwareStateChangedEvent):
                self._register_hardware_state_changed(event)

    def _register_audience_updated(self, event: AudienceUpdatedEvent) -> None:
        add_post_commit_hook(
            self.session,
            partial(self.realtime.publish_audience_updated, event.audience_id),
        )

        if event.notify_subscribers:
            notification = AudienceChangedNotification(audience_id=event.audience_id)
            add_post_commit_hook(
                self.session,
                partial(self.notifications.send_audience_changed, notification),
            )

    def _register_hardware_state_changed(self, event: HardwareStateChangedEvent) -> None:
        hardware = event.hardware
        notification = HardwareStateNotification(
            previous_state=event.previous_state,
            hardware_id=hardware.id,
            audience_id=hardware.audience_id,
            state=hardware.state,
            hardware_type=getattr(hardware.type, "value", hardware.type),
            title=hardware.title,
            description=hardware.description,
            inv_number=hardware.inv_number,
            x=hardware.x,
            y=hardware.y,
            actor_user_id=event.actor_user_id,
        )
        add_post_commit_hook(
            self.session,
            partial(self.notifications.send_hardware_state, notification),
        )
