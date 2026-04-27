import asyncio

from services.telegram_delivery_log_service import TelegramDeliveryLogService
from services.telegram_delivery_service import TelegramDeliveryResult


def test_delivery_log_service_creates_delivery_log_rows() -> None:
    class FakeRepo:
        def __init__(self) -> None:
            self.delivery_logs = []

        async def create_many(self, delivery_logs) -> None:
            self.delivery_logs = list(delivery_logs)

    repo = FakeRepo()
    asyncio.run(
        TelegramDeliveryLogService(repo).save_results(
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

    delivery_logs = repo.delivery_logs
    assert len(delivery_logs) == 2

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
