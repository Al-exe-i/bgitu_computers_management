"""telegram subscriptions

Revision ID: 1d3b9e4c2a7f
Revises: f3b08eadf01a
Create Date: 2026-04-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1d3b9e4c2a7f"
down_revision: Union[str, Sequence[str], None] = "f3b08eadf01a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telegram_subscriptions",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column(
            "delivery_mode",
            sa.String(length=32),
            server_default="immediate",
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_telegram_subscriptions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_telegram_subscriptions")),
        sa.UniqueConstraint(
            "user_id",
            "scope_type",
            "scope_id",
            "event_type",
            name=op.f("uq_telegram_subscriptions_user_id_scope_type"),
        ),
    )
    op.create_index(
        op.f("ix_telegram_subscriptions_user_id"),
        "telegram_subscriptions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_telegram_subscriptions_user_id"),
        table_name="telegram_subscriptions",
    )
    op.drop_table("telegram_subscriptions")
