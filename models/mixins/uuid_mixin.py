from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid7

from sqlalchemy.dialects.postgresql import UUID as PGUUID


class UUIDPrimaryKeyMixin:
    """Примесь с UUID-первичным ключом"""

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )
