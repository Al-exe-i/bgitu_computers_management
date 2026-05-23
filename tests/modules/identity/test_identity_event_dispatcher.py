import asyncio

from core.outbox import OutboxEventType
from modules.identity.adapters.fastapi_events import IdentityEventDispatcher
from modules.identity.events import AuthSecurityNotificationEvent


class FakeOutboxPublisher:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def publish(self, *, event_type: str, payload: dict) -> None:
        self.events.append({"event_type": event_type, "payload": payload})


def test_identity_event_dispatcher_writes_auth_security_event_to_outbox() -> None:
    async def scenario() -> None:
        outbox = FakeOutboxPublisher()
        dispatcher = IdentityEventDispatcher(outbox)

        await dispatcher.dispatch(
            [
                AuthSecurityNotificationEvent(
                    user_id=7,
                    event_name="Login",
                    ip="127.0.0.1",
                    user_agent="pytest",
                )
            ]
        )

        assert outbox.events == [
            {
                "event_type": OutboxEventType.IDENTITY_AUTH_SECURITY.value,
                "payload": {
                    "user_id": 7,
                    "event_name": "Login",
                    "ip": "127.0.0.1",
                    "user_agent": "pytest",
                },
            }
        ]

    asyncio.run(scenario())
