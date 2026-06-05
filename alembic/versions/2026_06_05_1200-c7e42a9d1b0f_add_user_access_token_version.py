"""add user access token version

Revision ID: c7e42a9d1b0f
Revises: a82c1f4d9b31
Create Date: 2026-06-05 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c7e42a9d1b0f"
down_revision: str | Sequence[str] | None = "a82c1f4d9b31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "access_token_version",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "access_token_version")
