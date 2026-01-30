"""add_leetcode_no_to_problems

Revision ID: 6a770aa2ed1b
Revises: 83cf51042617
Create Date: 2026-01-25 11:26:48.071496

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a770aa2ed1b'
down_revision: Union[str, Sequence[str], None] = '83cf51042617'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('problems', sa.Column('leetcode_no', sa.Integer(), nullable=True))
    op.create_index('ix_problems_leetcode_no', 'problems', ['leetcode_no'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_problems_leetcode_no', 'problems')
    op.drop_column('problems', 'leetcode_no')
