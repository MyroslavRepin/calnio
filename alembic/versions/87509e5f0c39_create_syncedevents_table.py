"""Create SyncedEvents table

Revision ID: 87509e5f0c39
Revises: e208a4ca9752
Create Date: 2026-07-02 20:11:16.879417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87509e5f0c39'
down_revision: Union[str, Sequence[str], None] = 'e208a4ca9752'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('synced_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notion_page_id', sa.String(), nullable=False),
    sa.Column('caldav_href', sa.String(), nullable=False),
    sa.Column('caldav_uid', sa.String(), nullable=False),
    sa.Column('etag', sa.String(), nullable=True),
    sa.Column('notion_last_edited', sa.DateTime(timezone=True), nullable=True),
    sa.Column('row_created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('row_updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_synced_events_notion_page_id'), 'synced_events', ['notion_page_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_synced_events_notion_page_id'), table_name='synced_events')
    op.drop_table('synced_events')
