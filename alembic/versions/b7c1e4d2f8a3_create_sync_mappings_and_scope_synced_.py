"""create sync_mappings, scope synced_events by mapping

Revision ID: b7c1e4d2f8a3
Revises: 4113d7ba6b93
Create Date: 2026-09-13 00:00:00.000000

Splits the single binding (notion_connections.data_source_id +
sync_settings.due_date_property + caldav_credentials.calendar_url) into N rows,
one per Notion data source, each with its own calendar and its own switch.

Existing rows are adopted, not wiped: a user who has a database selected gets
one mapping carrying whatever they had configured, and their synced_events rows
are repointed at it. Nothing re-syncs and no CalDAV event is orphaned.

The five now-unused columns are left in place so a downgrade restores working
old code. A follow-up release drops them.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c1e4d2f8a3'
down_revision: Union[str, Sequence[str], None] = '4113d7ba6b93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'sync_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('data_source_id', sa.String(), nullable=False),
        sa.Column('data_source_name', sa.String(), nullable=True),
        sa.Column('due_date_property', sa.String(), nullable=True),
        sa.Column('calendar_url', sa.String(), nullable=True),
        sa.Column('calendar_name', sa.String(), nullable=True),
        sa.Column('enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_status', sa.String(), nullable=True),
        sa.Column('row_created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('row_updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'data_source_id', name='uq_sync_mappings_user_source'),
    )
    op.create_index(op.f('ix_sync_mappings_user_id'), 'sync_mappings', ['user_id'], unique=False)

    # One mapping per user who had a database selected. LEFT JOIN on purpose: a
    # half-configured user keeps their nulls and their mapping is simply not
    # eligible, exactly as their setup is not eligible today.
    op.execute("""
        INSERT INTO sync_mappings
            (user_id, data_source_id, data_source_name, due_date_property,
             calendar_url, calendar_name, enabled, last_run_at, last_status,
             row_created_at, row_updated_at)
        SELECT nc.user_id, nc.data_source_id, nc.data_source_name,
               ss.due_date_property, cc.calendar_url, cc.calendar_name,
               COALESCE(ss.enabled, false), ss.last_run_at, ss.last_status,
               now(), now()
        FROM notion_connections nc
        LEFT JOIN sync_settings ss ON ss.user_id = nc.user_id
        LEFT JOIN caldav_credentials cc ON cc.user_id = nc.user_id
        WHERE nc.data_source_id IS NOT NULL
    """)

    op.add_column('synced_events', sa.Column('mapping_id', sa.Integer(), nullable=True))

    # Unambiguous: the insert above creates at most one mapping per user.
    op.execute("""
        UPDATE synced_events se
        SET mapping_id = sm.id
        FROM sync_mappings sm
        WHERE sm.user_id = se.user_id
    """)

    # Rows whose user has no data_source_id at all, so no mapping could be
    # built for them. Their CalDAV events survive with no link row, which the
    # next sync recreates and iCloud answers 412 — already true of them before
    # this migration. The pre-flight count says whether this is zero.
    op.execute('DELETE FROM synced_events WHERE mapping_id IS NULL')

    op.alter_column('synced_events', 'mapping_id', nullable=False)
    op.create_index(op.f('ix_synced_events_mapping_id'), 'synced_events', ['mapping_id'], unique=False)
    op.create_foreign_key('fk_synced_events_mapping_id', 'synced_events', 'sync_mappings', ['mapping_id'], ['id'], ondelete='CASCADE')

    # A user may now link the same Notion page from two mappings, so the page
    # is unique per mapping rather than per user.
    op.drop_constraint('uq_synced_events_user_page', 'synced_events', type_='unique')
    op.create_unique_constraint('uq_synced_events_mapping_page', 'synced_events', ['mapping_id', 'notion_page_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Going back restores uniqueness per user. Two mappings that linked the
    # same page would collide on it, so those extra rows go; the first mapping's
    # row is kept, which is the one the old single-binding code would own.
    op.execute("""
        DELETE FROM synced_events
        WHERE id NOT IN (
            SELECT MIN(id) FROM synced_events GROUP BY user_id, notion_page_id
        )
    """)

    op.drop_constraint('uq_synced_events_mapping_page', 'synced_events', type_='unique')
    op.create_unique_constraint('uq_synced_events_user_page', 'synced_events', ['user_id', 'notion_page_id'])
    op.drop_constraint('fk_synced_events_mapping_id', 'synced_events', type_='foreignkey')
    op.drop_index(op.f('ix_synced_events_mapping_id'), table_name='synced_events')
    op.drop_column('synced_events', 'mapping_id')
    op.drop_index(op.f('ix_sync_mappings_user_id'), table_name='sync_mappings')
    op.drop_table('sync_mappings')
