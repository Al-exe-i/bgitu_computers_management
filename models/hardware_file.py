from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column
from models.base import Base
from models.mixins import IntIdPkMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.hardware import Hardware


class HardwareFile(IntIdPkMixin, Base):
    file_path: Mapped[str]
    file_type: Mapped[str]
    hardware_id: Mapped[int] = mapped_column(
        ForeignKey("hardwares.id", ondelete="CASCADE"), nullable=False
    )

    hardware: Mapped["Hardware"] = relationship(back_populates="files")
