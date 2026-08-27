"""enforce case-insensitive user email uniqueness

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2026-08-27 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d5e6f7a8b9c0"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT lower(btrim(email))
                    FROM users
                    GROUP BY lower(btrim(email))
                    HAVING count(*) > 1
                ) THEN
                    RAISE EXCEPTION
                        'Duplicate user emails exist after case normalization';
                END IF;
            END
            $$
            """
        )
    )
    op.execute(sa.text("UPDATE users SET email = lower(btrim(email))"))
    op.drop_constraint(op.f("uq_users_email"), "users", type_="unique")
    op.create_index(
        "uq_users_email_ci",
        "users",
        [sa.text("lower(email)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_users_email_ci", table_name="users")
    op.create_unique_constraint(op.f("uq_users_email"), "users", ["email"])
