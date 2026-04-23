import asyncio
from contextlib import asynccontextmanager

from tasks.notifications import TelegramDeliveryResult, _persist_delivery_results


class FakeSession:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


def test_persist_delivery_results_creates_delivery_log_rows(monkeypatch) -> None:
    captured: dict = {}
    session = FakeSession()

    class FakeRepo:
        def __init__(self, db) -> None:
            captured["repo_session"] = db

        async def create_many(self, delivery_logs) -> None:
            captured["delivery_logs"] = list(delivery_logs)

    @asynccontextmanager
    async def fake_open_task_session():
        yield session

    monkeypatch.setattr("tasks.notifications.open_task_session", fake_open_task_session)
    monkeypatch.setattr(
        "tasks.notifications.TelegramNotificationDeliveryLogRepository",
        FakeRepo,
    )

    asyncio.run(
        _persist_delivery_results(
            notification_id="notif-1",
            event_type="hardware_fault",
            payload={"hardware_id": 42, "audience_id": 215},
            results=[
                TelegramDeliveryResult(
                    telegram_id=1001,
                    delivered=True,
                    attempts=1,
                ),
                TelegramDeliveryResult(
                    telegram_id=1002,
                    delivered=False,
                    attempts=3,
                    error_type="TelegramNetworkError",
                    error_message="temporary failure",
                ),
            ],
        )
    )

    delivery_logs = captured["delivery_logs"]
    assert len(delivery_logs) == 2
    assert captured["repo_session"] is session
    assert session.committed is True

    assert delivery_logs[0].notification_id == "notif-1"
    assert delivery_logs[0].event_type == "hardware_fault"
    assert delivery_logs[0].telegram_id == 1001
    assert delivery_logs[0].status == "delivered"
    assert delivery_logs[0].attempts == 1
    assert delivery_logs[0].error_type is None
    assert delivery_logs[0].delivered_at is not None
    assert delivery_logs[0].payload == {"hardware_id": 42, "audience_id": 215}

    assert delivery_logs[1].telegram_id == 1002
    assert delivery_logs[1].status == "failed"
    assert delivery_logs[1].attempts == 3
    assert delivery_logs[1].error_type == "TelegramNetworkError"
    assert delivery_logs[1].error_message == "temporary failure"
    assert delivery_logs[1].delivered_at is None
    assert delivery_logs[1].payload == {"hardware_id": 42, "audience_id": 215}
