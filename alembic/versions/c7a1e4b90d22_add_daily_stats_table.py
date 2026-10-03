"""add daily_stats table

Revision ID: c7a1e4b90d22
Revises: 843301e6e7b4
Create Date: 2026-10-03 11:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c7a1e4b90d22'
down_revision: Union[str, Sequence[str], None] = '843301e6e7b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'daily_stats',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('done', sa.Integer(), nullable=False),
        sa.Column('not_done', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('daily_stats')
