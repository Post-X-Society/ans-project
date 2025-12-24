"""
Pydantic schemas for Rating Service API.

Issue #58: Backend: Rating System Service (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine
ADR 0005: EFCSN Compliance Architecture
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FactCheckRatingValue(str, Enum):
    """
    EFCSN-compliant rating values for fact-checks.

    These values align with the European Fact-Checking Standards Network
    Code of Standards requirements for transparent rating systems.
    """

    TRUE = "true"  # Completely accurate
    PARTLY_FALSE = "partly_false"  # Mix of true and false
    FALSE = "false"  # Completely inaccurate
    MISSING_CONTEXT = "missing_context"  # True but misleading
    ALTERED = "altered"  # Digitally manipulated
    SATIRE = "satire"  # Satirical content
    UNVERIFIABLE = "unverifiable"  # Cannot be proven


class RatingCreate(BaseModel):
    """Schema for creating/assigning a new rating to a fact-check."""

    rating: FactCheckRatingValue = Field(
        ..., description="The rating value to assign to the fact-check"
    )
    justification: str = Field(
        ...,
        min_length=50,
        description="Detailed explanation for the rating (minimum 50 characters)",
    )

    @field_validator("justification")
    @classmethod
    def justification_not_empty_whitespace(cls, v: str) -> str:
        """Ensure justification is not just whitespace."""
        stripped = v.strip()
        if len(stripped) < 50:
            raise ValueError("Justification must contain at least 50 non-whitespace characters")
        return stripped


class RatingResponse(BaseModel):
    """Schema for rating response."""

    id: UUID
    fact_check_id: UUID
    assigned_by_id: UUID
    rating: str
    justification: str
    version: int
    is_current: bool
    assigned_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RatingHistoryResponse(BaseModel):
    """Schema for rating history response."""

    fact_check_id: UUID
    ratings: list[RatingResponse]
    total_versions: int


class CurrentRatingResponse(BaseModel):
    """Schema for current rating response."""

    fact_check_id: UUID
    rating: Optional[RatingResponse] = None
    has_rating: bool = Field(..., description="Whether the fact-check has a current rating")
