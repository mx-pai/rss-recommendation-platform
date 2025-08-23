"""enable ON DELETE CASCADE for articles.source_id

Revision ID: a79bcd899b20
Revises: ed09c9a9060d
Create Date: 2025-08-20 23:02:20.543420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a79bcd899b20'
down_revision: Union[str, Sequence[str], None] = 'ed09c9a9060d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 删除旧外键（名称通常是这个）
    op.drop_constraint('articles_source_id_fkey', 'articles', type_='foreignkey')
    # 创建新外键，带 ON DELETE CASCADE
    op.create_foreign_key(
        'articles_source_id_fkey',
        source_table='articles',
        referent_table='content_sources',
        local_cols=['source_id'],
        remote_cols=['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
     # 回滚：去掉级联，恢复普通外键
    op.drop_constraint('articles_source_id_fkey', 'articles', type_='foreignkey')
    op.create_foreign_key(
        'articles_source_id_fkey',
        source_table='articles',
        referent_table='content_sources',
        local_cols=['source_id'],
        remote_cols=['id']
        )
