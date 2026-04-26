from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class AuthSecurityNotificationEvent:
    user_id: int
    event_name: str
    ip: str | None = None
    user_agent: str | None = None


IdentityEvent = AuthSecurityNotificationEvent
