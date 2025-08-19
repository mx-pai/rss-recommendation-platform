"""add images summary word_count to articles

Revision ID: ed09c9a9060d
Revises: 3b3e04fc0860
Create Date: 2025-08-17 23:13:17.885379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed09c9a9060d'
down_revision: Union[str, Sequence[str], None] = '3b3e04fc0860'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('articles', sa.Column('images', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('word_count', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('articles', 'word_count')
    op.drop_column('articles', 'summary')
    op.drop_column('articles', 'images')
