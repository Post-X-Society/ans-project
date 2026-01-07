"""
Pydantic schemas for Transparency Reports API.

Issue #89: Backend - Automated Monthly Transparency Reports (TDD)
EPIC #52: Analytics & EFCSN Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

Provides schemas for:
- Transparency report generation requests
- Report response models
- Publication status updates
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TransparencyReportGenerate(BaseModel):
    """Request schema for generating a transparency report."""

    year: int = Field(..., ge=2020, le=2100, description="Report year")
    month: int = Field(..., ge=1, le=12, description="Report month (1-12)")
    force_regenerate: bool = Field(
        default=False,
        description="If True, regenerate even if report exists",
    )


class TransparencyReportBase(BaseModel):
    """Base schema for transparency report."""

    id: str = Field(..., description="Report UUID")
    year: int = Field(..., description="Report year")
    month: int = Field(..., description="Report month")
    title: dict[str, str] = Field(..., description="Multilingual title (en, nl)")
    summary: dict[str, str] = Field(..., description="Multilingual summary (en, nl)")
    is_published: bool = Field(..., description="Whether report is publicly visible")
    generated_at: datetime = Field(..., description="When report was generated")
    published_at: Optional[datetime] = Field(None, description="When report was published")
    created_at: datetime = Field(..., description="Record creation timestamp")

    model_config = {"from_attributes": True}


class TransparencyReportResponse(TransparencyReportBase):
    """Full response schema for transparency report with data."""

    report_data: dict[str, Any] = Field(..., description="Full report metrics data")


class TransparencyReportListItem(TransparencyReportBase):
    """List item schema (without full report_data for efficiency)."""

    pass


class TransparencyReportListResponse(BaseModel):
    """Response schema for listing reports."""

    reports: list[TransparencyReportListItem] = Field(
        ..., description="List of transparency reports"
    )
    total: int = Field(..., ge=0, description="Total number of reports")


class TransparencyReportEmailResult(BaseModel):
    """Response schema for email sending result."""

    emails_queued: int = Field(..., ge=0, description="Number of emails queued")
    pdf_generated: bool = Field(..., description="Whether PDF was generated")
    csv_generated: bool = Field(..., description="Whether CSV was generated")
    report_id: str = Field(..., description="Report UUID")


class TriggerReportGeneration(BaseModel):
    """Request to manually trigger report generation via Celery."""

    year: Optional[int] = Field(
        None,
        ge=2020,
        le=2100,
        description="Report year (defaults to previous month)",
    )
    month: Optional[int] = Field(
        None,
        ge=1,
        le=12,
        description="Report month (defaults to previous month)",
    )
    auto_publish: bool = Field(
        default=False,
        description="Automatically publish the report after generation",
    )
    notify_admins: bool = Field(
        default=True,
        description="Send email notifications to admins",
    )


class TriggerReportResponse(BaseModel):
    """Response for triggered report generation."""

    task_id: str = Field(..., description="Celery task ID for tracking")
    message: str = Field(..., description="Status message")
