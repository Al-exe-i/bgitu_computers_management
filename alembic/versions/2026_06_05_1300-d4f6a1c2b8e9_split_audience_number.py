"""split audience id and room number

Revision ID: d4f6a1c2b8e9
Revises: c7e42a9d1b0f
Create Date: 2026-06-05 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4f6a1c2b8e9"
down_revision: str | Sequence[str] | None = "c7e42a9d1b0f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("audiences", sa.Column("number", sa.Integer(), nullable=True))
    op.execute("UPDATE audiences SET number = id")
    op.alter_column("audiences", "number", existing_type=sa.Integer(), nullable=False)
    op.create_unique_constraint(
        "uq_audiences_office_id_number",
        "audiences",
        ["office_id", "number"],
    )

    op.execute(
        """
        SELECT setval(
            pg_get_serial_sequence('audiences', 'id'),
            COALESCE((SELECT MAX(id) FROM audiences), 1),
            (SELECT COUNT(*) > 0 FROM audiences)
        )
        """
    )


def downgrade() -> None:
    op.drop_constraint("uq_audiences_office_id_number", "audiences", type_="unique")
    op.drop_column("audiences", "number")
