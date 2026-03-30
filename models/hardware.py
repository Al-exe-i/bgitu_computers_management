import enum
from sqlalchemy import String, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models import Audience
from models.base import Base
from models.hardware_file import HardwareFile
from models.mixins import IntIdPkMixin


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
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    audience_id: Mapped[int] = mapped_column(ForeignKey('audiences.id', ondelete='CASCADE'))

    audience: Mapped["Audience"] = relationship(back_populates="hardware")
    files: Mapped[list[HardwareFile]] = relationship(
        back_populates="hardware",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
