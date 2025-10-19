from typing import List
from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models import Audience
from models.base import Base
from models.mixins.int_id_pk_mixin import IntIdPkMixin


class Office(IntIdPkMixin, Base):
    address: Mapped[str] = mapped_column(String(100), nullable=False)

    audiences: Mapped[List["Audience"]] = relationship(
        "Audience",
        back_populates="office",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Audience.id"
    )

    __table_args__ = (
        CheckConstraint("id IN (1, 2)", name="id_check"),
    )