import asyncio

import pytest

from core.outbox import OutboxEventType
from tasks import outbox


def test_dispatch_event_routes_auth_security_notification(monkeypatch) -> None:
    calls: list[dict] = []

    async def fake_send(payload: dict) -> None:
        calls.append(payload)

    monkeypatch.setattr(outbox, "_send_realtime_auth_security_notification", fake_send)

    asyncio.run(
        outbox._dispatch_event(
            OutboxEventType.IDENTITY_AUTH_SECURITY.value,
            {
                "user_id": 7,
                "event_name": "Login",
                "ip": "127.0.0.1",
                "user_agent": "pytest",
            },
        )
    )

    assert calls == [
        {
            "user_id": 7,
            "event_name": "Login",
            "ip": "127.0.0.1",
            "user_agent": "pytest",
        }
    ]


def test_dispatch_event_routes_hardware_state_notification(monkeypatch) -> None:
    calls: list[dict] = []

    async def fake_send(payload: dict) -> None:
        calls.append(payload)

    monkeypatch.setattr(outbox, "_send_realtime_hardware_state_notification", fake_send)

    asyncio.run(
        outbox._dispatch_event(
            OutboxEventType.INVENTORY_HARDWARE_STATE_CHANGED.value,
            {
                "previous_state": True,
                "hardware_id": 4,
                "audience_id": 10,
                "state": False,
            },
        )
    )

    assert calls == [
        {
            "previous_state": True,
            "hardware_id": 4,
            "audience_id": 10,
            "state": False,
        }
    ]


def test_dispatch_event_routes_audience_update_and_notification(monkeypatch) -> None:
    calls: list[tuple[str, int | dict]] = []

    async def fake_publish(audience_id: int) -> None:
        calls.append(("audience_updated", audience_id))

    async def fake_send(payload: dict) -> None:
        calls.append(("audience_notification", payload))

    monkeypatch.setattr(outbox, "_publish_audience_updated", fake_publish)
    monkeypatch.setattr(outbox, "_send_realtime_audience_changed_notification", fake_send)

    asyncio.run(
        outbox._dispatch_event(
            OutboxEventType.INVENTORY_AUDIENCE_UPDATED.value,
            {"audience_id": 10},
        )
    )

    assert calls == [
        ("audience_updated", 10),
        ("audience_notification", {"audience_id": 10}),
    ]


def test_dispatch_event_rejects_unknown_event_type() -> None:
    with pytest.raises(ValueError):
        asyncio.run(outbox._dispatch_event("unknown", {}))
