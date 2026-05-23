from enum import StrEnum


class OutboxEventType(StrEnum):
    IDENTITY_AUTH_SECURITY = "identity.auth_security"
    INVENTORY_AUDIENCE_UPDATED = "inventory.audience_updated"
    INVENTORY_HARDWARE_STATE_CHANGED = "inventory.hardware_state_changed"


class OutboxEventStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
