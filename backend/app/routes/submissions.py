"""API routes for submission history."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.connection import get_db
from app.middleware.auth import get_current_user
from app.db.tables import Submission, Problem
from app.schemas.progress import SubmissionSchema

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.get("/{problem_id}", response_model=list[SubmissionSchema])
async def get_submissions(
    problem_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get submission history for a specific problem.

    Returns all submissions by the user for this problem, ordered by most recent first.
    """
    user_id = user["id"]

    result = await db.execute(
        select(Submission, Problem)
        .join(Problem, Submission.problem_id == Problem.id)
        .where(Submission.user_id == user_id)
        .where(Submission.problem_id == problem_id)
        .order_by(Submission.submitted_at.desc())
    )
    submissions_data = result.all()

    return [
        SubmissionSchema(
            id=submission.id,
            problem_id=submission.problem_id,
            problem_title=problem.title,
            code=submission.code,
            language=submission.language.value,
            passed=submission.passed,
            runtime_ms=submission.runtime_ms,
            submitted_at=submission.submitted_at,
        )
        for submission, problem in submissions_data
    ]
