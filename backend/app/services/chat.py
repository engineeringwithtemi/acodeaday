"""Chat service for managing chat sessions and messages."""

import uuid
from typing import AsyncGenerator

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.logging import get_logger
from app.db.tables import ChatMessage, ChatMode, ChatSession, MessageRole, Problem
from app.schemas.chat import ChatWSResponse, LLMMessage, LLMStreamChunk
from app.services.llm import build_context_message, generate_session_title, stream_chat_completion

logger = get_logger(__name__)


async def create_session(
    db: AsyncSession,
    user_id: str,
    problem_id: uuid.UUID,
    mode: ChatMode,
    model: str | None = None,
) -> ChatSession:
    """
    Create a new chat session.

    Args:
        db: Database session
        user_id: User identifier
        problem_id: Problem UUID
        mode: Chat mode (socratic or direct)
        model: LLM model to use (None = default)

    Returns:
        Created ChatSession
    """
    # Count existing sessions for this user/problem to generate title
    result = await db.execute(
        select(func.count(ChatSession.id))
        .where(ChatSession.user_id == user_id)
        .where(ChatSession.problem_id == problem_id)
    )
    session_count = result.scalar() or 0
    default_title = f"acadAI Chat {session_count + 1}"

    session = ChatSession(
        user_id=user_id,
        problem_id=problem_id,
        mode=mode,
        model=model,
        is_active=True,
        title=default_title,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info("chat_session_created", session_id=str(session.id), mode=mode, model=model, title=default_title)
    return session


async def get_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: str,
) -> ChatSession | None:
    """
    Get a chat session with its messages.

    Args:
        db: Database session
        session_id: Session UUID
        user_id: User identifier (for authorization)

    Returns:
        ChatSession with messages loaded, or None if not found/unauthorized
    """
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id)
        .where(ChatSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()

    if session:
        # Sort messages by created_at
        session.messages.sort(key=lambda m: m.created_at)

    return session


async def get_sessions_for_problem(
    db: AsyncSession,
    user_id: str,
    problem_slug: str,
) -> list[ChatSession]:
    """
    Get all chat sessions for a specific problem.

    Args:
        db: Database session
        user_id: User identifier
        problem_slug: Problem slug

    Returns:
        List of ChatSession objects (without messages loaded)
    """
    # First get the problem ID
    result = await db.execute(select(Problem).where(Problem.slug == problem_slug))
    problem = result.scalar_one_or_none()

    if not problem:
        return []

    # Get sessions for this problem
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .where(ChatSession.problem_id == problem.id)
        .where(ChatSession.is_active == True)  # noqa: E712
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    return list(sessions)


async def update_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: str,
    title: str | None = None,
    mode: ChatMode | None = None,
    model: str | None = None,
    is_active: bool | None = None,
) -> ChatSession | None:
    """
    Update a chat session.

    Args:
        db: Database session
        session_id: Session UUID
        user_id: User identifier (for authorization)
        title: New title (optional)
        mode: New mode (optional)
        model: New model (optional)
        is_active: New active status (optional)

    Returns:
        Updated ChatSession or None if not found/unauthorized
    """
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .where(ChatSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        return None

    if title is not None:
        session.title = title
    if mode is not None:
        session.mode = mode
    if model is not None:
        session.model = model
    if is_active is not None:
        session.is_active = is_active

    await db.commit()
    await db.refresh(session)

    logger.info("chat_session_updated", session_id=str(session_id))
    return session


async def delete_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: str,
) -> bool:
    """
    Delete a chat session (soft delete by setting is_active=False).

    Args:
        db: Database session
        session_id: Session UUID
        user_id: User identifier (for authorization)

    Returns:
        True if deleted, False if not found/unauthorized
    """
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .where(ChatSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        return False

    session.is_active = False
    await db.commit()

    logger.info("chat_session_deleted", session_id=str(session_id))
    return True


async def add_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    role: MessageRole,
    content: str,
    code_snapshot: str | None = None,
    test_results_snapshot: dict | None = None,
) -> ChatMessage:
    """
    Add a message to a chat session.

    Args:
        db: Database session
        session_id: Session UUID
        role: Message role (user, assistant, system)
        content: Message content (Markdown)
        code_snapshot: Code snapshot at time of message
        test_results_snapshot: Test results snapshot

    Returns:
        Created ChatMessage
    """
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        code_snapshot=code_snapshot,
        test_results_snapshot=test_results_snapshot,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    logger.info("chat_message_added", session_id=str(session_id), role=role, content_length=len(content))
    return message


async def stream_response(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_message: str,
    current_code: str | None = None,
    test_results: dict | None = None,
) -> AsyncGenerator[ChatWSResponse, None]:
    """
    Stream AI response for a user message.

    This function:
    1. Saves the user message to DB
    2. Loads problem context and conversation history
    3. Streams LLM response
    4. Saves complete assistant response to DB
    5. Auto-generates title if first message

    Args:
        db: Database session
        session_id: Session UUID
        user_message: User's message content
        current_code: User's current code
        test_results: Test execution results

    Yields:
        ChatWSResponse objects (chunks, done, or error)
    """
    try:
        # Get session with problem data
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.problem))
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            yield ChatWSResponse(type="error", error="Session not found")
            return

        # Save user message
        user_msg = await add_message(
            db=db,
            session_id=session_id,
            role=MessageRole.USER,
            content=user_message,
            code_snapshot=current_code,
            test_results_snapshot=test_results,
        )

        # Build context from problem data
        problem = session.problem
        context_msg = build_context_message(
            problem_title=problem.title,
            problem_description=problem.description,
            problem_constraints=problem.constraints,
            problem_examples=problem.examples.get("examples", []) if isinstance(problem.examples, dict) else problem.examples,
            current_code=current_code,
            test_results=test_results,
        )

        # Build conversation history (last 20 messages)
        history_messages: list[LLMMessage] = []
        messages = sorted(session.messages, key=lambda m: m.created_at)

        # Add context as first user message if no prior messages (excluding the one we just added)
        if len(messages) == 1:  # Only the message we just added
            history_messages.append(LLMMessage(role="user", content=context_msg))
            history_messages.append(LLMMessage(role="user", content=user_message))
        else:
            # Add last 20 messages (excluding system messages and the one we just added)
            for msg in messages[-21:-1]:  # -1 to exclude the message we just added
                if msg.role != MessageRole.SYSTEM:
                    history_messages.append(
                        LLMMessage(
                            role=msg.role.value,
                            content=msg.content,
                        )
                    )
            # Add current context and user message
            history_messages.append(LLMMessage(role="user", content=f"{context_msg}\n\n---\n\n{user_message}"))

        # Stream LLM response
        assistant_content = ""
        async for chunk in stream_chat_completion(
            messages=history_messages,
            model=session.model,
            mode=session.mode.value,
        ):
            assistant_content += chunk.content
            yield ChatWSResponse(type="chunk", content=chunk.content)

            if chunk.finish_reason:
                break

        # Save complete assistant response
        assistant_msg = await add_message(
            db=db,
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
        )

        # Generate title if this is the first exchange
        if len(messages) == 1 and not session.title:
            try:
                title = await generate_session_title(user_message)
                session.title = title
                await db.commit()
            except Exception as e:
                logger.warning("title_generation_failed", error=str(e))

        yield ChatWSResponse(type="done", message_id=str(assistant_msg.id))

    except Exception as e:
        logger.error("stream_response_error", session_id=str(session_id), error=str(e))
        yield ChatWSResponse(type="error", error=str(e))
