import enum
from typing import Dict, Any

from sqlalchemy import ForeignKey, Enum, VARCHAR, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
from models.mixins.int_id_pk_mixin import IntIdPkMixin


class HardwareType(enum.Enum):
    tv = "tv"
    camera = "camera"
    projector = "projector"
    sound_system = "sound_system"
    interactive_board = "interactive_board"
    other = "other"


class AdditionalHardware(IntIdPkMixin, Base):
    audience_id: Mapped[int] = mapped_column(ForeignKey('audiences.id', ondelete="CASCADE"))
    type: Mapped[HardwareType] = mapped_column(Enum(HardwareType))
    name: Mapped[str] = mapped_column(VARCHAR(100))  # Например: "Sony 4K TV"
    description: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True) # Например: "висит на стене под стендом БГИТУ"
    is_functional: Mapped[bool] = mapped_column(default=True)

    # Дополнительные характеристики в JSON
    specifications: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    audience: Mapped["Audience"] = relationship("Audience", back_populates="additional_hardware")