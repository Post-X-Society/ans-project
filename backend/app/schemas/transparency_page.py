"""
Pydantic schemas for Transparency Page API.

Issue #83: Backend: Transparency Page Service with Versioning
EPIC #51: Transparency & Methodology Pages
ADR 0005: EFCSN Compliance Architecture
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TransparencyPageBase(BaseModel):
    """Base schema for transparency page data."""

    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly identifier")
    title: dict[str, str] = Field(..., description="Multilingual title as {lang_code: title}")
    content: dict[str, str] = Field(
        ..., description="Multilingual markdown content as {lang_code: content}"
    )


class TransparencyPageCreate(TransparencyPageBase):
    """Schema for creating a new transparency page."""

    pass


class TransparencyPageUpdate(BaseModel):
    """Schema for updating a transparency page."""

    title: Optional[dict[str, str]] = Field(
        None, description="Multilingual title as {lang_code: title}"
    )
    content: Optional[dict[str, str]] = Field(
        None, description="Multilingual markdown content as {lang_code: content}"
    )
    change_summary: str = Field(
        ..., min_length=1, max_length=500, description="Description of changes made"
    )


class TransparencyPageResponse(BaseModel):
    """Schema for transparency page response."""

    id: UUID
    slug: str
    title: dict[str, Any]
    content: dict[str, Any]
    version: int
    last_reviewed: Optional[datetime] = None
    next_review_due: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransparencyPageSummary(BaseModel):
    """Schema for transparency page summary (listing)."""

    id: UUID
    slug: str
    title: dict[str, Any]
    version: int
    last_reviewed: Optional[datetime] = None
    next_review_due: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransparencyPageVersionResponse(BaseModel):
    """Schema for transparency page version response."""

    id: UUID
    page_id: UUID
    version: int
    title: dict[str, Any]
    content: dict[str, Any]
    changed_by_id: UUID
    change_summary: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransparencyPageDiff(BaseModel):
    """Schema for diff between two page versions."""

    slug: str
    from_version: int
    to_version: int
    diff: dict[str, Any] = Field(..., description="Diff data containing changes between versions")
    language: Optional[str] = Field(None, description="Language filter applied to diff")


class TransparencyPageListResponse(BaseModel):
    """Schema for paginated list of transparency pages."""

    items: list[TransparencyPageSummary]
    total: int


class ReviewDueResponse(BaseModel):
    """Schema for pages due for annual review."""

    pages: list[TransparencyPageSummary]
    total_due: int
