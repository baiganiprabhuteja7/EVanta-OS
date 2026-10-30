"""add station_layouts table

Revision ID: e8b2a5c31f49
Revises: d9a41d7f8767
Create Date: 2026-10-24 22:38:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e8b2a5c31f49'
down_revision = 'd9a41d7f8767'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'station_layouts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('scale_ratio', sa.Numeric(precision=10, scale=4), nullable=False, server_default='1.0'),
        sa.Column('scale_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('disclaimer', sa.String(length=255), nullable=False),
        sa.Column('layout_data', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_station_layouts_id'), 'station_layouts', ['id'], unique=False)
    op.create_index(op.f('ix_station_layouts_station_id'), 'station_layouts', ['station_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_station_layouts_station_id'), table_name='station_layouts')
    op.drop_index(op.f('ix_station_layouts_id'), table_name='station_layouts')
    op.drop_table('station_layouts')
