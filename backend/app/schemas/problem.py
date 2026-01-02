"""Pydantic schemas for problems."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.tables import Difficulty, Language


class TestCaseSchema(BaseModel):
    """Test case schema (for responses)."""

    id: UUID
    input: dict | list  # JSON data
    expected: dict | list  # JSON data
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
    examples: dict
    created_at: datetime

    # Related data
    languages: list[ProblemLanguageSchema]
    test_cases: list[TestCaseSchema]  # Filtered to non-hidden

    model_config = {"from_attributes": True}
