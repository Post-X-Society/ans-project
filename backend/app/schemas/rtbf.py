"""
Pydantic schemas for Right to be Forgotten (RTBF) workflow

Issue #92: Backend: Right to be Forgotten Workflow (TDD)
Part of EPIC #53: GDPR & Data Retention Compliance
"""

from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RTBFRequestCreate(BaseModel):
    """Schema for creating a new RTBF request"""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Reason for requesting data deletion",
    )
    date_of_birth: Optional[date] = Field(
        None,
        description="Date of birth for minor detection (optional)",
    )

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        """Validate that reason is not just whitespace"""
        if not v.strip():
            raise ValueError("Reason cannot be empty")
        return v.strip()


class RTBFRequestResponse(BaseModel):
    """Schema for RTBF request response"""

    id: UUID
    user_id: UUID
    reason: str
    status: str
    requester_date_of_birth: Optional[date] = None
    notification_email: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    deletion_summary: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class RTBFRequestListResponse(BaseModel):
    """Schema for listing RTBF requests"""

    items: list["RTBFRequestResponse"]
    total: int
    pending_count: int
    processing_count: int

    model_config = {"from_attributes": True}


class RTBFRequestRejectInput(BaseModel):
    """Schema for rejecting an RTBF request"""

    rejection_reason: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Reason for rejecting the request",
    )


class RTBFRequestProcessResult(BaseModel):
    """Schema for RTBF request processing result"""

    request_id: UUID
    status: str
    auto_approved: bool = False
    reason: Optional[str] = None
    user_anonymized: bool = False
    submissions_deleted: int = 0
    submissions_anonymized: int = 0
    deletion_summary: Optional[dict[str, Any]] = None


class DataExportRequest(BaseModel):
    """Schema for requesting data export (GDPR Article 20)"""

    include_submissions: bool = Field(
        True,
        description="Include user's submissions in export",
    )
    include_activity_logs: bool = Field(
        False,
        description="Include user's activity logs in export",
    )


class DataExportResponse(BaseModel):
    """Schema for data export response"""

    user: dict[str, Any]
    submissions: list[dict[str, Any]]
    export_date: datetime
    format_version: str = "1.0"


class UserDataSummary(BaseModel):
    """Schema for summarizing user's data before deletion"""

    user_id: UUID
    email: str
    submissions_count: int
    published_submissions_count: int
    has_active_fact_checks: bool
    can_be_deleted: bool
    deletion_restrictions: list[str] = Field(default_factory=list)


# Update forward references
RTBFRequestListResponse.model_rebuild()
