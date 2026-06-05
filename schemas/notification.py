import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationScopeType(str, enum.Enum):
    audience = "audience"
    office = "office"
    user = "user"


class NotificationEventType(str, enum.Enum):
    audience_changed = "audience_changed"
    hardware_fault = "hardware_fault"
    hardware_recovered = "hardware_recovered"
    auth_security = "auth_security"


class NotificationSubscriptionCreate(BaseModel):
    scope_type: NotificationScopeType
    scope_id: int = Field(gt=0)
    event_type: NotificationEventType


class NotificationSubscriptionResponse(BaseModel):
    id: int
    scope_type: NotificationScopeType
    scope_id: int
    event_type: NotificationEventType
    enabled: bool
    created_at: datetime


class RealtimeNotificationPayload(BaseModel):
    notification_id: str
    event_type: NotificationEventType
    title: str
    message: str
    scope_type: NotificationScopeType | None = None
    scope_id: int | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    audience_id: int | None = None
    audience_public_id: UUID | None = None
    payload: dict = Field(default_factory=dict)
    created_at: datetime
