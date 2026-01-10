"""API routes for code persistence (save/reset user code)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.db.tables import Problem, UserCode
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/code", tags=["code"])


class SaveCodeRequest(BaseModel):
    """Request body for saving code."""

    problem_slug: str
    language: str = "python"
    code: str


class ResetCodeRequest(BaseModel):
    """Request body for resetting code."""

    problem_slug: str
    language: str = "python"


class SaveCodeResponse(BaseModel):
    """Response for save code endpoint."""

    success: bool
    message: str


class ResetCodeResponse(BaseModel):
    """Response for reset code endpoint."""

    success: bool
    message: str


@router.post("/save", response_model=SaveCodeResponse)
async def save_code(
    request: SaveCodeRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Save user's code for a problem.

    Upserts into user_code table - creates new record or updates existing.
    Called by frontend on debounced code changes (every 500ms after typing stops).
    """
    user_id = user["id"]

    # Get problem ID from slug
    result = await db.execute(select(Problem).where(Problem.slug == request.problem_slug))
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{request.problem_slug}' not found")

    # Upsert: insert or update on conflict
    stmt = insert(UserCode).values(
        user_id=user_id,
        problem_id=problem.id,
        language=request.language,
        code=request.code,
    )

    # On conflict (user_id, problem_id, language), update the code
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "problem_id", "language"],
        set_={"code": request.code},
    )

    await db.execute(stmt)
    await db.commit()

    return SaveCodeResponse(success=True, message="Code saved")


@router.post("/reset", response_model=ResetCodeResponse)
async def reset_code(
    request: ResetCodeRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reset user's code to starter code by deleting their saved code record.

    After this, fetching the problem will return starter_code since no user_code exists.
    """
    user_id = user["id"]

    # Get problem ID from slug
    result = await db.execute(select(Problem).where(Problem.slug == request.problem_slug))
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{request.problem_slug}' not found")

    # Delete user's code for this problem/language
    await db.execute(
        delete(UserCode).where(
            UserCode.user_id == user_id,
            UserCode.problem_id == problem.id,
            UserCode.language == request.language,
        )
    )
    await db.commit()

    return ResetCodeResponse(success=True, message="Code reset to starter code")


class LoadSubmissionRequest(BaseModel):
    """Request body for loading code from a submission."""

    problem_slug: str
    code: str
    language: str = "python"


@router.post("/load-submission", response_model=SaveCodeResponse)
async def load_submission_code(
    request: LoadSubmissionRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Load code from a past submission into the editor.

    Updates user_code with the submission's code so it appears in the editor.
    """
    user_id = user["id"]

    # Get problem ID from slug
    result = await db.execute(select(Problem).where(Problem.slug == request.problem_slug))
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{request.problem_slug}' not found")

    # Upsert: insert or update on conflict
    stmt = insert(UserCode).values(
        user_id=user_id,
        problem_id=problem.id,
        language=request.language,
        code=request.code,
    )

    # On conflict (user_id, problem_id, language), update the code
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "problem_id", "language"],
        set_={"code": request.code},
    )

    await db.execute(stmt)
    await db.commit()

    return SaveCodeResponse(success=True, message="Code loaded from submission")
