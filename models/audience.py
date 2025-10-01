from typing import Dict, List, Any
from sqlalchemy import JSON, Enum, VARCHAR, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
import enum
from models.mixins.int_id_pk_mixin import IntIdPkMixin


class AudienceType(enum.Enum):
    row = 0
    perimeter = 1


class Computer(IntIdPkMixin, Base):
    name: Mapped[str] = mapped_column(VARCHAR(32))
    row_id: Mapped[int] = mapped_column(ForeignKey('rows.id'))
    state: Mapped[bool] = mapped_column(default=True)

    row: Mapped["Row"] = relationship("Row", back_populates="computers")


class Row(IntIdPkMixin, Base):
    name: Mapped[str] = mapped_column(VARCHAR(6)) # row_xx - max row_99
    audience_id: Mapped[int] = mapped_column(ForeignKey('audiences.id'))

    audience: Mapped["Audience"] = relationship("Audience", back_populates="rows")
    computers: Mapped[List["Computer"]] = relationship("Computer", back_populates="row", cascade="all, delete-orphan")


class Audience(IntIdPkMixin, Base):
    #rows: Mapped[Dict[str, List[dict]] | None] = mapped_column(JSON, default=None)
    additional_hardware: Mapped[Dict[str, Any] | None] = mapped_column(JSON, default=None)
    type: Mapped[AudienceType] = mapped_column(Enum(AudienceType), default=AudienceType.row)

    rows: Mapped[List["Row"]] = relationship("Row", back_populates="audience", cascade="all, delete-orphan")