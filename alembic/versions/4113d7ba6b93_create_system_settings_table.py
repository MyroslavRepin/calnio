"""create system_settings table

Revision ID: 4113d7ba6b93
Revises: 0703ca8b02e9
Create Date: 2026-08-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4113d7ba6b93'
down_revision: Union[str, Sequence[str], None] = '0703ca8b02e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('maintenance_mode', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('maintenance_message', sa.String(), nullable=True),
        sa.Column('row_created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('row_updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('system_settings')
