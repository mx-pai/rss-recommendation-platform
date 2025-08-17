"""add fetch fields to content sources

Revision ID: 2c80e2760970
Revises: 
Create Date: 2025-08-17 14:27:13.442816

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c80e2760970'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('content_sources', sa.Column('fetch_frequency', sa.Integer, nullable=True, server_default='60'))
    op.add_column('content_sources', sa.Column('fetch_config', sa.Text(), nullable=True))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('content_sources', 'fetch_frequency')
    op.drop_column('content_sources', 'fetch_config')
