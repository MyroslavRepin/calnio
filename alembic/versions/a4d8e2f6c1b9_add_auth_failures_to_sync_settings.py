"""add auth_failures to sync_settings

Revision ID: a4d8e2f6c1b9
Revises: 9c2e5f1a7b34
Create Date: 2026-10-11 12:00:00.000000

iCloud has answered 401 to a password that worked fifteen minutes earlier.
Syncing now turns off after three rejected runs in a row instead of the first,
and this column counts them.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4d8e2f6c1b9'
down_revision: Union[str, Sequence[str], None] = '9c2e5f1a7b34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'sync_settings',
        sa.Column('auth_failures', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sync_settings', 'auth_failures')
