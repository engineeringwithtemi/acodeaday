"""Spaced repetition logic and user progress management."""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.logging import get_logger
from app.db.tables import Problem, Submission, UserProgress

logger = get_logger(__name__)

# Spaced repetition constants (legacy)
REVIEW_INTERVAL_DAYS = 7

# Anki SM-2 algorithm constants
DEFAULT_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3
MASTERY_THRESHOLD_DAYS = 30  # Auto-master when interval reaches this

# Valid ratings
VALID_RATINGS = {"again", "hard", "good", "mastered"}


def calculate_next_review(
    current_interval: int,
    ease_factor: float,
    rating: str,
) -> tuple[int, float, bool]:
    """
    Calculate next review interval using SM-2 algorithm.

    Args:
        current_interval: Current interval in days (0 for first review)
        ease_factor: Current ease factor (default 2.5)
        rating: User rating ("again", "hard", "good", "mastered")

    Returns:
        Tuple of (new_interval_days, new_ease_factor, is_mastered)
    """
    if rating == "mastered":
        # Immediately mark as mastered, exit rotation
        return 0, ease_factor, True

    if rating == "again":
        # Reset to 1 day, decrease ease
        new_ease = max(MIN_EASE_FACTOR, ease_factor - 0.2)
        return 1, new_ease, False

    if current_interval == 0:
        # First review - use fixed intervals
        intervals = {"hard": 1, "good": 3}
        return intervals[rating], ease_factor, False

    if rating == "hard":
        # Slower growth, decrease ease slightly
        # Ensure interval always grows by at least 1 day
        new_interval = max(current_interval + 1, int(current_interval * 1.2))
        new_ease = max(MIN_EASE_FACTOR, ease_factor - 0.15)
        return new_interval, new_ease, False

    if rating == "good":
        # Normal growth using ease factor
        # Ensure interval always grows by at least 1 day (prevents stuck at 1 with low ease)
        new_interval = max(current_interval + 1, int(current_interval * ease_factor))
        # Auto-master if interval reaches threshold
        is_mastered = new_interval >= MASTERY_THRESHOLD_DAYS
        return new_interval, ease_factor, is_mastered

    # Should never reach here
    raise ValueError(f"Invalid rating: {rating}")


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
    Update user progress after submission (Anki-style).

    On successful submission:
    - Creates progress record if first time (doesn't set interval - that's done via rating)
    - Returns current progress state + flag indicating rating is needed
    - Only shows rating if problem is "due" (first time, or next_review_date <= today)

    Args:
        db: Database session
        user_id: User identifier (username from Basic Auth)
        problem_id: Problem UUID
        passed: Whether submission passed all tests

    Returns:
        Dict with progress info and needs_rating flag
    """
    if not passed:
        logger.info("submission_failed_no_progress_update", user_id=user_id, problem_id=str(problem_id))
        return {"needs_rating": False}

    # Find or create UserProgress
    result = await db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == user_id)
        .where(UserProgress.problem_id == problem_id)
    )
    progress = result.scalar_one_or_none()

    if not progress:
        # First time solving - create progress record
        # Don't set interval yet - that happens when user rates
        progress = UserProgress(
            user_id=user_id,
            problem_id=problem_id,
            times_solved=0,  # Will be incremented when rating is applied
            last_solved_at=None,
            next_review_date=None,
            is_mastered=False,
            show_again=False,
            ease_factor=DEFAULT_EASE_FACTOR,
            interval_days=0,
            review_count=0,
        )
        db.add(progress)
        logger.info(
            "first_solve_record_created",
            user_id=user_id,
            problem_id=str(problem_id),
        )
        # First time - always show rating
        return {
            "needs_rating": True,
            "times_solved": 0,
            "is_mastered": False,
            "next_review_date": None,
            "interval_days": 0,
            "ease_factor": DEFAULT_EASE_FACTOR,
        }

    # Check if already mastered (and not flagged for show_again)
    if progress.is_mastered and not progress.show_again:
        logger.info(
            "already_mastered",
            user_id=user_id,
            problem_id=str(problem_id),
        )
        return {
            "needs_rating": False,
            "times_solved": progress.times_solved,
            "is_mastered": True,
            "next_review_date": None,
            "interval_days": progress.interval_days,
            "ease_factor": round(progress.ease_factor, 2),
        }

    # Check if problem is due for review
    today = _utc_date()
    is_due = (
        progress.next_review_date is None  # Never rated yet
        or progress.next_review_date <= today  # Due for review
    )

    if not is_due:
        logger.info(
            "not_due_for_review",
            user_id=user_id,
            problem_id=str(problem_id),
            next_review_date=str(progress.next_review_date),
        )
        return {
            "needs_rating": False,
            "times_solved": progress.times_solved,
            "is_mastered": progress.is_mastered,
            "next_review_date": progress.next_review_date.isoformat(),
            "interval_days": progress.interval_days,
            "ease_factor": round(progress.ease_factor, 2),
        }

    # Problem is due - show rating buttons
    return {
        "needs_rating": True,
        "times_solved": progress.times_solved,
        "is_mastered": progress.is_mastered,
        "next_review_date": progress.next_review_date.isoformat() if progress.next_review_date else None,
        "interval_days": progress.interval_days,
        "ease_factor": round(progress.ease_factor, 2),
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


async def get_all_problems_with_progress(
    db: AsyncSession, user_id: str
) -> list[tuple[Problem, UserProgress | None]]:
    """
    Get all problems with their user progress (if any).

    Returns all problems ordered by sequence_number, with user progress
    joined where available (None for unsolved problems).

    Returns:
        List of (Problem, UserProgress | None) tuples
    """
    # Get all problems
    result = await db.execute(
        select(Problem).order_by(Problem.sequence_number.asc())
    )
    all_problems = result.scalars().all()

    # Get user's progress for all problems
    result = await db.execute(
        select(UserProgress).where(UserProgress.user_id == user_id)
    )
    progress_list = result.scalars().all()

    # Create a lookup dict by problem_id
    progress_by_problem = {p.problem_id: p for p in progress_list}

    # Combine problems with their progress (None if not started)
    return [(problem, progress_by_problem.get(problem.id)) for problem in all_problems]


async def get_mastered_problems(
    db: AsyncSession, user_id: str
) -> list[tuple[Problem, UserProgress, Submission | None]]:
    """
    Get all mastered problems for a user with their last submission.

    Returns:
        List of (Problem, UserProgress, Submission | None) tuples
    """
    # Get mastered problems with progress
    result = await db.execute(
        select(Problem, UserProgress)
        .join(UserProgress, Problem.id == UserProgress.problem_id)
        .where(UserProgress.user_id == user_id)
        .where(UserProgress.is_mastered.is_(True))
        .order_by(UserProgress.last_solved_at.desc())
    )
    mastered_data = result.all()

    if not mastered_data:
        return []

    # Get the last passing submission for each mastered problem
    problem_ids = [problem.id for problem, _ in mastered_data]

    # For each problem, get the most recent passing submission
    submissions_by_problem = {}
    for problem_id in problem_ids:
        result = await db.execute(
            select(Submission)
            .where(Submission.user_id == user_id)
            .where(Submission.problem_id == problem_id)
            .where(Submission.passed.is_(True))
            .order_by(Submission.submitted_at.desc())
            .limit(1)
        )
        submission = result.scalar_one_or_none()
        if submission:
            submissions_by_problem[problem_id] = submission

    # Combine into tuples
    return [
        (problem, progress, submissions_by_problem.get(problem.id))
        for problem, progress in mastered_data
    ]


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

    # Re-add to rotation and reset Anki fields
    progress.show_again = True
    progress.is_mastered = False
    progress.next_review_date = _utc_date()
    progress.interval_days = 0
    progress.ease_factor = DEFAULT_EASE_FACTOR

    logger.info(
        "marked_show_again",
        user_id=user_id,
        problem_id=str(problem_id),
        next_review=str(progress.next_review_date),
        ease_factor_reset=DEFAULT_EASE_FACTOR,
    )
    # Note: Caller is responsible for committing the transaction


async def apply_rating(
    db: AsyncSession,
    user_id: str,
    problem_id: uuid.UUID,
    rating: str,
) -> dict:
    """
    Apply a user's difficulty rating after successful submission.

    Uses the SM-2 algorithm to calculate the next review interval
    and update the ease factor.

    Args:
        db: Database session
        user_id: User identifier
        problem_id: Problem UUID
        rating: One of "again", "hard", "good", "mastered"

    Returns:
        Dict with updated progress info

    Raises:
        ValueError: If rating is invalid or no progress record exists
    """
    if rating not in VALID_RATINGS:
        raise ValueError(f"Invalid rating: {rating}. Must be one of {VALID_RATINGS}")

    # Find UserProgress record
    result = await db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == user_id)
        .where(UserProgress.problem_id == problem_id)
    )
    progress = result.scalar_one_or_none()

    if not progress:
        raise ValueError("No progress record found. User must submit successfully first.")

    # Calculate new values using SM-2 algorithm
    new_interval, new_ease, is_mastered = calculate_next_review(
        current_interval=progress.interval_days,
        ease_factor=progress.ease_factor,
        rating=rating,
    )

    # Update progress record
    progress.interval_days = new_interval
    progress.ease_factor = new_ease
    progress.is_mastered = is_mastered
    progress.review_count += 1
    progress.times_solved += 1
    progress.last_solved_at = _utcnow()

    if is_mastered:
        progress.next_review_date = None
    else:
        progress.next_review_date = _utc_date() + timedelta(days=new_interval)

    logger.info(
        "rating_applied",
        user_id=user_id,
        problem_id=str(problem_id),
        rating=rating,
        new_interval=new_interval,
        new_ease=new_ease,
        is_mastered=is_mastered,
        next_review=str(progress.next_review_date),
    )

    return {
        "interval_days": new_interval,
        "ease_factor": round(new_ease, 2),
        "next_review_date": progress.next_review_date.isoformat() if progress.next_review_date else None,
        "is_mastered": is_mastered,
        "review_count": progress.review_count,
        "times_solved": progress.times_solved,
    }
