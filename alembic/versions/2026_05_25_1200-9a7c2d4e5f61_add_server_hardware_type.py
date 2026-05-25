"""add server hardware type

Revision ID: 9a7c2d4e5f61
Revises: 4e8f1b2c9d3a
Create Date: 2026-05-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "9a7c2d4e5f61"
down_revision: Union[str, Sequence[str], None] = "4e8f1b2c9d3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE hardwaretype ADD VALUE IF NOT EXISTS 'server'")


def downgrade() -> None:
    # PostgreSQL does not support dropping enum values safely without rebuilding
    # dependent columns, so downgrade is intentionally left as a no-op.
    pass
