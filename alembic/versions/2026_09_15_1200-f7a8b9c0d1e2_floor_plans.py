"""Add room types and editable floor plans."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "audiences",
        sa.Column(
            "room_type", sa.String(20), nullable=False, server_default="educational"
        ),
    )
    op.create_check_constraint(
        "audience_room_type",
        "audiences",
        "room_type IN ('educational', 'administrative')",
    )
    op.create_table(
        "floor_plans",
        sa.Column(
            "office_id",
            sa.Integer(),
            sa.ForeignKey("offices.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("floor", sa.Integer(), primary_key=True),
        sa.Column("width", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("positions", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.CheckConstraint(
            "width BETWEEN 1 AND 50 AND height BETWEEN 1 AND 50",
            name="ck_floor_plan_dimensions",
        ),
        sa.CheckConstraint("revision >= 0", name="ck_floor_plan_revision"),
    )


def downgrade() -> None:
    op.drop_table("floor_plans")
    op.drop_constraint("audience_room_type", "audiences", type_="check")
    op.drop_column("audiences", "room_type")
