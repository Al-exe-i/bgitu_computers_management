from fastapi import BackgroundTasks

from modules.identity.events import AuthSecurityNotificationEvent, IdentityEvent
from utils.telegram_notifications import enqueue_auth_security_notification


def dispatch_identity_events(
    background_tasks: BackgroundTasks,
    events: list[IdentityEvent],
) -> None:
    for event in events:
        if isinstance(event, AuthSecurityNotificationEvent):
            enqueue_auth_security_notification(
                background_tasks,
                user_id=event.user_id,
                event_name=event.event_name,
                ip=event.ip,
                user_agent=event.user_agent,
            )
