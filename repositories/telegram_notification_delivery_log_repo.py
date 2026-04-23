from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from models.telegram_notification_delivery_log import TelegramNotificationDeliveryLog


class TelegramNotificationDeliveryLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_many(
        self,
        delivery_logs: Sequence[TelegramNotificationDeliveryLog],
    ) -> None:
        if not delivery_logs:
            return

        self.db.add_all(list(delivery_logs))
        await self.db.flush()
