from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.mixins import IntIdPkMixin


class NotificationSubscription(IntIdPkMixin, Base):
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "scope_type",
            "scope_id",
            "event_type",
        ),
        Index(
            "ix_notification_subscriptions_event_scope",
            "event_type",
            "scope_type",
            "scope_id",
            "enabled",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_id: Mapped[int] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
