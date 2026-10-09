from datetime import UTC, datetime
from uuid import uuid4

from modules.notifications.contracts import (
    AudienceChangedNotification,
    AuthSecurityNotification,
    HardwareStateNotification,
)
from modules.notifications.schemas import (
    NotificationEventType,
    NotificationScopeType,
    RealtimeNotificationPayload,
)


class RealtimeNotificationRenderer:
    def build_hardware_state_payload(
        self,
        notification: HardwareStateNotification,
        *,
        event_type: NotificationEventType,
        audience_public_id=None,
        audience_number: int | None = None,
    ) -> dict:
        is_fault = event_type == NotificationEventType.hardware_fault
        title = "Оборудование неисправно" if is_fault else "Оборудование восстановлено"
        hardware_label = notification.title or self._render_hardware_type(
            notification.hardware_type
        )
        audience_label = (
            audience_number if audience_number is not None else notification.audience_id
        )
        message_parts = [f"{hardware_label} в аудитории {audience_label}"]

        if notification.x is not None and notification.y is not None:
            message_parts.append(
                f"ряд {notification.y + 1}, позиция {notification.x + 1}"
            )

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
            audience_public_id=audience_public_id,
            payload={
                "audience_id": notification.audience_id,
                "audience_public_id": str(audience_public_id)
                if audience_public_id
                else None,
                "audience_number": audience_number,
                "hardware_id": notification.hardware_id,
                "hardware_type": notification.hardware_type,
                "title": notification.title,
                "description": notification.description,
                "inv_number": notification.inv_number,
                "x": notification.x,
                "y": notification.y,
                "actor_user_id": notification.actor_user_id,
            },
            created_at=datetime.now(UTC),
        )
        return payload.model_dump(mode="json")

    def build_auth_security_payload(
        self, notification: AuthSecurityNotification
    ) -> dict:
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
            created_at=datetime.now(UTC),
        )
        return payload.model_dump(mode="json")

    def build_audience_changed_payload(
        self,
        notification: AudienceChangedNotification,
        *,
        audience_public_id=None,
        audience_number: int | None = None,
    ) -> dict:
        audience_label = (
            audience_number if audience_number is not None else notification.audience_id
        )
        payload = RealtimeNotificationPayload(
            notification_id=uuid4().hex,
            event_type=NotificationEventType.audience_changed,
            title="Аудитория обновлена",
            message=f"Изменения в аудитории {audience_label}",
            scope_type=NotificationScopeType.audience,
            scope_id=notification.audience_id,
            entity_type="audience",
            entity_id=notification.audience_id,
            audience_id=notification.audience_id,
            audience_public_id=audience_public_id,
            payload={
                "audience_id": notification.audience_id,
                "audience_public_id": str(audience_public_id)
                if audience_public_id
                else None,
                "audience_number": audience_number,
            },
            created_at=datetime.now(UTC),
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
