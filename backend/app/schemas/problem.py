"""Pydantic schemas for problems."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.db.tables import Difficulty, Language


class ProblemExampleSchema(BaseModel):
    """Example schema for problem examples."""

    input: str
    output: str
    explanation: str | None = None


class TestCaseSchema(BaseModel):
    """Test case schema (for responses)."""

    id: UUID
    input: dict | list  # JSON data (usually array of args)
    expected: dict | list | int | float | str | bool | None  # JSON data (any valid JSON value)
    is_hidden: bool
    sequence: int

    model_config = {"from_attributes": True}


class ProblemLanguageSchema(BaseModel):
    """Problem language-specific data."""

    id: UUID
    language: Language
    starter_code: str
    function_signature: dict

    model_config = {"from_attributes": True}


class ProblemSchema(BaseModel):
    """Problem schema for list views."""

    id: UUID
    title: str
    slug: str
    difficulty: Difficulty
    pattern: str
    sequence_number: int

    model_config = {"from_attributes": True}


class ProblemDetailSchema(BaseModel):
    """
    Detailed problem schema with all related data.

    Includes test cases (visible only), language configs, etc.
    """

    id: UUID
    title: str
    slug: str
    description: str
    difficulty: Difficulty
    pattern: str
    sequence_number: int
    constraints: list[str]
    examples: list[ProblemExampleSchema]
    created_at: datetime

    # Related data
    languages: list[ProblemLanguageSchema]
    test_cases: list[TestCaseSchema]  # Filtered to non-hidden

    # User's saved code (if any) - populated from user_code table
    user_code: str | None = None

    model_config = {"from_attributes": True}

    @field_validator("examples", mode="before")
    @classmethod
    def unwrap_examples(cls, v):
        """Unwrap examples from JSONB dict structure."""
        if isinstance(v, dict) and "examples" in v:
            return v["examples"]
        return v
