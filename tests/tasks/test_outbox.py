import asyncio

import pytest

from core.outbox import OutboxEventType
from tasks import outbox


def test_dispatch_event_routes_auth_security_notification(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(
        outbox,
        "schedule_auth_security_notification",
        lambda **payload: calls.append(payload),
    )

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


def test_dispatch_event_rejects_unknown_event_type() -> None:
    with pytest.raises(ValueError):
        asyncio.run(outbox._dispatch_event("unknown", {}))
