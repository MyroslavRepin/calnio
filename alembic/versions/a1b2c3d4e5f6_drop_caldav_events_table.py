"""Drop caldav_events table

The caldav_events table / CalDavEventORM was never used: events live on iCloud
via CalDAV and sync state is tracked in synced_events. Drop the dead table.

Revision ID: a1b2c3d4e5f6
Revises: ec5668403e86
Create Date: 2026-07-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'ec5668403e86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the caldav_events table."""
    op.drop_index(op.f('ix_caldav_events_uid'), table_name='caldav_events')
    op.drop_table('caldav_events')


def downgrade() -> None:
    """Recreate the caldav_events table."""
    op.create_table('caldav_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uid', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('all_day', sa.Boolean(), nullable=False),
    sa.Column('calendar', sa.String(), nullable=False),
    sa.Column('href', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('row_created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('row_updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_caldav_events_uid'), 'caldav_events', ['uid'], unique=True)
