from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.orm import Base


class FloorPlan(Base):
    __tablename__ = "floor_plans"
    __table_args__ = (
        CheckConstraint(
            "width BETWEEN 1 AND 50 AND height BETWEEN 1 AND 50",
            name="ck_floor_plan_dimensions",
        ),
        CheckConstraint("revision >= 0", name="ck_floor_plan_revision"),
    )
    office_id: Mapped[int] = mapped_column(
        ForeignKey("offices.id", ondelete="CASCADE"), primary_key=True
    )
    floor: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    width: Mapped[int] = mapped_column(
        Integer, nullable=False, default=20, server_default="20"
    )
    height: Mapped[int] = mapped_column(
        Integer, nullable=False, default=12, server_default="12"
    )
    revision: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    positions: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    landmarks: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
