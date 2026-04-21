from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ALL_AUDIENCES = "__all__"


def encode_audience_key(audience_id: int | None) -> str:
    if audience_id is None:
        return ALL_AUDIENCES
    return str(audience_id)


def decode_audience_key(audience_key: str | None) -> int | None:
    if audience_key in (None, ALL_AUDIENCES, ""):
        return None
    return int(audience_key)


@dataclass(slots=True)
class RedisConnectionMeta:
    connection_id: str
    instance_id: str
    audience_id: int | None
    user_id: int | None
    connected_at: datetime
    last_seen: datetime
    ip: str | None
    user_agent: str | None

    @property
    def audience_key(self) -> str:
        return encode_audience_key(self.audience_id)

    def to_mapping(self) -> dict[str, str]:
        return {
            "connection_id": self.connection_id,
            "instance_id": self.instance_id,
            "audience_key": self.audience_key,
            "user_id": "" if self.user_id is None else str(self.user_id),
            "connected_at": self.connected_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "ip": self.ip or "",
            "user_agent": self.user_agent or "",
        }

    @classmethod
    def from_mapping(cls, data: dict[str, str]) -> "RedisConnectionMeta":
        return cls(
            connection_id=data["connection_id"],
            instance_id=data["instance_id"],
            audience_id=decode_audience_key(data.get("audience_key")),
            user_id=int(data["user_id"]) if data.get("user_id") else None,
            connected_at=datetime.fromisoformat(data["connected_at"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            ip=data.get("ip") or None,
            user_agent=data.get("user_agent") or None,
        )


@dataclass(slots=True, frozen=True)
class AudienceUpdatedEvent:
    event_id: str
    type: Literal["audience_updated"]
    audience_id: int
    sent_at: datetime

    @classmethod
    def new(cls, audience_id: int) -> "AudienceUpdatedEvent":
        return cls(
            event_id=str(uuid4()),
            type="audience_updated",
            audience_id=audience_id,
            sent_at=datetime.now(timezone.utc),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "type": self.type,
            "audience_id": self.audience_id,
            "sent_at": self.sent_at.isoformat(),
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "AudienceUpdatedEvent":
        return cls(
            event_id=str(payload["event_id"]),
            type="audience_updated",
            audience_id=int(payload["audience_id"]),
            sent_at=datetime.fromisoformat(str(payload["sent_at"])),
        )
