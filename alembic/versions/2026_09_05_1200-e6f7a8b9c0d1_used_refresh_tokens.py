"""Remember consumed refresh hashes until their session is deleted."""

import sqlalchemy as sa

from alembic import op

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "used_refresh_tokens",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("user_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_index("ix_used_refresh_tokens_session_id", "used_refresh_tokens", ["session_id"])


def downgrade() -> None:
    op.drop_table("used_refresh_tokens")
