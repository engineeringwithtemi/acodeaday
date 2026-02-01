"""Pydantic schemas for diagram generation."""

import enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NodeShape(str, enum.Enum):
    """Constrained set of renderable node shapes.

    The LLM can ONLY pick from these values — anything else fails Pydantic validation.
    """

    RECT = "rect"
    DIAMOND = "diamond"
    STADIUM = "stadium"
    SUBROUTINE = "subroutine"
    CIRCLE = "circle"


class DiagramNode(BaseModel):
    """A node in the flowchart diagram."""

    id: str = Field(..., description="Unique node identifier (e.g. n0, n1)")
    label: str = Field(..., description="Human-readable pseudocode label")
    shape: NodeShape = Field(
        ...,
        description="Node shape: rect=statement, diamond=condition, stadium=start/end, subroutine=function, circle=connector",
    )


class DiagramEdge(BaseModel):
    """An edge connecting two nodes in the flowchart."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    from_node: str = Field(..., alias="from", description="Source node ID")
    to_node: str = Field(..., alias="to", description="Target node ID")
    label: str | None = Field(default=None, description="Optional edge label (e.g. Yes, No, done)")


class PseudocodeDiagramRequest(BaseModel):
    """Request to generate a pseudocode flowchart diagram."""

    code: str = Field(..., min_length=1, description="User's code to translate to pseudocode")
    language: Literal["python", "javascript"] = Field(
        ..., description="Programming language"
    )


class PseudocodeDiagramResponse(BaseModel):
    """Response containing the pseudocode flowchart data."""

    nodes: list[DiagramNode]
    edges: list[DiagramEdge]
