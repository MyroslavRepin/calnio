"""two-way sync: write-back switches, calendar cursor, merge baseline

Revision ID: c4f7a91b2d60
Revises: b7c1e4d2f8a3
Create Date: 2026-09-15 12:00:00.000000

synced_events stops being a pure link index and starts holding the state both
sides last agreed on, which is what tells a Notion edit apart from a calendar
edit. Existing rows have no baseline: start_at stays NULL, and the first run
after this migration fills it in from Notion rather than reading a calendar
event as something the user just changed.

etag and notion_last_edited go: neither was ever read, and content comparison
replaces what the timestamp was meant to do.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4f7a91b2d60'
down_revision: Union[str, Sequence[str], None] = 'b7c1e4d2f8a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'sync_mappings',
        sa.Column(
            'write_back',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        'sync_mappings',
        sa.Column('write_back_since', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'sync_mappings',
        sa.Column('caldav_sync_token', sa.String(), nullable=True),
    )

    # Every grant that exists today was consented to when Calnio only asked to
    # read, so none of them may write until the user connects again.
    op.add_column(
        'notion_connections',
        sa.Column(
            'can_write',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        'synced_events',
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'synced_events',
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'synced_events',
        sa.Column(
            'all_day',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.drop_column('synced_events', 'etag')
    op.drop_column('synced_events', 'notion_last_edited')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'synced_events',
        sa.Column('notion_last_edited', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column('synced_events', sa.Column('etag', sa.String(), nullable=True))
    op.drop_column('synced_events', 'all_day')
    op.drop_column('synced_events', 'end_at')
    op.drop_column('synced_events', 'start_at')

    op.drop_column('notion_connections', 'can_write')

    op.drop_column('sync_mappings', 'caldav_sync_token')
    op.drop_column('sync_mappings', 'write_back_since')
    op.drop_column('sync_mappings', 'write_back')
