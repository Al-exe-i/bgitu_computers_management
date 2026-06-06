"""remove telegram integration

Revision ID: f1b2c3d4e5a6
Revises: e5a7b8c9d0f1
Create Date: 2026-06-06 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f1b2c3d4e5a6"
down_revision: Union[str, Sequence[str], None] = "e5a7b8c9d0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("telegram_notification_delivery_logs")
    op.drop_table("telegram_subscriptions")
    op.drop_table("telegram_link_tokens")

    op.drop_constraint(op.f("uq_users_telegram_id"), "users", type_="unique")
    op.drop_column("users", "telegram_id_confirmed")
    op.drop_column("users", "telegram_id")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "telegram_id_confirmed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.create_unique_constraint(op.f("uq_users_telegram_id"), "users", ["telegram_id"])

    op.create_table(
        "telegram_link_tokens",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
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
            name=op.f("fk_telegram_link_tokens_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_telegram_link_tokens")),
        sa.UniqueConstraint(
            "token_hash",
            name=op.f("uq_telegram_link_tokens_token_hash"),
        ),
    )
    op.create_index(
        op.f("ix_telegram_link_tokens_user_id"),
        "telegram_link_tokens",
        ["user_id"],
        unique=False,
    )

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

    op.create_table(
        "telegram_notification_delivery_logs",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notification_id", sa.String(length=32), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("error_type", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_telegram_notification_delivery_logs"),
        ),
    )
    op.create_index(
        op.f("ix_telegram_notification_delivery_logs_created_at"),
        "telegram_notification_delivery_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telegram_notification_delivery_logs_delivered_at"),
        "telegram_notification_delivery_logs",
        ["delivered_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telegram_notification_delivery_logs_event_type"),
        "telegram_notification_delivery_logs",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telegram_notification_delivery_logs_notification_id"),
        "telegram_notification_delivery_logs",
        ["notification_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telegram_notification_delivery_logs_status"),
        "telegram_notification_delivery_logs",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telegram_notification_delivery_logs_telegram_id"),
        "telegram_notification_delivery_logs",
        ["telegram_id"],
        unique=False,
    )
