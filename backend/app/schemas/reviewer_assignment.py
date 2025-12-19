"""
Pydantic schemas for reviewer assignments
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewerAssignmentBase(BaseModel):
    """Base schema for reviewer assignment"""

    pass


class ReviewerAssignmentCreate(BaseModel):
    """Schema for assigning reviewers to a submission"""

    reviewer_ids: list[UUID] = Field(
        ..., min_length=1, description="List of reviewer user IDs to assign"
    )


class ReviewerInfo(BaseModel):
    """Schema for reviewer information"""

    id: UUID
    email: str
    role: str
    full_name: str | None = None
    assigned_at: datetime

    model_config = {"from_attributes": True}


class ReviewerAssignmentResponse(BaseModel):
    """Schema for reviewer assignment response"""

    id: UUID  # submission_id (aliased as 'id' for response)
    reviewers: list[ReviewerInfo]

    model_config = {"from_attributes": True}


class ReviewerRemoveResponse(BaseModel):
    """Schema for successful reviewer removal"""

    message: str
    submission_id: UUID
    reviewer_id: UUID
    remaining_reviewers: list[ReviewerInfo]

    model_config = {"from_attributes": True}
