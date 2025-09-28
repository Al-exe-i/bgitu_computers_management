from typing import Dict, List, Any
from sqlalchemy import Column, Integer, JSON, Enum
from sqlalchemy.orm import Mapped, MappedColumn, mapped_column
from models.base import Base
import enum
from models.mixins.int_id_pk_mixin import IntIdPkMixin


class AudienceType(enum.Enum):
    row = 0
    perimeter = 1


class Audience(IntIdPkMixin, Base):
    rows: Mapped[Dict[str, List[dict]] | None] = mapped_column(JSON, default=None)
    additional_hardware: Mapped[Dict[str, Any] | None] = mapped_column(JSON, default=None)
    type: Mapped[AudienceType] = MappedColumn(Enum(AudienceType), default=AudienceType.row)