"""Сведения о корпусах и этажах.

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
"""

import sqlalchemy as sa

from alembic import op

revision = "b9c0d1e2f3a4"
down_revision = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("offices", "floor_plans"):
        op.add_column(table, sa.Column("name", sa.String(120), nullable=True))
        op.add_column(table, sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "offices", sa.Column("internet_provider", sa.String(120), nullable=True)
    )


def downgrade():
    op.drop_column("offices", "internet_provider")
    for table in ("floor_plans", "offices"):
        op.drop_column(table, "description")
        op.drop_column(table, "name")
