from core.outbox import OutboxEventType
from modules.identity.events import AuthSecurityNotificationEvent, IdentityEvent
from services.outbox_service import OutboxPublisher


class IdentityEventDispatcher:
    def __init__(self, outbox: OutboxPublisher) -> None:
        self.outbox = outbox

    async def dispatch(self, events: list[IdentityEvent]) -> None:
        for event in events:
            if isinstance(event, AuthSecurityNotificationEvent):
                await self.outbox.publish(
                    event_type=OutboxEventType.IDENTITY_AUTH_SECURITY.value,
                    payload={
                        "user_id": event.user_id,
                        "event_name": event.event_name,
                        "ip": event.ip,
                        "user_agent": event.user_agent,
                    },
                )
