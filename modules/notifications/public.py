"""Notification commands exposed to other business modules."""
from typing import Protocol

from modules.notifications.contracts import (
    AudienceChangedNotification,
    AuthSecurityNotification,
    HardwareStateNotification,
    RealtimeNotificationDispatchResult,
)

__all__ = [
    "AudienceChangedNotification", "AuthSecurityNotification", "HardwareStateNotification",
    "NotificationDelivery", "RealtimeNotificationDispatchResult",
]


class NotificationDelivery(Protocol):
    async def send_hardware_state(self, notification: HardwareStateNotification) -> RealtimeNotificationDispatchResult: ...
    async def send_auth_security(self, notification: AuthSecurityNotification) -> RealtimeNotificationDispatchResult: ...
    async def send_audience_changed(self, notification: AudienceChangedNotification) -> RealtimeNotificationDispatchResult: ...
