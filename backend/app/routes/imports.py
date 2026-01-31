"""API routes for AI-powered problem import."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import get_logger
from app.db.connection import get_db
from app.db.tables import ImportJob, ImportJobProblem, ImportJobStatus, Problem
from app.middleware.auth import get_current_user
from app.schemas.import_schemas import (
    ImportedProblemResponse,
    ImportJobDetailResponse,
    ImportJobResponse,
    ImportJobSummaryResponse,
    ImportRequest,
)
from app.services.import_workflow import import_problems_workflow

logger = get_logger(__name__)
router = APIRouter(prefix="/api/imports", tags=["imports"])

MAX_CONCURRENT_JOBS = 3


@router.post("/", response_model=ImportJobResponse)
async def start_import(
    request: ImportRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a problem import workflow."""
    user_id = user["id"]

    # Debounce: check for active import with same prompt
    active = await db.execute(
        select(ImportJob).where(
            ImportJob.user_id == user_id,
            ImportJob.prompt == request.prompt,
            ImportJob.status.in_(["queued", "processing"]),
        )
    )
    existing = active.scalar_one_or_none()
    if existing:
        return ImportJobResponse.model_validate(existing)

    # Enforce concurrent job limit
    active_count_result = await db.execute(
        select(ImportJob).where(
            ImportJob.user_id == user_id,
            ImportJob.status.in_(["queued", "processing"]),
        )
    )
    active_jobs = active_count_result.scalars().all()
    if len(active_jobs) >= MAX_CONCURRENT_JOBS:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum {MAX_CONCURRENT_JOBS} concurrent imports allowed. "
            "Please wait for an existing import to complete.",
        )

    # Create import job record
    job = ImportJob(
        user_id=user_id,
        prompt=request.prompt,
        status=ImportJobStatus.QUEUED,
        message="Your request has been accepted",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Start background task
    asyncio.create_task(
        import_problems_workflow(str(job.id), request.prompt),
        name=f"import-{job.id}",
    )

    logger.info("import_started", job_id=str(job.id), prompt=request.prompt)
    return ImportJobResponse.model_validate(job)


@router.get("/", response_model=list[ImportJobSummaryResponse])
async def list_imports(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all import jobs for the current user."""
    result = await db.execute(
        select(ImportJob)
        .where(ImportJob.user_id == user["id"])
        .order_by(ImportJob.created_at.desc())
    )
    jobs = result.scalars().all()
    return [ImportJobSummaryResponse.model_validate(j) for j in jobs]


@router.get("/{import_id}", response_model=ImportJobDetailResponse)
async def get_import(
    import_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get import job status with linked problems."""
    import uuid as uuid_mod

    try:
        job_uuid = uuid_mod.UUID(import_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid import ID")

    job = await db.get(ImportJob, job_uuid)
    if not job or job.user_id != user["id"]:
        raise HTTPException(status_code=404, detail="Import job not found")

    # Get linked problems
    problems_result = await db.execute(
        select(Problem)
        .join(ImportJobProblem, Problem.id == ImportJobProblem.problem_id)
        .where(ImportJobProblem.import_job_id == job.id)
        .order_by(Problem.sequence_number)
    )
    problems = problems_result.scalars().all()

    return ImportJobDetailResponse(
        id=job.id,
        prompt=job.prompt,
        status=job.status.value if hasattr(job.status, "value") else str(job.status),
        message=job.message,
        progress=job.progress,
        total=job.total,
        problems=[
            ImportedProblemResponse(
                id=p.id,
                title=p.title,
                slug=p.slug,
                difficulty=p.difficulty.value if hasattr(p.difficulty, "value") else str(p.difficulty),
                pattern=p.pattern,
            )
            for p in problems
        ],
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.post("/{import_id}/cancel")
async def cancel_import(
    import_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an in-progress import. Cancellation is cooperative — the workflow
    checks for cancellation at the top of each problem iteration."""
    import uuid as uuid_mod

    try:
        job_uuid = uuid_mod.UUID(import_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid import ID")

    job = await db.get(ImportJob, job_uuid)
    if not job or job.user_id != user["id"]:
        raise HTTPException(status_code=404, detail="Import job not found")

    if job.status not in (ImportJobStatus.QUEUED, ImportJobStatus.PROCESSING):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status '{job.status}'",
        )

    job.status = ImportJobStatus.CANCELLED
    job.message = "Cancelling..."
    await db.commit()

    logger.info("import_cancelled", job_id=str(job.id))
    return {"status": "cancelled", "message": "Import will be cancelled shortly"}
