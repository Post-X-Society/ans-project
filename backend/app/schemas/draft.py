"""
Pydantic schemas for Fact-Check Draft Storage API.

Issue #123: Backend: Fact-Check Draft Storage API (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine
ADR 0005: EFCSN Compliance Architecture

Draft content structure for storing reviewer work-in-progress fact-checks.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DraftContent(BaseModel):
    """
    Schema for draft content stored in the fact_check.draft_content JSONB column.

    This structure stores reviewer work-in-progress content with auto-save support.
    """

    claim_summary: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Brief summary of the claim being fact-checked",
    )
    analysis: Optional[str] = Field(
        default=None,
        description="HTML-formatted analysis of the claim",
    )
    verdict: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Draft verdict (true, false, partly_false, etc.)",
    )
    justification: Optional[str] = Field(
        default=None,
        description="Detailed explanation for the verdict (min 50 chars when provided)",
    )
    sources_cited: list[str] = Field(
        default_factory=list,
        description="List of source URLs/references cited in the fact-check",
    )
    internal_notes: Optional[str] = Field(
        default=None,
        description="Internal notes visible only to reviewers and admins",
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Draft version number, incremented on each save",
    )
    last_edited_by: Optional[UUID] = Field(
        default=None,
        description="UUID of the user who last edited the draft",
    )

    @field_validator("justification")
    @classmethod
    def validate_justification_length(cls, v: Optional[str]) -> Optional[str]:
        """Validate justification has minimum 50 characters if provided."""
        if v is not None:
            stripped = v.strip()
            if stripped and len(stripped) < 50:
                raise ValueError("Justification must be at least 50 characters when provided")
            return stripped
        return v

    @field_validator("sources_cited")
    @classmethod
    def validate_sources_format(cls, v: list[str]) -> list[str]:
        """Validate and clean source URLs."""
        return [source.strip() for source in v if source.strip()]


class DraftUpdate(BaseModel):
    """
    Schema for updating/saving draft content via PATCH endpoint.

    All fields are optional to support partial updates.
    """

    claim_summary: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Brief summary of the claim being fact-checked",
    )
    analysis: Optional[str] = Field(
        default=None,
        description="HTML-formatted analysis of the claim",
    )
    verdict: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Draft verdict (true, false, partly_false, etc.)",
    )
    justification: Optional[str] = Field(
        default=None,
        description="Detailed explanation for the verdict (min 50 chars when provided)",
    )
    sources_cited: Optional[list[str]] = Field(
        default=None,
        description="List of source URLs/references cited in the fact-check",
    )
    internal_notes: Optional[str] = Field(
        default=None,
        description="Internal notes visible only to reviewers and admins",
    )

    @field_validator("justification")
    @classmethod
    def validate_justification_length(cls, v: Optional[str]) -> Optional[str]:
        """Validate justification has minimum 50 characters if provided."""
        if v is not None:
            stripped = v.strip()
            if stripped and len(stripped) < 50:
                raise ValueError("Justification must be at least 50 characters when provided")
            return stripped
        return v

    @field_validator("sources_cited")
    @classmethod
    def validate_sources_format(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate and clean source URLs."""
        if v is not None:
            return [source.strip() for source in v if source.strip()]
        return v


class DraftResponse(BaseModel):
    """Schema for draft response returned by GET and PATCH endpoints."""

    fact_check_id: UUID
    draft_content: Optional[DraftContent] = Field(
        default=None,
        description="The draft content, null if no draft exists",
    )
    draft_updated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last draft update",
    )
    has_draft: bool = Field(
        description="Whether the fact-check has a saved draft",
    )

    model_config = {"from_attributes": True}
