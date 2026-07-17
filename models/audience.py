from uuid import UUID, uuid7
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
from .mixins import IntIdPkMixin

if TYPE_CHECKING:
    from models.hardware import Hardware
    from models.office import Office


class Audience(IntIdPkMixin, Base):
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_audiences_public_id"),
        UniqueConstraint("office_id", "number", name="uq_audiences_office_id_number"),
    )

    public_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), default=uuid7, nullable=False
    )
    number: Mapped[int]
    floor: Mapped[int]
    description: Mapped[str | None] = mapped_column(String(200))
    office_id: Mapped[int] = mapped_column(ForeignKey("offices.id", ondelete="CASCADE"))
    width: Mapped[int]
    height: Mapped[int]

    landmarks: Mapped[dict[str, str]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    hardware: Mapped[list["Hardware"]] = relationship(
        back_populates="audience", cascade="all, delete-orphan", passive_deletes=True
    )

    office: Mapped["Office"] = relationship(back_populates="audiences")
