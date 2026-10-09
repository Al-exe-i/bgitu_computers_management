from typing import Any

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.mixins import IntIdPkMixin
from db.orm import Base
from modules.inventory.models.audience import Audience
from modules.inventory.models.hardware_file import HardwareFile
from modules.inventory.types import HardwareType


class Hardware(IntIdPkMixin, Base):
    inv_number: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str | None] = mapped_column(String(64))
    state: Mapped[bool] = mapped_column(default=True)
    description: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[HardwareType] = mapped_column(Enum(HardwareType))

    x: Mapped[int]
    y: Mapped[int]
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    specs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    audience_id: Mapped[int] = mapped_column(
        ForeignKey("audiences.id", ondelete="CASCADE")
    )

    audience: Mapped["Audience"] = relationship(back_populates="hardware")
    files: Mapped[list[HardwareFile]] = relationship(
        back_populates="hardware",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
