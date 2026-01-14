"""SQLAlchemy database models for acodeaday."""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Difficulty(enum.StrEnum):
    """Problem difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Language(enum.StrEnum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    # Future languages can be added here:
    # JAVA = "java"
    # CPP = "cpp"
    # GO = "go"


class ChatMode(enum.StrEnum):
    """Chat assistant modes."""

    SOCRATIC = "socratic"
    DIRECT = "direct"


class MessageRole(enum.StrEnum):
    """Chat message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Problem(Base):
    """Core problem data from Blind 75."""

    __tablename__ = "problems"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), nullable=False)
    pattern: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g., "hash-map", "two-pointers"

    # SEQUENCE_NUMBER: Determines order in Blind 75 (1-75)
    # Used to find "next unsolved problem": SELECT * WHERE sequence_number = (min unsolved)
    sequence_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    # Constraints as ARRAY of strings (not JSONB)
    constraints: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)

    # Examples stored as JSONB (complex structure with input/output/explanation)
    examples: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    languages: Mapped[list["ProblemLanguage"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )
    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )
    user_progress: Mapped[list["UserProgress"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )
    user_codes: Mapped[list["UserCode"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )


class ProblemLanguage(Base):
    """Language-specific code and solutions for problems."""

    __tablename__ = "problem_languages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[Language] = mapped_column(
        Enum(Language), nullable=False
    )  # Python, JavaScript, etc.
    starter_code: Mapped[str] = mapped_column(Text, nullable=False)
    reference_solution: Mapped[str] = mapped_column(Text, nullable=False)

    # Function signature as JSONB: {"name": "twoSum", "params": [...], "return_type": "List[int]"}
    function_signature: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    problem: Mapped["Problem"] = relationship(back_populates="languages")

    __table_args__ = (
        Index("ix_problem_languages_problem_id", "problem_id"),
        Index("ix_problem_languages_language", "language"),
    )


class TestCase(Base):
    """Test inputs and expected outputs for problems."""

    __tablename__ = "test_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )

    # Input as JSONB array: [[2,7,11,15], 9] means twoSum([2,7,11,15], 9)
    input: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Stored as JSON array

    # Expected output as JSONB: [0,1] or "hello" or {"key": "value"}
    expected: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Hidden test cases only shown on submit (not on "Run Code")
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Sequence determines order of test case execution
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    problem: Mapped["Problem"] = relationship(back_populates="test_cases")

    __table_args__ = (Index("ix_test_cases_problem_id", "problem_id"),)


class UserProgress(Base):
    """Tracks user's progress and spaced repetition for problems."""

    __tablename__ = "user_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # No auth.users table - user_id is just a string identifier (username)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )

    # Spaced repetition fields (legacy - kept for backwards compatibility)
    times_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_solved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_mastered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_again: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Anki SM-2 algorithm fields
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    problem: Mapped["Problem"] = relationship(back_populates="user_progress")

    __table_args__ = (
        Index("ix_user_progress_user_id", "user_id"),
        Index("ix_user_progress_problem_id", "problem_id"),
        Index("ix_user_progress_next_review_date", "next_review_date"),
        Index("ix_user_progress_user_problem", "user_id", "problem_id", unique=True),
    )


class Submission(Base):
    """History of all code submissions."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )

    code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Language] = mapped_column(Enum(Language), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Test result summary (for displaying "X / Y testcases passed")
    total_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # First failed test details (NULL if all passed)
    failed_test_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failed_input: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    failed_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    failed_expected: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    failed_is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    submitted_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    problem: Mapped["Problem"] = relationship(back_populates="submissions")

    __table_args__ = (Index("ix_submissions_user_problem", "user_id", "problem_id"),)


class UserCode(Base):
    """Stores user's current code for each problem (server-side code persistence)."""

    __tablename__ = "user_code"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(Text, default="python", nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    problem: Mapped["Problem"] = relationship(back_populates="user_codes")

    __table_args__ = (
        Index("idx_user_code_user_problem", "user_id", "problem_id"),
        Index(
            "ix_user_code_unique", "user_id", "problem_id", "language", unique=True
        ),
    )


class ChatSession(Base):
    """AI chat sessions for problem-solving assistance."""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mode: Mapped[ChatMode] = mapped_column(
        Enum(ChatMode, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    problem: Mapped["Problem"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete", passive_deletes=True
    )

    __table_args__ = (
        Index("ix_chat_sessions_user_problem", "user_id", "problem_id"),
        Index("ix_chat_sessions_user_id", "user_id"),
    )


class ChatMessage(Base):
    """Messages within chat sessions."""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    code_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_results_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    __table_args__ = (Index("ix_chat_messages_session_id", "session_id"),)
