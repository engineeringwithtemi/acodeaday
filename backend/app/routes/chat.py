"""API routes for chat functionality."""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.config.logging import get_logger
from app.db.connection import get_db
from app.middleware.auth import get_current_user
from app.schemas.chat import (
    ChatSessionSchema,
    ChatSessionWithMessagesSchema,
    CreateSessionRequest,
    ModelInfo,
    SendMessageRequest,
    UpdateSessionRequest,
)
from app.services.chat import (
    create_session,
    delete_session,
    get_session,
    get_sessions_for_problem,
    process_message_and_stream,
    update_session,
)
from app.services.llm import get_available_models, get_default_model

logger = get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/models", response_model=list[ModelInfo])
async def list_models():
    """
    Get list of available LLM models.

    Returns models that have valid API keys configured.
    First model in list is the default.
    """
    try:
        available = get_available_models()

        if not available:
            raise HTTPException(
                status_code=503,
                detail="No LLM models available - check API key configuration"
            )

        default_model = available[0]

        return [
            ModelInfo(
                name=model,
                display_name=model.replace("gemini/", "").replace("gpt-", "GPT-").replace("claude-", "Claude "),
                is_default=(model == default_model)
            )
            for model in available
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_models_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list models")


@router.post("/sessions", response_model=ChatSessionSchema)
async def create_chat_session(
    request: CreateSessionRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new chat session for a problem.

    The session will use the default model if none is specified.
    """
    try:
        # Import here to avoid circular dependency
        from sqlalchemy import select
        from app.db.tables import Problem

        # Get problem by slug
        result = await db.execute(select(Problem).where(Problem.slug == request.problem_slug))
        problem = result.scalar_one_or_none()

        if not problem:
            raise HTTPException(status_code=404, detail=f"Problem '{request.problem_slug}' not found")

        # Validate model if provided
        if request.model:
            available = get_available_models()
            if request.model not in available:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{request.model}' not available. Available models: {', '.join(available)}"
                )

        session = await create_session(
            db=db,
            user_id=user["id"],
            problem_id=problem.id,
            mode=request.mode,
            model=request.model,
            title=request.title,
        )

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_session_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create chat session")


@router.get("/sessions/{slug}", response_model=list[ChatSessionSchema])
async def list_sessions(
    slug: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all chat sessions for a problem.

    Returns sessions ordered by most recent first.
    """
    try:
        sessions = await get_sessions_for_problem(
            db=db,
            user_id=user["id"],
            problem_slug=slug,
        )
        return sessions

    except Exception as e:
        logger.error("list_sessions_error", slug=slug, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list sessions")


@router.get("/session/{session_id}", response_model=ChatSessionWithMessagesSchema)
async def get_chat_session(
    session_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a chat session with all messages.

    Only returns session if it belongs to the authenticated user.
    """
    try:
        session = await get_session(
            db=db,
            session_id=session_id,
            user_id=user["id"],
        )

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_session_error", session_id=str(session_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get session")


@router.patch("/session/{session_id}", response_model=ChatSessionSchema)
async def update_chat_session(
    session_id: uuid.UUID,
    request: UpdateSessionRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a chat session.

    Can update title, mode, model, or active status.
    """
    try:
        # Validate model if provided
        if request.model:
            available = get_available_models()
            if request.model not in available:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{request.model}' not available"
                )

        session = await update_session(
            db=db,
            session_id=session_id,
            user_id=user["id"],
            title=request.title,
            mode=request.mode,
            model=request.model,
            is_active=request.is_active,
        )

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_session_error", session_id=str(session_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update session")


@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a chat session (soft delete).

    Sets is_active=False instead of actually deleting.
    """
    try:
        success = await delete_session(
            db=db,
            session_id=session_id,
            user_id=user["id"],
        )

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_session_error", session_id=str(session_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.post("/session/{session_id}/message")
async def send_message_stream(
    session_id: uuid.UUID,
    request: SendMessageRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message and stream AI response in a single request.

    This endpoint:
    1. Saves the user message to the database
    2. Streams the AI response using Server-Sent Events format
    3. Saves the complete AI response to the database

    The response is a streaming response with SSE format:
    - data: {"type": "chunk", "content": "..."}
    - data: {"type": "done", "message_id": "..."}
    - data: {"type": "error", "error": "..."}
    """

    async def event_generator():
        try:
            async for event in process_message_and_stream(
                db=db,
                session_id=session_id,
                user_id=user["id"],
                user_message=request.content,
                current_code=request.current_code,
                test_results=request.test_results,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error("stream_error", session_id=str(session_id), error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
