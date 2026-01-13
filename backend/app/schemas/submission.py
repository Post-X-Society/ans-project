"""
Pydantic schemas for Submission API
"""

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.claim import ClaimResponse


class SubmissionUserInfo(BaseModel):
    """Schema for user information in submission response"""

    id: UUID
    email: str

    model_config = {"from_attributes": True}


class SubmissionReviewerInfo(BaseModel):
    """Schema for reviewer information in submission response"""

    id: UUID
    email: str
    role: str

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
    user_id: Optional[UUID] = None
    user: Optional[SubmissionUserInfo] = None
    content: str
    submission_type: str
    status: str
    workflow_state: str
    created_at: datetime
    updated_at: datetime
    reviewers: List[SubmissionReviewerInfo] = Field(default_factory=list)
    is_assigned_to_me: bool = False  # For reviewers to know if they're assigned
    fact_check_id: Optional[UUID] = None  # From first claim's first fact_check
    peer_review_triggered: bool = False

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
