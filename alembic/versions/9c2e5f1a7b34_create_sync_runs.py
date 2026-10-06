"""create sync_runs

Revision ID: 9c2e5f1a7b34
Revises: f3a2b8c1d4e7
Create Date: 2026-10-06 12:00:00.000000

sync_mappings only knows how the last run went. This keeps every run for a
while, so the admin page can chart success rate, run time and work done.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c2e5f1a7b34'
down_revision: Union[str, Sequence[str], None] = 'f3a2b8c1d4e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'sync_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('mapping_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('created', sa.Integer(), server_default='0', nullable=False),
        sa.Column('updated', sa.Integer(), server_default='0', nullable=False),
        sa.Column('deleted', sa.Integer(), server_default='0', nullable=False),
        sa.Column('pulled', sa.Integer(), server_default='0', nullable=False),
        sa.Column('imported', sa.Integer(), server_default='0', nullable=False),
        sa.Column('trashed', sa.Integer(), server_default='0', nullable=False),
        sa.Column(
            'row_created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mapping_id'], ['sync_mappings.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sync_runs_run_id'), 'sync_runs', ['run_id'], unique=False)
    op.create_index(op.f('ix_sync_runs_user_id'), 'sync_runs', ['user_id'], unique=False)
    op.create_index(op.f('ix_sync_runs_mapping_id'), 'sync_runs', ['mapping_id'], unique=False)
    op.create_index(op.f('ix_sync_runs_started_at'), 'sync_runs', ['started_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_sync_runs_started_at'), table_name='sync_runs')
    op.drop_index(op.f('ix_sync_runs_mapping_id'), table_name='sync_runs')
    op.drop_index(op.f('ix_sync_runs_user_id'), table_name='sync_runs')
    op.drop_index(op.f('ix_sync_runs_run_id'), table_name='sync_runs')
    op.drop_table('sync_runs')
