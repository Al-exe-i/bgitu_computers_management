from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Protocol

from models.telegram_notification_delivery_log import TelegramNotificationDeliveryLog
from services.telegram_delivery_service import TelegramDeliveryResult


class TelegramDeliveryLogRepoPort(Protocol):
    async def create_many(self, delivery_logs: list[TelegramNotificationDeliveryLog]) -> None: ...


class TelegramDeliveryLogService:
    def __init__(self, repo: TelegramDeliveryLogRepoPort) -> None:
        self.repo = repo

    async def save_results(
        self,
        *,
        notification_id: str,
        event_type: str,
        payload: dict,
        results: Sequence[TelegramDeliveryResult],
    ) -> None:
        delivery_logs = self.build_delivery_logs(
            notification_id=notification_id,
            event_type=event_type,
            payload=payload,
            results=results,
        )
        if not delivery_logs:
            return

        await self.repo.create_many(delivery_logs)

    @staticmethod
    def build_delivery_logs(
        *,
        notification_id: str,
        event_type: str,
        payload: dict,
        results: Sequence[TelegramDeliveryResult],
    ) -> list[TelegramNotificationDeliveryLog]:
        if not results:
            return []

        logged_at = datetime.now(timezone.utc)
        return [
            TelegramNotificationDeliveryLog(
                notification_id=notification_id,
                event_type=event_type,
                telegram_id=result.telegram_id,
                status="delivered" if result.delivered else "failed",
                attempts=result.attempts,
                error_type=result.error_type,
                error_message=result.error_message,
                delivered_at=logged_at if result.delivered else None,
                payload=dict(payload),
            )
            for result in results
        ]
