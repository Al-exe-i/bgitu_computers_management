from functools import partial

from sqlalchemy.ext.asyncio import AsyncSession

from db.post_commit import add_post_commit_hook
from modules.identity.events import AuthSecurityNotificationEvent, IdentityEvent
from modules.notifications.public import AuthSecurityNotification, NotificationDelivery


class IdentityEventDispatcher:
    def __init__(
        self,
        session: AsyncSession,
        notifications: NotificationDelivery,
    ) -> None:
        self.session = session
        self.notifications = notifications

    async def dispatch(self, events: list[IdentityEvent]) -> None:
        for event in events:
            if not isinstance(event, AuthSecurityNotificationEvent):
                continue

            notification = AuthSecurityNotification(
                user_id=event.user_id,
                event_name=event.event_name,
                ip=event.ip,
                user_agent=event.user_agent,
            )
            add_post_commit_hook(
                self.session,
                partial(self.notifications.send_auth_security, notification),
            )
