"""change_pattern_to_array

Revision ID: b7c09ca0d8a9
Revises: 0731a45bfca5
Create Date: 2026-01-16 08:18:20.845525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, TEXT


# revision identifiers, used by Alembic.
revision: str = 'b7c09ca0d8a9'
down_revision: Union[str, Sequence[str], None] = '0731a45bfca5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change pattern column from VARCHAR(50) to TEXT[] array."""
    # First convert existing VARCHAR values to array format
    # Then alter the column type
    op.execute('''
        ALTER TABLE problems
        ALTER COLUMN pattern TYPE TEXT[]
        USING ARRAY[pattern]
    ''')


def downgrade() -> None:
    """Revert pattern column from TEXT[] back to VARCHAR(50)."""
    # Take first element of array when reverting
    op.execute('''
        ALTER TABLE problems
        ALTER COLUMN pattern TYPE VARCHAR(50)
        USING pattern[1]
    ''')
