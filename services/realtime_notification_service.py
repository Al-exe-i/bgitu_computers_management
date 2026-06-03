from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from loguru import logger

from core.exceptions import NotificationAudienceNotFoundError
from repositories.audience_repo import AudienceRepository
from repositories.notification_subscription_repo import NotificationSubscriptionRepository
from schemas.notification import (
    NotificationEventType,
    NotificationScopeType,
    RealtimeNotificationPayload,
)


class RealtimeNotificationPublisher(Protocol):
    async def publish_notification(self, *, user_id: int, payload: dict) -> None: ...


@dataclass(slots=True, frozen=True)
class HardwareStateNotification:
    previous_state: bool
    hardware_id: int
    audience_id: int
    state: bool
    hardware_type: str | None = None
    title: str | None = None
    description: str | None = None
    inv_number: str | None = None
    x: int | None = None
    y: int | None = None
    actor_user_id: int | None = None


@dataclass(slots=True, frozen=True)
class AuthSecurityNotification:
    user_id: int
    event_name: str
    ip: str | None = None
    user_agent: str | None = None


@dataclass(slots=True, frozen=True)
class AudienceChangedNotification:
    audience_id: int


@dataclass(slots=True, frozen=True)
class RealtimeNotificationDispatchResult:
    sent: int
    event_type: str

    def as_task_result(self) -> dict[str, int | str]:
        return {
            "sent": self.sent,
            "event_type": self.event_type,
        }


class RealtimeNotificationRecipientService:
    def __init__(
        self,
        subscription_repo: NotificationSubscriptionRepository,
        audience_repo: AudienceRepository,
    ) -> None:
        self.subscription_repo = subscription_repo
        self.audience_repo = audience_repo

    async def get_hardware_event_recipient_user_ids(
        self,
        *,
        audience_id: int,
        event_type: NotificationEventType,
        exclude_user_id: int | None = None,
    ) -> list[int]:
        scopes = await self._audience_and_office_scopes(
            audience_id=audience_id,
            event_type=event_type,
        )
        return await self.subscription_repo.list_recipient_user_ids(
            event_type=event_type.value,
            scopes=scopes,
            exclude_user_id=exclude_user_id,
        )

    async def get_audience_event_recipient_user_ids(
        self,
        *,
        audience_id: int,
        event_type: NotificationEventType,
    ) -> list[int]:
        scopes = await self._audience_and_office_scopes(
            audience_id=audience_id,
            event_type=event_type,
        )
        return await self.subscription_repo.list_recipient_user_ids(
            event_type=event_type.value,
            scopes=scopes,
        )

    async def get_user_event_recipient_user_ids(
        self,
        *,
        user_id: int,
        event_type: NotificationEventType,
    ) -> list[int]:
        return await self.subscription_repo.list_recipient_user_ids(
            event_type=event_type.value,
            scopes=[(NotificationScopeType.user.value, user_id)],
        )

    async def _audience_and_office_scopes(
        self,
        *,
        audience_id: int,
        event_type: NotificationEventType,
    ) -> list[tuple[str, int]]:
        audience = await self.audience_repo.get_one_short(audience_id)
        if audience is None:
            logger.warning(
                "Realtime notification audience not found: audience_id={} event_type={}",
                audience_id,
                event_type.value,
            )
            raise NotificationAudienceNotFoundError()

        return [
            (NotificationScopeType.audience.value, audience_id),
            (NotificationScopeType.office.value, audience.office_id),
        ]


class RealtimeNotificationRenderer:
    def build_hardware_state_payload(
        self,
        notification: HardwareStateNotification,
        *,
        event_type: NotificationEventType,
    ) -> dict:
        is_fault = event_type == NotificationEventType.hardware_fault
        title = "Оборудование неисправно" if is_fault else "Оборудование восстановлено"
        hardware_label = notification.title or self._render_hardware_type(notification.hardware_type)
        message_parts = [f"{hardware_label} в аудитории {notification.audience_id}"]

        if notification.x is not None and notification.y is not None:
            message_parts.append(f"ряд {notification.y + 1}, позиция {notification.x + 1}")

        payload = RealtimeNotificationPayload(
            notification_id=uuid4().hex,
            event_type=event_type,
            title=title,
            message=", ".join(message_parts),
            scope_type=NotificationScopeType.audience,
            scope_id=notification.audience_id,
            entity_type="hardware",
            entity_id=notification.hardware_id,
            audience_id=notification.audience_id,
            payload={
                "hardware_id": notification.hardware_id,
                "hardware_type": notification.hardware_type,
                "title": notification.title,
                "description": notification.description,
                "inv_number": notification.inv_number,
                "x": notification.x,
                "y": notification.y,
                "actor_user_id": notification.actor_user_id,
            },
            created_at=datetime.now(timezone.utc),
        )
        return payload.model_dump(mode="json")

    def build_auth_security_payload(self, notification: AuthSecurityNotification) -> dict:
        payload = RealtimeNotificationPayload(
            notification_id=uuid4().hex,
            event_type=NotificationEventType.auth_security,
            title="Событие безопасности",
            message=notification.event_name,
            scope_type=NotificationScopeType.user,
            scope_id=notification.user_id,
            entity_type="user",
            entity_id=notification.user_id,
            payload={
                "event_name": notification.event_name,
                "ip": notification.ip,
                "user_agent": notification.user_agent,
            },
            created_at=datetime.now(timezone.utc),
        )
        return payload.model_dump(mode="json")

    def build_audience_changed_payload(self, notification: AudienceChangedNotification) -> dict:
        payload = RealtimeNotificationPayload(
            notification_id=uuid4().hex,
            event_type=NotificationEventType.audience_changed,
            title="Аудитория обновлена",
            message=f"Изменения в аудитории {notification.audience_id}",
            scope_type=NotificationScopeType.audience,
            scope_id=notification.audience_id,
            entity_type="audience",
            entity_id=notification.audience_id,
            audience_id=notification.audience_id,
            payload={"audience_id": notification.audience_id},
            created_at=datetime.now(timezone.utc),
        )
        return payload.model_dump(mode="json")

    @staticmethod
    def _render_hardware_type(hardware_type: str | None) -> str:
        if not hardware_type:
            return "Оборудование"

        return {
            "computer": "Компьютер",
            "tv": "Телевизор",
            "projector": "Проектор",
            "printer": "Принтер",
            "switch": "Коммутатор",
            "router": "Роутер",
            "server": "Сервер",
            "other": "Оборудование",
        }.get(hardware_type, hardware_type)


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

        payload = self.renderer.build_hardware_state_payload(notification, event_type=event_type)
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

        payload = self.renderer.build_audience_changed_payload(notification)
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
