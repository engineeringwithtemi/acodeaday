"""add comparison to test_cases

Revision ID: 9c1a4b3a2f5e
Revises: b7c09ca0d8a9
Create Date: 2026-01-10 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c1a4b3a2f5e'
down_revision: Union[str, Sequence[str], None] = 'b7c09ca0d8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('test_cases', sa.Column('comparison', sa.String(length=32), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('test_cases', 'comparison')
