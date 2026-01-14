"""API routes for user progress and spaced repetition."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.middleware.auth import get_current_user
from app.schemas.progress import (
    MasteredProblemSchema,
    MasteredProblemsResponse,
    ProblemBasicSchema,
    ProblemProgressSchema,
    ProblemWithProgressSchema,
    ProgressResponse,
    ShowAgainResponse,
    SubmissionBasicSchema,
    TodaySessionResponse,
    UserProgressBasicSchema,
)
from app.services.progress import (
    get_all_problems_with_progress,
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

    Returns all problems with user progress, plus summary counts.
    """
    user_id = user["id"]

    # Get all problems with progress
    problems_with_progress = await get_all_problems_with_progress(db, user_id)

    # Build problem list with nested structure
    problems_list = []
    completed_count = 0
    mastered_count = 0

    for problem, progress in problems_with_progress:
        problem_schema = ProblemBasicSchema(
            id=problem.id,
            title=problem.title,
            slug=problem.slug,
            difficulty=problem.difficulty,
            pattern=problem.pattern,
            sequence_number=problem.sequence_number,
        )

        progress_schema = None
        if progress:
            progress_schema = UserProgressBasicSchema(
                times_solved=progress.times_solved,
                last_solved_at=progress.last_solved_at,
                next_review_date=progress.next_review_date,
                is_mastered=progress.is_mastered,
                show_again=progress.show_again,
            )
            if progress.times_solved > 0:
                completed_count += 1
            if progress.is_mastered:
                mastered_count += 1

        problems_list.append(
            ProblemWithProgressSchema(
                problem=problem_schema,
                user_progress=progress_schema,
            )
        )

    return ProgressResponse(
        problems=problems_list,
        total_problems=len(problems_with_progress),
        completed_problems=completed_count,
        mastered_problems=mastered_count,
    )


@router.get("/mastered", response_model=MasteredProblemsResponse)
async def get_mastered(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of all mastered problems.

    Returns problems with mastery info and last submission, sorted by most recently solved.
    """
    user_id = user["id"]

    mastered = await get_mastered_problems(db, user_id)

    mastered_list = []
    for problem, progress, last_submission in mastered:
        problem_schema = ProblemBasicSchema(
            id=problem.id,
            title=problem.title,
            slug=problem.slug,
            difficulty=problem.difficulty,
            pattern=problem.pattern,
            sequence_number=problem.sequence_number,
        )

        progress_schema = UserProgressBasicSchema(
            times_solved=progress.times_solved,
            last_solved_at=progress.last_solved_at,
            next_review_date=progress.next_review_date,
            is_mastered=progress.is_mastered,
            show_again=progress.show_again,
        )

        submission_schema = None
        if last_submission:
            submission_schema = SubmissionBasicSchema(
                id=last_submission.id,
                code=last_submission.code,
                language=last_submission.language.value,
                passed=last_submission.passed,
                runtime_ms=last_submission.runtime_ms,
                memory_kb=last_submission.memory_kb,
                submitted_at=last_submission.submitted_at,
            )

        mastered_list.append(
            MasteredProblemSchema(
                problem=problem_schema,
                user_progress=progress_schema,
                last_submission=submission_schema,
            )
        )

    return MasteredProblemsResponse(mastered_problems=mastered_list)


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
