"""add is_admin to users

Revision ID: e5d1a7c93f42
Revises: c4f7a91b2d60
Create Date: 2026-09-16 00:20:00.000000

Nobody is an admin until a row is changed by hand. There is no route that
grants it, on purpose.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5d1a7c93f42'
down_revision: Union[str, Sequence[str], None] = 'c4f7a91b2d60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column(
            'is_admin',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'is_admin')
