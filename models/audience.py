from typing import List
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
from .mixins import IntIdPkMixin


class Audience(IntIdPkMixin, Base):
    floor: Mapped[int]
    description: Mapped[str | None] = mapped_column(String(200))
    office_id: Mapped[int] = mapped_column(ForeignKey('offices.id', ondelete='CASCADE'))
    width: Mapped[int]
    height: Mapped[int]

    landmarks: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)

    hardware: Mapped[List["Hardware"]] = relationship(
        back_populates="audience",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    office: Mapped["Office"] = relationship(back_populates="audiences")