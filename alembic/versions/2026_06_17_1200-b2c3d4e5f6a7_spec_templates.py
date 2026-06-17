"""spec templates

Revision ID: b2c3d4e5f6a7
Revises: f1b2c3d4e5a6
Create Date: 2026-06-17 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "f1b2c3d4e5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "spec_templates",
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("hardware_type", sa.String(length=32), nullable=False),
        sa.Column(
            "specs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_spec_templates_hardware_type"),
        "spec_templates",
        ["hardware_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_spec_templates_hardware_type"),
        table_name="spec_templates",
    )
    op.drop_table("spec_templates")
