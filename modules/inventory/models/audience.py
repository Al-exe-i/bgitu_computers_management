from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.mixins import IntIdPkMixin
from db.orm import Base
from modules.inventory.types import RoomType

if TYPE_CHECKING:
    from modules.inventory.models.hardware import Hardware
    from modules.inventory.models.office import Office


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
    room_type: Mapped[RoomType] = mapped_column(
        SQLEnum(
            RoomType,
            native_enum=False,
            create_constraint=True,
            length=20,
            name="audience_room_type",
        ),
        nullable=False,
        default=RoomType.educational,
        server_default="educational",
    )
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
