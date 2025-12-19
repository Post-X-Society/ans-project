"""
Pydantic schemas for Submission API
"""

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.claim import ClaimResponse


class UserBasic(BaseModel):
    """Basic user information for embedding in responses"""

    id: UUID
    email: str

    model_config = {"from_attributes": True}


class SpotlightContentBasic(BaseModel):
    """Basic spotlight content information for embedding in responses"""

    spotlight_id: str
    thumbnail_url: str
    creator_name: Optional[str] = None
    creator_username: Optional[str] = None
    view_count: Optional[int] = None
    duration_ms: Optional[int] = None

    model_config = {"from_attributes": True}


class SubmissionCreate(BaseModel):
    """Schema for creating a new submission"""

    content: str = Field(..., min_length=10, max_length=5000, description="Content to fact-check")
    type: Literal["text", "image", "url"] = Field(..., description="Type of submission")

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Validate content is not just whitespace"""
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace")
        return v.strip()


class SubmissionResponse(BaseModel):
    """Schema for submission response"""

    id: UUID
    user_id: Optional[UUID] = None  # Optional for now (no auth yet)
    content: str
    submission_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    user: Optional[UserBasic] = None
    spotlight_content: Optional[SpotlightContentBasic] = None
    reviewers: List[UserBasic] = Field(default_factory=list)

    model_config = {"from_attributes": True}  # Allow ORM models


class SubmissionWithClaimsResponse(SubmissionResponse):
    """Schema for submission response with extracted claims"""

    claims: List[ClaimResponse] = Field(default_factory=list)
    extracted_claims_count: int = Field(default=0)

    model_config = {"from_attributes": True}


class SubmissionListResponse(BaseModel):
    """Schema for paginated list of submissions"""

    items: List[SubmissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
