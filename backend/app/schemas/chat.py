"""Pydantic schemas for chat functionality."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.tables import ChatMode, MessageRole


# Chat Session Schemas
class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""

    problem_slug: str
    mode: ChatMode = Field(default=ChatMode.SOCRATIC)
    model: str | None = Field(default=None, description="LLM model (uses default if None)")
    title: str | None = Field(default=None, max_length=100, description="Optional session title")


class UpdateSessionRequest(BaseModel):
    """Request to update a chat session."""

    title: str | None = Field(default=None, max_length=50)
    mode: ChatMode | None = None
    model: str | None = None
    is_active: bool | None = None


class SendMessageRequest(BaseModel):
    """Request to send a message and stream AI response."""

    content: str = Field(..., min_length=1, description="User message content")
    current_code: str | None = Field(default=None, description="User's current code")
    test_results: dict | None = Field(default=None, description="Test execution results")


class ChatMessageSchema(BaseModel):
    """Chat message schema."""

    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    code_snapshot: str | None = None
    test_results_snapshot: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionSchema(BaseModel):
    """Chat session schema (without messages)."""

    id: UUID
    user_id: str
    problem_id: UUID
    title: str | None
    mode: ChatMode
    model: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionWithMessagesSchema(BaseModel):
    """Chat session with all messages."""

    id: UUID
    user_id: str
    problem_id: UUID
    title: str | None
    mode: ChatMode
    model: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageSchema]

    model_config = {"from_attributes": True}


# LLM Schemas (for internal use with LiteLLM)
class LLMMessage(BaseModel):
    """LLM message format."""

    role: Literal["system", "user", "assistant"]
    content: str


class LLMRequest(BaseModel):
    """Request to LLM service."""

    model: str
    messages: list[LLMMessage]
    max_tokens: int
    temperature: float
    stream: bool = True


class LLMStreamChunk(BaseModel):
    """Streaming chunk from LLM."""

    content: str
    finish_reason: str | None = None


# Model Configuration
class ModelInfo(BaseModel):
    """Available model information."""

    name: str
    display_name: str
    is_default: bool
