from core.exceptions import NotificationAudienceNotFoundError
from modules.notifications.contracts import (
    AudienceChangedNotification,
    AuthSecurityNotification,
    HardwareStateNotification,
    RealtimeNotificationDispatchResult,
)
from modules.notifications.ports import RealtimeNotificationPublisher
from modules.notifications.schemas import NotificationEventType
from modules.notifications.services.recipients import (
    RealtimeNotificationRecipientService,
)
from modules.notifications.services.renderer import RealtimeNotificationRenderer


class RealtimeNotificationDispatcher:
    def __init__(
        self,
        *,
        recipients: RealtimeNotificationRecipientService,
        renderer: RealtimeNotificationRenderer,
        publisher: RealtimeNotificationPublisher,
    ) -> None:
        self.recipients = recipients
        self.renderer = renderer
        self.publisher = publisher

    async def send_hardware_state(
        self,
        notification: HardwareStateNotification,
    ) -> RealtimeNotificationDispatchResult:
        event_type = self._hardware_event_type(notification)
        if event_type is None:
            return RealtimeNotificationDispatchResult(sent=0, event_type="unknown")

        try:
            recipient_ids = await self.recipients.get_hardware_event_recipient_user_ids(
                audience_id=notification.audience_id,
                event_type=event_type,
                exclude_user_id=notification.actor_user_id,
            )
        except NotificationAudienceNotFoundError:
            return RealtimeNotificationDispatchResult(sent=0, event_type=event_type.value)

        try:
            audience = await self.recipients.get_audience_context(
                audience_id=notification.audience_id,
                event_type=event_type,
            )
        except NotificationAudienceNotFoundError:
            return RealtimeNotificationDispatchResult(sent=0, event_type=event_type.value)

        payload = self.renderer.build_hardware_state_payload(
            notification,
            event_type=event_type,
            audience_public_id=getattr(audience, "public_id", None),
            audience_number=getattr(audience, "number", None),
        )
        await self._publish_to_recipients(recipient_ids, payload)
        return RealtimeNotificationDispatchResult(sent=len(recipient_ids), event_type=event_type.value)

    async def send_auth_security(
        self,
        notification: AuthSecurityNotification,
    ) -> RealtimeNotificationDispatchResult:
        event_type = NotificationEventType.auth_security
        recipient_ids = await self.recipients.get_user_event_recipient_user_ids(
            user_id=notification.user_id,
            event_type=event_type,
        )
        payload = self.renderer.build_auth_security_payload(notification)
        await self._publish_to_recipients(recipient_ids, payload)
        return RealtimeNotificationDispatchResult(sent=len(recipient_ids), event_type=event_type.value)

    async def send_audience_changed(
        self,
        notification: AudienceChangedNotification,
    ) -> RealtimeNotificationDispatchResult:
        event_type = NotificationEventType.audience_changed
        try:
            recipient_ids = await self.recipients.get_audience_event_recipient_user_ids(
                audience_id=notification.audience_id,
                event_type=event_type,
            )
        except NotificationAudienceNotFoundError:
            return RealtimeNotificationDispatchResult(sent=0, event_type=event_type.value)

        try:
            audience = await self.recipients.get_audience_context(
                audience_id=notification.audience_id,
                event_type=event_type,
            )
        except NotificationAudienceNotFoundError:
            return RealtimeNotificationDispatchResult(sent=0, event_type=event_type.value)

        payload = self.renderer.build_audience_changed_payload(
            notification,
            audience_public_id=getattr(audience, "public_id", None),
            audience_number=getattr(audience, "number", None),
        )
        await self._publish_to_recipients(recipient_ids, payload)
        return RealtimeNotificationDispatchResult(sent=len(recipient_ids), event_type=event_type.value)

    async def _publish_to_recipients(self, recipient_ids: list[int], payload: dict) -> None:
        for user_id in recipient_ids:
            await self.publisher.publish_notification(user_id=user_id, payload=payload)

    @staticmethod
    def _hardware_event_type(notification: HardwareStateNotification) -> NotificationEventType | None:
        if notification.previous_state == notification.state:
            return None

        if notification.previous_state and not notification.state:
            return NotificationEventType.hardware_fault

        return NotificationEventType.hardware_recovered
