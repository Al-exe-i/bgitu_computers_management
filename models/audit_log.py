# models/audit_log.py
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from models.base import Base
from models.mixins import IntIdPkMixin

if TYPE_CHECKING:
    from models.user import User


class AuditLog(IntIdPkMixin, Base):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    method: Mapped[str | None] = mapped_column(String(8), nullable=True)

    # Связь с пользователем-инициатором, чтобы в журнале показывать его логин,
    # а не «Пользователь #N». Грузим заранее (selectin), чтобы не падать в async-режиме.
    user: Mapped["User | None"] = relationship(
        "User",
        lazy="selectin",
        viewonly=True,
    )
