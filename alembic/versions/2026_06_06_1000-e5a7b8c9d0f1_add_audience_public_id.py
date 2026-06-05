"""add audience public id

Revision ID: e5a7b8c9d0f1
Revises: d4f6a1c2b8e9
Create Date: 2026-06-06 10:00:00.000000

"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e5a7b8c9d0f1"
down_revision: str | Sequence[str] | None = "d4f6a1c2b8e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audiences",
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    bind = op.get_bind()
    audience_ids = bind.execute(sa.text("SELECT id FROM audiences WHERE public_id IS NULL")).scalars().all()
    for audience_id in audience_ids:
        bind.execute(
            sa.text("UPDATE audiences SET public_id = :public_id WHERE id = :audience_id"),
            {"public_id": str(uuid4()), "audience_id": audience_id},
        )

    op.alter_column(
        "audiences",
        "public_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_unique_constraint("uq_audiences_public_id", "audiences", ["public_id"])


def downgrade() -> None:
    op.drop_constraint("uq_audiences_public_id", "audiences", type_="unique")
    op.drop_column("audiences", "public_id")
