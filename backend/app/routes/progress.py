"""API routes for user progress and spaced repetition."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.middleware.auth import get_current_user
from app.schemas.progress import (
    MasteredProblemSchema,
    ProblemProgressSchema,
    ProgressResponse,
    ShowAgainResponse,
    TodaySessionResponse,
)
from app.services.progress import (
    get_mastered_problems,
    get_todays_problems,
    get_user_progress_stats,
    mark_show_again,
)

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/today", response_model=TodaySessionResponse)
async def get_today(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get today's session: up to 2 review problems + 1 new problem.

    Returns problems due for review plus the next unsolved problem.
    """
    user_id = user["id"]

    review_problems, review_progress, new_problem = await get_todays_problems(
        db, user_id
    )

    # Get total mastered and solved counts
    stats = await get_user_progress_stats(db, user_id)

    # Build response with review problems
    review_list = []
    for problem, progress in zip(review_problems, review_progress):
        review_list.append(
            ProblemProgressSchema(
                id=problem.id,
                title=problem.title,
                slug=problem.slug,
                difficulty=problem.difficulty,
                pattern=problem.pattern,
                sequence_number=problem.sequence_number,
                times_solved=progress.times_solved,
                last_solved_at=progress.last_solved_at,
                next_review_date=progress.next_review_date,
                is_mastered=progress.is_mastered,
            )
        )

    # Build new problem response
    new_problem_schema = None
    if new_problem:
        new_problem_schema = ProblemProgressSchema(
            id=new_problem.id,
            title=new_problem.title,
            slug=new_problem.slug,
            difficulty=new_problem.difficulty,
            pattern=new_problem.pattern,
            sequence_number=new_problem.sequence_number,
            times_solved=0,
            last_solved_at=None,
            next_review_date=None,
            is_mastered=False,
        )

    return TodaySessionResponse(
        review_problems=review_list,
        new_problem=new_problem_schema,
        total_mastered=stats["mastered_count"],
        total_solved=stats["solved_count"],
    )


@router.get("/progress", response_model=ProgressResponse)
async def get_progress(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's overall progress across all Blind 75 problems.

    Returns counts, breakdowns by difficulty/pattern, and due for review count.
    """
    user_id = user["id"]

    stats = await get_user_progress_stats(db, user_id)

    return ProgressResponse(
        total_problems=stats["total_problems"],
        solved_count=stats["solved_count"],
        mastered_count=stats["mastered_count"],
        in_progress_count=stats["in_progress_count"],
        unsolved_count=stats["unsolved_count"],
        due_for_review=stats["due_for_review"],
        problems_by_difficulty=stats["problems_by_difficulty"],
        problems_by_pattern=stats["problems_by_pattern"],
    )


@router.get("/mastered", response_model=list[MasteredProblemSchema])
async def get_mastered(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of all mastered problems.

    Returns problems with mastery info, sorted by most recently solved.
    """
    user_id = user["id"]

    mastered = await get_mastered_problems(db, user_id)

    return [
        MasteredProblemSchema(
            id=problem.id,
            title=problem.title,
            slug=problem.slug,
            difficulty=problem.difficulty,
            pattern=problem.pattern,
            sequence_number=problem.sequence_number,
            times_solved=progress.times_solved,
            last_solved_at=progress.last_solved_at,
            show_again=progress.show_again,
        )
        for problem, progress in mastered
    ]


@router.post("/mastered/{problem_id}/show-again", response_model=ShowAgainResponse)
async def show_again(
    problem_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Re-add a mastered problem to review rotation.

    Sets the problem to be reviewed again starting today.
    """
    user_id = user["id"]

    try:
        await mark_show_again(db, user_id, problem_id)
        await db.commit()
        return ShowAgainResponse(success=True, message="Problem re-added to rotation")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
