"""add import_jobs tables

Revision ID: a1b2c3d4e5f6
Revises: 6a770aa2ed1b
Create Date: 2026-01-30 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "6a770aa2ed1b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "queued", "processing", "completed", "failed", "cancelled",
                name="importjobstatus",
            ),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=True),
        sa.Column("total", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_import_jobs_user_id", "import_jobs", ["user_id"])
    op.create_index("ix_import_jobs_status", "import_jobs", ["status"])

    op.create_table(
        "import_job_problems",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "import_job_id",
            UUID(as_uuid=True),
            sa.ForeignKey("import_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "problem_id",
            UUID(as_uuid=True),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_import_job_problems_job_id", "import_job_problems", ["import_job_id"]
    )
    op.create_index(
        "ix_import_job_problems_problem_id", "import_job_problems", ["problem_id"]
    )
    op.create_index(
        "ix_import_job_problems_unique",
        "import_job_problems",
        ["import_job_id", "problem_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("import_job_problems")
    op.drop_table("import_jobs")
    op.execute("DROP TYPE IF EXISTS importjobstatus")
