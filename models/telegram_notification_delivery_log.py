from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.mixins import IntIdPkMixin


class TelegramNotificationDeliveryLog(IntIdPkMixin, Base):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    notification_id: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    error_type: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
