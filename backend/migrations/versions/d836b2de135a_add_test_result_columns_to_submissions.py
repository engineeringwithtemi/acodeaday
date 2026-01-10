"""add_test_result_columns_to_submissions

Revision ID: d836b2de135a
Revises: fb7f174fb2a3
Create Date: 2026-01-10 19:09:57.635757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'd836b2de135a'
down_revision: Union[str, Sequence[str], None] = 'fb7f174fb2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Test result summary columns
    op.add_column('submissions', sa.Column('total_test_cases', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('submissions', sa.Column('passed_count', sa.Integer(), nullable=False, server_default='0'))

    # First failed test details (NULL if all passed)
    op.add_column('submissions', sa.Column('failed_test_number', sa.Integer(), nullable=True))
    op.add_column('submissions', sa.Column('failed_input', JSONB(), nullable=True))
    op.add_column('submissions', sa.Column('failed_output', JSONB(), nullable=True))
    op.add_column('submissions', sa.Column('failed_expected', JSONB(), nullable=True))
    op.add_column('submissions', sa.Column('failed_is_hidden', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('submissions', 'failed_is_hidden')
    op.drop_column('submissions', 'failed_expected')
    op.drop_column('submissions', 'failed_output')
    op.drop_column('submissions', 'failed_input')
    op.drop_column('submissions', 'failed_test_number')
    op.drop_column('submissions', 'passed_count')
    op.drop_column('submissions', 'total_test_cases')
