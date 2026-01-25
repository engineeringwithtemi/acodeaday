"""add_comparison_strategy_to_problems

Revision ID: 83cf51042617
Revises: b7c09ca0d8a9
Create Date: 2026-01-21 22:23:03.463579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83cf51042617'
down_revision: Union[str, Sequence[str], None] = 'b7c09ca0d8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add comparison_strategy column to problems table."""
    op.add_column(
        'problems',
        sa.Column('comparison_strategy', sa.String(50), nullable=True)
    )


def downgrade() -> None:
    """Remove comparison_strategy column from problems table."""
    op.drop_column('problems', 'comparison_strategy')
