"""per-user sync: sync_settings + synced_events.user_id

Revision ID: ed165f9f9302
Revises: 7db3fe5e6a7d
Create Date: 2026-07-28 21:45:19.270408

Run `services.sync.reset_all()` BEFORE this migration. Link rows written by
the old single-user loop have no user to attribute them to, so this drops
them — and rows dropped while their CalDAV events still exist become
un-owned events that the next sync recreates, which iCloud answers with a
412 duplicate. reset_all deletes the events too, and the first per-user run
rebuilds everything from Notion.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed165f9f9302'
down_revision: Union[str, Sequence[str], None] = '7db3fe5e6a7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'sync_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('due_date_property', sa.String(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_status', sa.String(), nullable=True),
        sa.Column('row_created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('row_updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sync_settings_user_id'), 'sync_settings', ['user_id'], unique=True)

    # Pre-per-user rows, ownerless by construction. See the module docstring:
    # their CalDAV events must already be gone.
    op.execute('DELETE FROM synced_events')

    op.add_column('synced_events', sa.Column('user_id', sa.Integer(), nullable=False))
    # notion_page_id is no longer globally unique — two users may link the same
    # shared Notion page into their own calendars.
    op.drop_index(op.f('ix_synced_events_notion_page_id'), table_name='synced_events')
    op.create_index(op.f('ix_synced_events_notion_page_id'), 'synced_events', ['notion_page_id'], unique=False)
    op.create_index(op.f('ix_synced_events_user_id'), 'synced_events', ['user_id'], unique=False)
    op.create_unique_constraint('uq_synced_events_user_page', 'synced_events', ['user_id', 'notion_page_id'])
    op.create_foreign_key('fk_synced_events_user_id', 'synced_events', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    # Going back restores a globally unique notion_page_id, which two users'
    # rows would collide on — so the table is emptied here too.
    op.execute('DELETE FROM synced_events')

    op.drop_constraint('fk_synced_events_user_id', 'synced_events', type_='foreignkey')
    op.drop_constraint('uq_synced_events_user_page', 'synced_events', type_='unique')
    op.drop_index(op.f('ix_synced_events_user_id'), table_name='synced_events')
    op.drop_index(op.f('ix_synced_events_notion_page_id'), table_name='synced_events')
    op.create_index(op.f('ix_synced_events_notion_page_id'), 'synced_events', ['notion_page_id'], unique=True)
    op.drop_column('synced_events', 'user_id')
    op.drop_index(op.f('ix_sync_settings_user_id'), table_name='sync_settings')
    op.drop_table('sync_settings')
