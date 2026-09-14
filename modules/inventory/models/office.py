
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.mixins.int_id_pk_mixin import IntIdPkMixin
from db.orm import Base
from modules.inventory.models.audience import Audience


class Office(IntIdPkMixin, Base):
    address: Mapped[str] = mapped_column(String(100), nullable=False)

    audiences: Mapped[list["Audience"]] = relationship(
        back_populates="office",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Audience.floor, Audience.number",
    )
