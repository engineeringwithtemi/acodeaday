"""SQLAlchemy database models for acodeaday."""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, Integer, String, Text, func
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


class ProblemLanguage(Base):
    """Language-specific code and solutions for problems."""

    __tablename__ = "problem_languages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "python", "javascript", etc.
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

    # Spaced repetition fields
    times_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_solved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_mastered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_again: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

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
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    problem: Mapped["Problem"] = relationship(back_populates="submissions")

    __table_args__ = (Index("ix_submissions_user_problem", "user_id", "problem_id"),)
