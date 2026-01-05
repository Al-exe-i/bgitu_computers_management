from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column
from models.base import Base
from models.mixins import IntIdPkMixin


class HardwareFile(IntIdPkMixin, Base):
    file_path: Mapped[str]
    file_type: Mapped[str]
    hardware_id: Mapped[int] = mapped_column(ForeignKey('hardwares.id', ondelete='CASCADE'))

    hardware: Mapped["Hardware"] = relationship(back_populates="files")