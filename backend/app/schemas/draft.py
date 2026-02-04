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

from pydantic import BaseModel, Field


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

    # Note: No validators here - DraftContent is used for reading stored data
    # Validation only happens on DraftUpdate (when saving)


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

    # Note: No strict validators on drafts - this is work-in-progress content
    # Validation happens at the "Submit for Review" stage, not during auto-save


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
