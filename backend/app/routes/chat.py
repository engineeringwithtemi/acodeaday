"""API routes for chat functionality."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import get_logger
from app.db.connection import get_db
from app.middleware.auth import get_current_user
from app.schemas.chat import (
    ChatSessionSchema,
    ChatSessionWithMessagesSchema,
    ChatWSMessage,
    ChatWSResponse,
    CreateSessionRequest,
    ModelInfo,
    UpdateSessionRequest,
)
from app.services.chat import (
    create_session,
    delete_session,
    get_session,
    get_sessions_for_problem,
    stream_response,
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


@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: uuid.UUID,
    token: str,
):
    """
    WebSocket endpoint for streaming chat responses.

    Authentication is via token query parameter (WebSockets don't support headers).
    Client sends ChatWSMessage, server streams ChatWSResponse.

    Message flow:
    1. Client connects with ?token=jwt_token
    2. Server validates token and accepts connection
    3. Client sends {"type": "message", "content": "...", "current_code": "...", "test_results": {...}}
    4. Server streams {"type": "chunk", "content": "..."}
    5. Server sends {"type": "done", "message_id": "..."}
    6. On error: {"type": "error", "error": "..."}
    """
    # Validate token
    from app.config.settings import settings

    try:
        # Get supabase client from app state
        supabase = websocket.app.state.supabase

        # Validate token
        response = await supabase.auth.get_user(token)

        if not response or not response.user:
            await websocket.close(code=4001, reason="Unauthorized")
            return

        user_id = response.user.id

    except Exception as e:
        logger.error("ws_auth_failed", error=str(e))
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # Accept WebSocket connection
    await websocket.accept()
    logger.info("ws_connected", session_id=str(session_id), user_id=user_id)

    try:
        # Get database session
        async for db in get_db():
            # Verify session belongs to user
            session = await get_session(db=db, session_id=session_id, user_id=user_id)

            if not session:
                await websocket.send_json(
                    ChatWSResponse(type="error", error="Session not found or unauthorized").model_dump()
                )
                await websocket.close()
                return

            # Listen for messages
            while True:
                try:
                    # Receive message from client
                    data = await websocket.receive_json()
                    ws_message = ChatWSMessage(**data)

                    if ws_message.type == "cancel":
                        logger.info("ws_cancel_requested", session_id=str(session_id))
                        # Just stop processing, client can reconnect
                        break

                    elif ws_message.type == "message":
                        if not ws_message.content:
                            await websocket.send_json(
                                ChatWSResponse(type="error", error="Message content required").model_dump()
                            )
                            continue

                        # Stream response
                        async for response in stream_response(
                            db=db,
                            session_id=session_id,
                            user_message=ws_message.content,
                            current_code=ws_message.current_code,
                            test_results=ws_message.test_results,
                        ):
                            await websocket.send_json(response.model_dump())

                except WebSocketDisconnect:
                    logger.info("ws_disconnected", session_id=str(session_id))
                    break

                except Exception as e:
                    logger.error("ws_message_error", session_id=str(session_id), error=str(e))
                    await websocket.send_json(
                        ChatWSResponse(type="error", error=str(e)).model_dump()
                    )

            break  # Exit the async for db loop

    except Exception as e:
        logger.error("ws_error", session_id=str(session_id), error=str(e))
        try:
            await websocket.send_json(
                ChatWSResponse(type="error", error="Internal server error").model_dump()
            )
        except:
            pass
        await websocket.close()
