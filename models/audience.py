from typing import List
from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
import enum
from .mixins import IntIdPkMixin

class HardwareType(enum.Enum):
    computer = "computer"
    tv = "tv"
    projector = "projector"
    printer = "printer"
    switch = "switch"
    router = "router"
    other = "other"

class Hardware(IntIdPkMixin, Base):
    inv_number: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str | None] = mapped_column(String(64))
    state: Mapped[bool] = mapped_column(default=True)
    description: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[HardwareType] = mapped_column(Enum(HardwareType))
    x: Mapped[int]
    y: Mapped[int]
    audience_id: Mapped[int] = mapped_column(ForeignKey('audiences.id', ondelete='CASCADE'))

    audience: Mapped["Audience"] = relationship(
        "Audience",
        back_populates="hardware"
    )


class Audience(IntIdPkMixin, Base):
    description: Mapped[str | None] = mapped_column(String(200))
    office_id: Mapped[int] = mapped_column(ForeignKey('offices.id', ondelete='CASCADE'))
    width: Mapped[int]
    height: Mapped[int]

    hardware: Mapped[List["Hardware"]] = relationship(
        "Hardware",
        back_populates="audience",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    office: Mapped["Office"] = relationship(
        "Office",
        back_populates="audiences"
    )