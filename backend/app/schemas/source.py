"""
Pydantic schemas for Source Service API.

Issue #70: Backend: Source Management Service (TDD)
EPIC #49: Evidence & Source Management
ADR 0005: EFCSN Compliance Architecture

Provides schemas for:
- Source creation and updates
- Source responses with citation numbering
- Source validation for publishing
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.source import SourceRelevance, SourceType


class SourceCreate(BaseModel):
    """Schema for creating a new source."""

    fact_check_id: UUID = Field(..., description="UUID of the fact-check this source belongs to")
    source_type: SourceType = Field(
        ..., description="Type of source (primary, secondary, expert, etc.)"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Title or description of the source",
    )
    url: Optional[str] = Field(None, description="URL to the source (if available)")
    publication_date: Optional[date] = Field(None, description="Date the source was published")
    access_date: date = Field(..., description="Date when the source was accessed")
    credibility_score: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Credibility rating from 1 (low) to 5 (high)",
    )
    relevance: Optional[SourceRelevance] = Field(
        None,
        description="How the source relates to the claim (supports, contradicts, contextualizes)",
    )
    archived_url: Optional[str] = Field(
        None, description="Archived URL (e.g., Wayback Machine snapshot)"
    )
    notes: Optional[str] = Field(None, description="Additional notes about the source")

    @field_validator("title")
    @classmethod
    def title_not_empty_whitespace(cls, v: str) -> str:
        """Ensure title is not just whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or only whitespace")
        return stripped


class SourceUpdate(BaseModel):
    """Schema for updating an existing source.

    All fields are optional - only provided fields will be updated.
    """

    source_type: Optional[SourceType] = Field(None, description="Type of source")
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Title or description of the source",
    )
    url: Optional[str] = Field(None, description="URL to the source")
    publication_date: Optional[date] = Field(None, description="Date the source was published")
    access_date: Optional[date] = Field(None, description="Date when the source was accessed")
    credibility_score: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Credibility rating from 1 (low) to 5 (high)",
    )
    relevance: Optional[SourceRelevance] = Field(
        None, description="How the source relates to the claim"
    )
    archived_url: Optional[str] = Field(None, description="Archived URL")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("title")
    @classmethod
    def title_not_empty_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Ensure title is not just whitespace if provided."""
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Title cannot be empty or only whitespace")
            return stripped
        return v


class SourceResponse(BaseModel):
    """Schema for source response."""

    id: UUID
    fact_check_id: UUID
    source_type: SourceType
    title: str
    url: Optional[str]
    publication_date: Optional[date]
    access_date: date
    credibility_score: Optional[int]
    relevance: Optional[SourceRelevance]
    archived_url: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceWithCitationResponse(BaseModel):
    """Schema for source with citation number."""

    source: SourceResponse
    citation_number: int = Field(
        ..., ge=1, description="Citation number for this source ([1], [2], etc.)"
    )
    citation_string: str = Field(..., description="Formatted citation string (e.g., '[1]')")


class SourceListResponse(BaseModel):
    """Schema for list of sources response."""

    fact_check_id: UUID
    sources: list[SourceResponse]
    total_count: int


class SourcesWithCitationsResponse(BaseModel):
    """Schema for list of sources with citations response."""

    fact_check_id: UUID
    sources: list[SourceWithCitationResponse]
    total_count: int


class SourceValidationResponse(BaseModel):
    """Schema for source validation result."""

    fact_check_id: UUID
    is_valid: bool = Field(
        ..., description="Whether the fact-check meets minimum source requirements"
    )
    source_count: int = Field(..., description="Current number of sources")
    minimum_required: int = Field(..., description="Minimum number of sources required (2)")
    message: str = Field(..., description="Validation message")


class SourceCredibilityResponse(BaseModel):
    """Schema for source credibility summary."""

    fact_check_id: UUID
    total_sources: int
    sources_with_scores: int
    average_credibility: Optional[float] = Field(
        None, description="Average credibility score (1-5), None if no scores"
    )
