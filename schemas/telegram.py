import enum
from datetime import datetime

from pydantic import BaseModel, Field


class TelegramScopeType(str, enum.Enum):
    audience = "audience"
    office = "office"
    user = "user"


class TelegramEventType(str, enum.Enum):
    audience_changed = "audience_changed"
    hardware_fault = "hardware_fault"
    hardware_recovered = "hardware_recovered"
    auth_security = "auth_security"


class TelegramDeliveryMode(str, enum.Enum):
    immediate = "immediate"
    daily_digest = "daily_digest"


class TelegramLinkStatusResponse(BaseModel):
    telegram_id: str | None = None
    telegram_id_confirmed: bool


class TelegramLinkStartResponse(BaseModel):
    link_token: str
    expires_at: datetime
    bot_username: str | None = None
    bot_deep_link: str | None = None


class TelegramLinkConfirmRequest(BaseModel):
    token: str
    telegram_id: int


class TelegramSubscriptionCreate(BaseModel):
    scope_type: TelegramScopeType
    scope_id: int = Field(gt=0)
    event_type: TelegramEventType
    delivery_mode: TelegramDeliveryMode = TelegramDeliveryMode.immediate


class TelegramSubscriptionResponse(BaseModel):
    id: int
    scope_type: TelegramScopeType
    scope_id: int
    event_type: TelegramEventType
    delivery_mode: TelegramDeliveryMode
    enabled: bool
    created_at: datetime
