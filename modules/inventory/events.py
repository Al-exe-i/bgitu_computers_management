from dataclasses import dataclass
from typing import Protocol


class HardwareStatePayload(Protocol):
    id: int
    audience_id: int
    state: bool
    type: object
    title: str | None
    description: str | None
    inv_number: str | None
    x: int
    y: int


@dataclass(slots=True, frozen=True)
class AudienceUpdatedEvent:
    audience_id: int
    notify_subscribers: bool = True


@dataclass(slots=True, frozen=True)
class HardwareStateChangedEvent:
    previous_state: bool
    hardware: HardwareStatePayload
    actor_user_id: int | None = None


InventoryEvent = AudienceUpdatedEvent | HardwareStateChangedEvent
