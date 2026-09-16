"""add last_error and last_run_id to sync_mappings

Revision ID: f3a2b8c1d4e7
Revises: e5d1a7c93f42
Create Date: 2026-09-16 00:40:00.000000

"Last run failed" is not an answer anybody can act on. The reason is kept
beside the status, and the run id beside it, so the log line with the full
traceback can be found by grepping for that id.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a2b8c1d4e7'
down_revision: Union[str, Sequence[str], None] = 'e5d1a7c93f42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('sync_mappings', sa.Column('last_error', sa.String(), nullable=True))
    op.add_column('sync_mappings', sa.Column('last_run_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sync_mappings', 'last_run_id')
    op.drop_column('sync_mappings', 'last_error')
