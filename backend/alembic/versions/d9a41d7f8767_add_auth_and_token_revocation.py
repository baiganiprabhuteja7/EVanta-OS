"""add_auth_and_token_revocation

Revision ID: d9a41d7f8767
Revises: 3c3981e9cb1d
Create Date: 2026-10-24 21:30:47.922450

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9a41d7f8767'
down_revision: Union[str, Sequence[str], None] = '3c3981e9cb1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add auth improvements and token revocation table."""
    # 1. Add username, failed_login_attempts, and locked_until to users
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c['name'] for c in insp.get_columns('users')]

    if 'username' not in columns:
        op.add_column('users', sa.Column('username', sa.String(length=100), nullable=True))
        op.create_index('ix_users_username', 'users', ['username'], unique=True)

    if 'failed_login_attempts' not in columns:
        op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False))

    if 'locked_until' not in columns:
        op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))

    # 2. Create revoked_tokens table if not exists
    if 'revoked_tokens' not in insp.get_table_names():
        op.create_table(
            'revoked_tokens',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('jti', sa.String(length=100), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_revoked_tokens_id', 'revoked_tokens', ['id'], unique=False)
        op.create_index('ix_revoked_tokens_jti', 'revoked_tokens', ['jti'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_revoked_tokens_jti', table_name='revoked_tokens')
    op.drop_index('ix_revoked_tokens_id', table_name='revoked_tokens')
    op.drop_table('revoked_tokens')

    op.drop_index('ix_users_username', table_name='users')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'username')
