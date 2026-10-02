"""add stopped_cleanly to system_settings

Revision ID: b3e8f1a6c2d9
Revises: f3a2b8c1d4e7
Create Date: 2026-10-02 12:00:00.000000

Docker restarts a crashed container without a word. This flag lets the next
startup say whether the previous process stopped on purpose or died.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3e8f1a6c2d9'
down_revision: Union[str, Sequence[str], None] = 'f3a2b8c1d4e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'system_settings',
        sa.Column('stopped_cleanly', sa.Boolean(), nullable=False, server_default='true'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('system_settings', 'stopped_cleanly')
