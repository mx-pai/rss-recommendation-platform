"""add keywords and category to articles

Revision ID: 17462152540a
Revises: e5ee6aabd6a7
Create Date: 2025-08-24 08:45:53.012838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17462152540a'
down_revision: Union[str, Sequence[str], None] = 'a79bcd899b20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加新字段，去掉comment避免问题
    op.add_column('articles', sa.Column('keywords', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('category', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # 删除字段
    op.drop_column('articles', 'category')
    op.drop_column('articles', 'keywords')
