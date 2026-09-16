"""Удаление пригласительных ссылок. Откат восстанавливает только пустую таблицу.

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = 'c0d1e2f3a4b5'
down_revision = 'b9c0d1e2f3a4'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('invite_links')


def downgrade():
    op.create_table(
        'invite_links',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('token_hash', sa.String(128), nullable=False, unique=True),
        sa.Column('target_email', sa.String(255)),
        sa.Column('target_role', postgresql.ENUM('admin', 'teacher', name='user_role', create_type=False),
                  nullable=False, server_default='teacher'),
        sa.Column('note', sa.String(255)),
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('used_by_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True)),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
    )
