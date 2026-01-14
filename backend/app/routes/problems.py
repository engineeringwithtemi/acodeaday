"""API routes for problems."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.connection import get_db
from app.db.tables import Problem, UserCode, UserProgress
from app.middleware.auth import get_current_user
from app.schemas.problem import ProblemDetailSchema, ProblemSchema

router = APIRouter(prefix="/api/problems", tags=["problems"])


@router.get("/", response_model=list[ProblemSchema])
async def get_problems(db: AsyncSession = Depends(get_db)):
    """
    Get list of all problems ordered by sequence number.

    Returns basic problem info without test cases or language details.
    """
    result = await db.execute(select(Problem).order_by(Problem.sequence_number))
    problems = result.scalars().all()
    return problems


@router.get("/{slug}", response_model=ProblemDetailSchema)
async def get_problem(
    slug: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed problem information including test cases and language configs.

    Returns first 3 test cases by sequence order.
    Also returns user's saved code if it exists.
    """
    user_id = user["id"]

    result = await db.execute(
        select(Problem)
        .options(joinedload(Problem.languages), joinedload(Problem.test_cases))
        .where(Problem.slug == slug)
    )
    problem = result.unique().scalar_one_or_none()

    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{slug}' not found")

    # Get first 3 test cases by sequence order
    sorted_test_cases = sorted(problem.test_cases, key=lambda tc: tc.sequence)
    first_three_test_cases = sorted_test_cases[:3]

    # Check if problem is due for review
    progress_result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user_id,
            UserProgress.problem_id == problem.id,
        )
    )
    progress = progress_result.scalar_one_or_none()

    # Problem is "due" if user has progress AND not mastered AND next_review_date <= today
    today = datetime.now(UTC).date()
    is_due_for_review = False
    if progress and not progress.is_mastered:
        if progress.next_review_date and progress.next_review_date <= today:
            is_due_for_review = True

    # Query user's saved code for this problem (always return it, frontend decides display)
    user_code_result = await db.execute(
        select(UserCode).where(
            UserCode.user_id == user_id,
            UserCode.problem_id == problem.id,
            UserCode.language == "python",  # Default to python for now
        )
    )
    user_code_record = user_code_result.scalar_one_or_none()
    saved_code = user_code_record.code if user_code_record else None

    return ProblemDetailSchema(
        id=problem.id,
        title=problem.title,
        slug=problem.slug,
        description=problem.description,
        difficulty=problem.difficulty,
        pattern=problem.pattern,
        sequence_number=problem.sequence_number,
        constraints=problem.constraints,
        examples=problem.examples,
        created_at=problem.created_at,
        languages=problem.languages,
        test_cases=first_three_test_cases,
        user_code=saved_code,
        is_due=is_due_for_review,
    )
