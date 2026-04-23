"""telegram notification delivery logs

Revision ID: 6c55f937e4ab
Revises: 8b8b0a1a6f3f
Create Date: 2026-04-23 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "6c55f937e4ab"
down_revision: Union[str, Sequence[str], None] = "8b8b0a1a6f3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index(
        op.f("ix_telegram_notification_delivery_logs_telegram_id"),
        table_name="telegram_notification_delivery_logs",
    )
    op.drop_index(
        op.f("ix_telegram_notification_delivery_logs_status"),
        table_name="telegram_notification_delivery_logs",
    )
    op.drop_index(
        op.f("ix_telegram_notification_delivery_logs_notification_id"),
        table_name="telegram_notification_delivery_logs",
    )
    op.drop_index(
        op.f("ix_telegram_notification_delivery_logs_event_type"),
        table_name="telegram_notification_delivery_logs",
    )
    op.drop_index(
        op.f("ix_telegram_notification_delivery_logs_delivered_at"),
        table_name="telegram_notification_delivery_logs",
    )
    op.drop_index(
        op.f("ix_telegram_notification_delivery_logs_created_at"),
        table_name="telegram_notification_delivery_logs",
    )
    op.drop_table("telegram_notification_delivery_logs")
