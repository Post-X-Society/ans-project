"""
Pydantic schemas for Correction Service API.

Issue #76: Backend: Correction Request Service (TDD)
EPIC #50: Corrections & Complaints System
ADR 0005: EFCSN Compliance Architecture

Provides schemas for:
- Public correction request submission (no auth required)
- Correction responses with SLA deadlines
- Correction list and filtering
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.correction import CorrectionStatus, CorrectionType


class CorrectionCreate(BaseModel):
    """Schema for creating a new correction request (public endpoint).

    This is a public-facing endpoint that does not require authentication.
    Users can submit correction requests for published fact-checks.
    """

    fact_check_id: UUID = Field(
        ...,
        description="UUID of the fact-check to request correction for",
    )
    correction_type: CorrectionType = Field(
        ...,
        description="Type of correction: minor, update, or substantial",
    )
    request_details: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed description of the correction request",
    )
    requester_email: Optional[EmailStr] = Field(
        None,
        description="Optional email for receiving acknowledgment and updates",
    )

    @field_validator("request_details")
    @classmethod
    def request_details_not_empty_whitespace(cls, v: str) -> str:
        """Ensure request_details is not just whitespace."""
        stripped: str = v.strip()
        if not stripped:
            raise ValueError("Request details cannot be empty or only whitespace")
        if len(stripped) < 10:
            raise ValueError("Request details must be at least 10 characters")
        return stripped


class CorrectionResponse(BaseModel):
    """Schema for correction response.

    Includes SLA deadline for EFCSN compliance tracking.
    """

    id: UUID
    fact_check_id: UUID
    correction_type: CorrectionType
    request_details: str
    requester_email: Optional[str] = None
    status: CorrectionStatus
    reviewed_by_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    sla_deadline: Optional[datetime] = Field(
        None,
        description="Deadline for processing this correction (7-day SLA)",
    )
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CorrectionListResponse(BaseModel):
    """Schema for list of corrections response."""

    fact_check_id: Optional[UUID] = Field(
        None,
        description="Fact-check ID if filtered, None for global list",
    )
    corrections: list[CorrectionResponse]
    total_count: int


class CorrectionPendingListResponse(BaseModel):
    """Schema for list of pending corrections (admin triage)."""

    corrections: list[CorrectionResponse]
    total_count: int
    overdue_count: int = Field(
        0,
        description="Number of corrections past their SLA deadline",
    )


class CorrectionSubmitResponse(BaseModel):
    """Schema for correction submission confirmation.

    Returned after successfully submitting a correction request.
    """

    id: UUID
    fact_check_id: UUID
    correction_type: CorrectionType
    status: CorrectionStatus
    requester_email: Optional[str] = None
    sla_deadline: Optional[datetime] = Field(
        None,
        description="Expected processing deadline (7-day SLA)",
    )
    acknowledgment_sent: bool = Field(
        False,
        description="Whether acknowledgment email was sent",
    )
    created_at: datetime

    model_config = {"from_attributes": True}


class CorrectionFilterParams(BaseModel):
    """Schema for filtering corrections in queries."""

    correction_type: Optional[CorrectionType] = Field(
        None,
        description="Filter by correction type",
    )
    status: Optional[CorrectionStatus] = Field(
        None,
        description="Filter by status",
    )
    include_overdue: Optional[bool] = Field(
        None,
        description="Filter to show only overdue corrections",
    )
