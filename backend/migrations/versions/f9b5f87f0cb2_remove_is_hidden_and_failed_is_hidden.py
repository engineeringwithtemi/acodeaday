"""remove_is_hidden_and_failed_is_hidden

Revision ID: f9b5f87f0cb2
Revises: 036ec3217785
Create Date: 2026-01-15 21:34:53.759840

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f9b5f87f0cb2'
down_revision: str | Sequence[str] | None = '036ec3217785'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove is_hidden column from test_cases table."""
    op.drop_column('test_cases', 'is_hidden')


def downgrade() -> None:
    """Add is_hidden column back to test_cases table."""
    op.add_column('test_cases', sa.Column('is_hidden', sa.Boolean(), nullable=False, server_default='false'))
    op.execute("ALTER TABLE test_cases ALTER COLUMN is_hidden DROP DEFAULT")
