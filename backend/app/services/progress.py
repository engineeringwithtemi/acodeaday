"""Spaced repetition logic and user progress management."""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import get_logger
from app.db.tables import Problem, UserProgress

logger = get_logger(__name__)

# Spaced repetition constants
REVIEW_INTERVAL_DAYS = 7


def _utcnow() -> datetime:
    """Return current UTC time as naive datetime (for TIMESTAMP WITHOUT TIME ZONE columns)."""
    return datetime.now(UTC).replace(tzinfo=None)


def _utc_date() -> date:
    """Return current UTC date (not local date)."""
    return datetime.now(UTC).date()


async def update_user_progress(
    db: AsyncSession, user_id: str, problem_id: uuid.UUID, passed: bool
) -> dict:
    """
    Update user progress after submission.

    Spaced repetition logic:
    - First solve (times_solved=0): Set times_solved=1, next_review_date = today + 7 days
    - Second solve (times_solved=1): Set times_solved=2, is_mastered=True, next_review_date=None
    - Already mastered: Do nothing (no state change)

    Args:
        db: Database session
        user_id: User identifier (username from Basic Auth)
        problem_id: Problem UUID
        passed: Whether submission passed all tests

    Returns:
        Dict with updated progress info (times_solved, is_mastered, next_review_date)
    """
    if not passed:
        logger.info("submission_failed_no_progress_update", user_id=user_id, problem_id=str(problem_id))
        return {}

    # Find or create UserProgress
    result = await db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == user_id)
        .where(UserProgress.problem_id == problem_id)
    )
    progress = result.scalar_one_or_none()

    if not progress:
        # First time solving this problem
        progress = UserProgress(
            user_id=user_id,
            problem_id=problem_id,
            times_solved=1,
            last_solved_at=_utcnow(),
            next_review_date=_utc_date() + timedelta(days=REVIEW_INTERVAL_DAYS),
            is_mastered=False,
            show_again=False,
        )
        db.add(progress)
        logger.info(
            "first_solve",
            user_id=user_id,
            problem_id=str(problem_id),
            next_review=str(progress.next_review_date),
        )
        return {
            "times_solved": 1,
            "is_mastered": False,
            "next_review_date": progress.next_review_date.isoformat(),
        }

    # Check if already mastered (and not flagged for show_again)
    if progress.is_mastered and not progress.show_again:
        logger.info(
            "already_mastered_no_update",
            user_id=user_id,
            problem_id=str(problem_id),
            times_solved=progress.times_solved,
        )
        return {
            "times_solved": progress.times_solved,
            "is_mastered": True,
            "next_review_date": None,
        }

    # Update based on current times_solved
    if progress.times_solved == 0:
        # First solve (edge case: progress exists but times_solved=0)
        progress.times_solved = 1
        progress.last_solved_at = _utcnow()
        progress.next_review_date = _utc_date() + timedelta(days=REVIEW_INTERVAL_DAYS)
        logger.info(
            "first_solve_update",
            user_id=user_id,
            problem_id=str(problem_id),
            next_review=str(progress.next_review_date),
        )
        return {
            "times_solved": 1,
            "is_mastered": False,
            "next_review_date": progress.next_review_date.isoformat(),
        }

    elif progress.times_solved == 1 or (progress.show_again and progress.is_mastered):
        # Second solve - mark as mastered
        progress.times_solved = 2 if progress.times_solved == 1 else progress.times_solved + 1
        progress.last_solved_at = _utcnow()
        progress.is_mastered = True
        progress.next_review_date = None
        progress.show_again = False
        logger.info(
            "mastered",
            user_id=user_id,
            problem_id=str(problem_id),
            times_solved=progress.times_solved,
        )
        return {
            "times_solved": progress.times_solved,
            "is_mastered": True,
            "next_review_date": None,
        }

    # Already solved 2+ times (shouldn't reach here if mastered check works)
    logger.info(
        "already_solved_multiple_times",
        user_id=user_id,
        problem_id=str(problem_id),
        times_solved=progress.times_solved,
    )
    return {
        "times_solved": progress.times_solved,
        "is_mastered": progress.is_mastered,
        "next_review_date": progress.next_review_date.isoformat() if progress.next_review_date else None,
    }


async def get_todays_problems(
    db: AsyncSession, user_id: str
) -> tuple[list[Problem], list[UserProgress], Problem | None]:
    """
    Get today's problems: up to 2 reviews + 1 new problem.

    Returns tuple of:
    - List of review problems (up to 2)
    - List of UserProgress for those problems
    - New problem (or None if all problems attempted)

    Returns problems in order:
    1. Oldest overdue review (if any)
    2. Second oldest overdue review (if any)
    3. Next unsolved problem (by sequence_number)
    """
    # 1. Get up to 2 overdue reviews
    result = await db.execute(
        select(Problem, UserProgress)
        .join(UserProgress, Problem.id == UserProgress.problem_id)
        .where(UserProgress.user_id == user_id)
        .where(UserProgress.is_mastered.is_(False))
        .where(UserProgress.next_review_date <= _utc_date())
        .order_by(UserProgress.next_review_date.asc())
        .limit(2)
    )
    review_data = result.all()
    review_problems = [row[0] for row in review_data]
    review_progress = [row[1] for row in review_data]

    # 2. Get next unsolved problem (by sequence_number)
    # Find lowest sequence_number not in user_progress
    result = await db.execute(
        select(Problem)
        .where(
            ~Problem.id.in_(
                select(UserProgress.problem_id).where(UserProgress.user_id == user_id)
            )
        )
        .order_by(Problem.sequence_number.asc())
        .limit(1)
    )
    new_problem = result.scalar_one_or_none()

    logger.info(
        "todays_problems",
        user_id=user_id,
        review_count=len(review_problems),
        has_new_problem=new_problem is not None,
    )

    return review_problems, review_progress, new_problem


async def get_user_progress_stats(db: AsyncSession, user_id: str) -> dict:
    """
    Get user's overall progress statistics.

    Returns:
        Dict with counts and breakdowns
    """
    # Get all user progress
    result = await db.execute(
        select(UserProgress, Problem)
        .join(Problem, UserProgress.problem_id == Problem.id)
        .where(UserProgress.user_id == user_id)
    )
    progress_data = result.all()

    # Calculate stats
    solved_count = len(progress_data)
    mastered_count = sum(1 for progress, _ in progress_data if progress.is_mastered)
    in_progress_count = solved_count - mastered_count

    # Due for review count
    due_count = sum(
        1
        for progress, _ in progress_data
        if progress.next_review_date
        and progress.next_review_date <= _utc_date()
        and not progress.is_mastered
    )

    # Get total problem count
    result = await db.execute(select(Problem))
    total_problems = len(result.scalars().all())

    # Breakdowns by difficulty and pattern
    problems_by_difficulty = {}
    problems_by_pattern = {}

    for progress, problem in progress_data:
        # Difficulty
        diff = problem.difficulty.value
        problems_by_difficulty[diff] = problems_by_difficulty.get(diff, 0) + 1

        # Pattern
        pattern = problem.pattern
        problems_by_pattern[pattern] = problems_by_pattern.get(pattern, 0) + 1

    return {
        "total_problems": total_problems,
        "solved_count": solved_count,
        "mastered_count": mastered_count,
        "in_progress_count": in_progress_count,
        "unsolved_count": total_problems - solved_count,
        "due_for_review": due_count,
        "problems_by_difficulty": problems_by_difficulty,
        "problems_by_pattern": problems_by_pattern,
    }


async def get_mastered_problems(
    db: AsyncSession, user_id: str
) -> list[tuple[Problem, UserProgress]]:
    """
    Get all mastered problems for a user.

    Returns:
        List of (Problem, UserProgress) tuples
    """
    result = await db.execute(
        select(Problem, UserProgress)
        .join(UserProgress, Problem.id == UserProgress.problem_id)
        .where(UserProgress.user_id == user_id)
        .where(UserProgress.is_mastered.is_(True))
        .order_by(UserProgress.last_solved_at.desc())
    )
    return result.all()


async def mark_show_again(
    db: AsyncSession, user_id: str, problem_id: uuid.UUID
) -> None:
    """
    Mark a mastered problem to show again in rotation.

    Sets show_again=True, is_mastered=False, next_review_date=today.
    """
    result = await db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == user_id)
        .where(UserProgress.problem_id == problem_id)
    )
    progress = result.scalar_one_or_none()

    if not progress:
        raise ValueError("Progress record not found")

    if not progress.is_mastered:
        raise ValueError("Problem is not mastered")

    # Re-add to rotation
    progress.show_again = True
    progress.is_mastered = False
    progress.next_review_date = _utc_date()

    logger.info(
        "marked_show_again",
        user_id=user_id,
        problem_id=str(problem_id),
        next_review=str(progress.next_review_date),
    )
    # Note: Caller is responsible for committing the transaction
