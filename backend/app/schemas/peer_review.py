"""
Pydantic schemas for Peer Review API.

Issue #66: Backend: Peer Review API Endpoints (TDD)
EPIC #48: Multi-Tier Approval & Peer Review
ADR 0005: EFCSN Compliance Architecture

Provides schemas for:
- Peer review initiation and submission
- Peer review status/consensus checking
- Trigger configuration management
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.peer_review import ApprovalStatus
from app.models.peer_review_trigger import TriggerType

# =============================================================================
# Peer Review Initiation Schemas
# =============================================================================


class PeerReviewInitiate(BaseModel):
    """Schema for initiating peer review on a fact-check."""

    reviewer_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="List of user UUIDs to assign as peer reviewers",
    )

    @field_validator("reviewer_ids")
    @classmethod
    def reviewer_ids_not_empty(cls, v: list[UUID]) -> list[UUID]:
        """Ensure reviewer_ids is not empty."""
        if not v:
            raise ValueError("At least one reviewer must be specified")
        return v


class PeerReviewInitiateResponse(BaseModel):
    """Schema for peer review initiation response."""

    fact_check_id: UUID
    reviews_created: int = Field(..., description="Number of reviews created")
    reviews: list["PeerReviewResponse"]


# =============================================================================
# Peer Review Submission Schemas
# =============================================================================


class PeerReviewSubmit(BaseModel):
    """Schema for submitting a peer review decision."""

    approved: bool = Field(
        ...,
        description="True for approval, False for rejection",
    )
    comments: Optional[str] = Field(
        None,
        max_length=5000,
        description="Optional comments explaining the decision",
    )


class PeerReviewResponse(BaseModel):
    """Schema for individual peer review response."""

    id: UUID
    fact_check_id: UUID
    reviewer_id: UUID
    approval_status: ApprovalStatus
    comments: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Peer Review Status Schemas
# =============================================================================


class PeerReviewStatusResponse(BaseModel):
    """Schema for peer review status/consensus response."""

    fact_check_id: UUID
    consensus_reached: bool = Field(
        ..., description="True if all reviewers have submitted decisions"
    )
    approved: bool = Field(..., description="True only if all reviewers approved (unanimous)")
    total_reviews: int = Field(..., description="Total number of peer reviews")
    approved_count: int = Field(..., description="Number of approved reviews")
    rejected_count: int = Field(..., description="Number of rejected reviews")
    pending_count: int = Field(..., description="Number of pending reviews")
    needs_more_reviewers: bool = Field(..., description="True if below minimum reviewer threshold")
    reviews: list[PeerReviewResponse] = Field(
        default_factory=list, description="List of individual reviews"
    )


# =============================================================================
# Pending Reviews Schemas
# =============================================================================


class PendingReviewItem(BaseModel):
    """Schema for a pending review item."""

    id: UUID
    fact_check_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class PendingReviewsResponse(BaseModel):
    """Schema for list of pending reviews response."""

    reviewer_id: UUID
    total_count: int
    reviews: list[PendingReviewItem]


# =============================================================================
# Trigger Configuration Schemas
# =============================================================================


class TriggerUpdate(BaseModel):
    """Schema for updating a peer review trigger."""

    trigger_id: UUID = Field(..., description="UUID of the trigger to update")
    enabled: Optional[bool] = Field(None, description="Enable/disable the trigger")
    threshold_value: Optional[dict[str, Any]] = Field(
        None, description="Trigger configuration (keywords, thresholds, etc.)"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Human-readable description"
    )


class TriggerResponse(BaseModel):
    """Schema for trigger response."""

    id: UUID
    trigger_type: TriggerType
    enabled: bool
    threshold_value: Optional[dict[str, Any]]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TriggerListResponse(BaseModel):
    """Schema for list of triggers response."""

    total_count: int
    triggers: list[TriggerResponse]


# Rebuild models to resolve forward references
PeerReviewInitiateResponse.model_rebuild()
