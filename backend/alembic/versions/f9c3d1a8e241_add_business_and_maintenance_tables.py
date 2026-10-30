"""add business and maintenance tables and columns

Revision ID: f9c3d1a8e241
Revises: e8b2a5c31f49
Create Date: 2026-10-30 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'f9c3d1a8e241'
down_revision = 'e8b2a5c31f49'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = Inspector.from_engine(conn)

    station_cols = [c['name'] for c in insp.get_columns('stations')]
    if 'initial_investment' not in station_cols:
        op.add_column('stations', sa.Column('initial_investment', sa.Numeric(precision=12, scale=2), server_default='2500000.0', nullable=False))
    if 'monthly_fixed_cost' not in station_cols:
        op.add_column('stations', sa.Column('monthly_fixed_cost', sa.Numeric(precision=10, scale=2), server_default='18000.0', nullable=False))

    charger_cols = [c['name'] for c in insp.get_columns('chargers')]
    if 'location_name' not in charger_cols:
        op.add_column('chargers', sa.Column('location_name', sa.String(length=100), server_default='Main Charging Canopy', nullable=False))

    tables = insp.get_table_names()
    if 'station_expenses' not in tables:
        op.create_table(
            'station_expenses',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('station_id', sa.Integer(), nullable=False),
            sa.Column('expense_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('recorded_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_station_expenses_id'), 'station_expenses', ['id'], unique=False)
        op.create_index(op.f('ix_station_expenses_station_id'), 'station_expenses', ['station_id'], unique=False)
        op.create_index(op.f('ix_station_expenses_expense_date'), 'station_expenses', ['expense_date'], unique=False)

    if 'maintenance_records' not in tables:
        op.create_table(
            'maintenance_records',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('station_id', sa.Integer(), nullable=False),
            sa.Column('charger_id', sa.Integer(), nullable=True),
            sa.Column('equipment_name', sa.String(length=100), nullable=False),
            sa.Column('issue_description', sa.Text(), nullable=False),
            sa.Column('severity', sa.String(length=20), server_default='Medium', nullable=False),
            sa.Column('status', sa.String(length=30), server_default='Reported', nullable=False),
            sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('cost', sa.Numeric(precision=10, scale=2), server_default='0.0', nullable=False),
            sa.Column('technician_name', sa.String(length=100), nullable=True),
            sa.Column('resolution_notes', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['charger_id'], ['chargers.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_maintenance_records_id'), 'maintenance_records', ['id'], unique=False)
        op.create_index(op.f('ix_maintenance_records_station_id'), 'maintenance_records', ['station_id'], unique=False)
        op.create_index(op.f('ix_maintenance_records_charger_id'), 'maintenance_records', ['charger_id'], unique=False)


def downgrade():
    op.drop_column('chargers', 'location_name')
    op.drop_column('stations', 'monthly_fixed_cost')
    op.drop_column('stations', 'initial_investment')
