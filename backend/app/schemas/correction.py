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


# =============================================================================
# Issue #77: Correction Application Schemas
# =============================================================================


class CorrectionReviewRequest(BaseModel):
    """Schema for reviewing (accepting/rejecting) a correction request.

    Admin-only endpoint for processing pending corrections.
    """

    resolution_notes: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Explanation of the review decision",
    )

    @field_validator("resolution_notes")
    @classmethod
    def resolution_notes_not_empty_whitespace(cls, v: str) -> str:
        """Ensure resolution_notes is not just whitespace."""
        stripped: str = v.strip()
        if not stripped:
            raise ValueError("Resolution notes cannot be empty or only whitespace")
        if len(stripped) < 10:
            raise ValueError("Resolution notes must be at least 10 characters")
        return stripped


class CorrectionApplyRequest(BaseModel):
    """Schema for applying an accepted correction to a fact-check.

    Admin-only endpoint for applying corrections after acceptance.
    """

    changes: dict[str, str | int | float | list[str] | None] = Field(
        ...,
        description="Dictionary of field changes to apply to the fact-check. "
        "Valid fields: verdict, confidence, reasoning, sources",
    )
    changes_summary: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Human-readable summary of the changes being applied",
    )

    @field_validator("changes")
    @classmethod
    def changes_not_empty(
        cls, v: dict[str, str | int | float | list[str] | None]
    ) -> dict[str, str | int | float | list[str] | None]:
        """Ensure changes dict is not empty."""
        if not v:
            raise ValueError("Changes must include at least one field to update")
        # Validate field names
        valid_fields: set[str] = {
            "verdict",
            "confidence",
            "reasoning",
            "sources",
            "correction_notice",
        }
        for field in v.keys():
            if field not in valid_fields:
                raise ValueError(
                    f"Invalid field '{field}'. Valid fields: {', '.join(valid_fields)}"
                )
        return v

    @field_validator("changes_summary")
    @classmethod
    def changes_summary_not_empty_whitespace(cls, v: str) -> str:
        """Ensure changes_summary is not just whitespace."""
        stripped: str = v.strip()
        if not stripped:
            raise ValueError("Changes summary cannot be empty or only whitespace")
        if len(stripped) < 10:
            raise ValueError("Changes summary must be at least 10 characters")
        return stripped


class CorrectionApplicationResponse(BaseModel):
    """Schema for correction application response.

    Returned after successfully applying a correction.
    """

    id: UUID
    correction_id: UUID
    applied_by_id: UUID
    version: int
    applied_at: datetime
    changes_summary: str
    previous_content: dict[str, str | int | float | list[str] | None]
    new_content: dict[str, str | int | float | list[str] | None]
    is_current: bool

    model_config = {"from_attributes": True}


class CorrectionHistoryResponse(BaseModel):
    """Schema for correction history response.

    Returns the full version history of corrections applied to a fact-check.
    """

    fact_check_id: UUID
    applications: list[CorrectionApplicationResponse]
    total_versions: int


# =============================================================================
# Issue #78: Additional Schemas for Correction API Endpoints
# =============================================================================


class CorrectionAllListResponse(BaseModel):
    """Schema for listing all corrections (admin endpoint).

    Includes pagination metadata for handling large result sets.
    Issue #78: Backend Correction API Endpoints
    """

    corrections: list[CorrectionResponse]
    total_count: int
    limit: int = Field(
        default=50,
        description="Maximum number of corrections returned per page",
    )
    offset: int = Field(
        default=0,
        description="Number of corrections skipped",
    )


class PublicLogCorrectionResponse(BaseModel):
    """Schema for correction in public log (privacy-aware).

    This schema omits sensitive information like requester_email
    for GDPR compliance and privacy protection.

    Issue #78: Backend Correction API Endpoints
    EFCSN Requirement: Public corrections log
    """

    id: UUID
    fact_check_id: UUID
    correction_type: CorrectionType
    request_details: str
    # requester_email intentionally omitted for privacy
    status: CorrectionStatus
    reviewed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublicLogListResponse(BaseModel):
    """Schema for public corrections log response.

    Returns only accepted substantial and update corrections
    for EFCSN transparency requirements.

    Issue #78: Backend Correction API Endpoints
    EFCSN Requirement: Public corrections log (last 2 years minimum)
    """

    corrections: list[PublicLogCorrectionResponse]
    total_count: int
