"""API routes for problems."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.connection import get_db
from app.db.tables import Problem
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
async def get_problem(slug: str, db: AsyncSession = Depends(get_db)):
    """
    Get detailed problem information including test cases and language configs.

    Only returns non-hidden test cases (hidden cases are only shown during submission).
    """
    result = await db.execute(
        select(Problem)
        .options(joinedload(Problem.languages), joinedload(Problem.test_cases))
        .where(Problem.slug == slug)
    )
    problem = result.unique().scalar_one_or_none()

    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{slug}' not found")

    # Build response with filtered test cases (don't mutate the ORM model)
    visible_test_cases = [tc for tc in problem.test_cases if not tc.is_hidden]

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
        test_cases=visible_test_cases,
    )
