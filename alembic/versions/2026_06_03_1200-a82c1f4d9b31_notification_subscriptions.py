"""notification subscriptions

Revision ID: a82c1f4d9b31
Revises: 9a7c2d4e5f61
Create Date: 2026-06-03 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a82c1f4d9b31"
down_revision: str | Sequence[str] | None = "9a7c2d4e5f61"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_subscriptions",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "scope_type", "scope_id", "event_type"),
    )
    op.create_index(
        op.f("ix_notification_subscriptions_user_id"),
        "notification_subscriptions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_subscriptions_event_scope",
        "notification_subscriptions",
        ["event_type", "scope_type", "scope_id", "enabled"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_subscriptions_event_scope",
        table_name="notification_subscriptions",
    )
    op.drop_index(
        op.f("ix_notification_subscriptions_user_id"),
        table_name="notification_subscriptions",
    )
    op.drop_table("notification_subscriptions")
