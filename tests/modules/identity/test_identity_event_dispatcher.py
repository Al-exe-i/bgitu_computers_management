import asyncio

from db.post_commit import run_post_commit_hooks
from modules.identity.adapters.fastapi_events import IdentityEventDispatcher
from modules.identity.events import AuthSecurityNotificationEvent
from services.realtime_notification_service import AuthSecurityNotification


class FakeSession:
    def __init__(self) -> None:
        self.info = {}


class FakeNotifications:
    def __init__(self) -> None:
        self.auth_security: list[AuthSecurityNotification] = []

    async def send_auth_security(self, notification: AuthSecurityNotification) -> None:
        self.auth_security.append(notification)


def test_identity_event_dispatcher_sends_notification_after_commit() -> None:
    async def scenario() -> None:
        session = FakeSession()
        notifications = FakeNotifications()
        dispatcher = IdentityEventDispatcher(session, notifications)

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

        assert notifications.auth_security == []

        await run_post_commit_hooks(session)

        assert notifications.auth_security == [
            AuthSecurityNotification(
                user_id=7,
                event_name="Login",
                ip="127.0.0.1",
                user_agent="pytest",
            )
        ]

    asyncio.run(scenario())
