"""add memory_kb to submissions

Revision ID: 2bbd7badbd70
Revises: 40b1440b17d7
Create Date: 2026-01-10 16:18:28.290600

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bbd7badbd70'
down_revision: Union[str, Sequence[str], None] = '40b1440b17d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('submissions', sa.Column('memory_kb', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('submissions', 'memory_kb')
