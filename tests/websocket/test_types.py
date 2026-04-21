from datetime import datetime, timezone

from websocket.types import (
    ALL_AUDIENCES,
    AudienceUpdatedEvent,
    RedisConnectionMeta,
    decode_audience_key,
    encode_audience_key,
)


def test_encode_and_decode_audience_keys_handle_global_scope() -> None:
    assert encode_audience_key(None) == ALL_AUDIENCES
    assert decode_audience_key(None) is None
    assert decode_audience_key(ALL_AUDIENCES) is None
    assert decode_audience_key("") is None
    assert encode_audience_key(7) == "7"
    assert decode_audience_key("7") == 7


def test_redis_connection_meta_roundtrip_preserves_fields() -> None:
    connected_at = datetime(2026, 4, 21, 12, 0, tzinfo=timezone.utc)
    last_seen = datetime(2026, 4, 21, 12, 5, tzinfo=timezone.utc)
    meta = RedisConnectionMeta(
        connection_id="conn-1",
        instance_id="instance-1",
        audience_id=5,
        user_id=11,
        connected_at=connected_at,
        last_seen=last_seen,
        ip="127.0.0.1",
        user_agent="pytest",
    )

    restored = RedisConnectionMeta.from_mapping(meta.to_mapping())

    assert restored == meta


def test_audience_updated_event_payload_roundtrip() -> None:
    event = AudienceUpdatedEvent(
        event_id="event-1",
        type="audience_updated",
        audience_id=8,
        sent_at=datetime(2026, 4, 21, 12, 10, tzinfo=timezone.utc),
    )

    restored = AudienceUpdatedEvent.from_payload(event.to_payload())

    assert restored == event
