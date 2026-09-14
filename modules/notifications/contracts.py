from dataclasses import dataclass


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
