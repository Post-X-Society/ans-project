"""
Pydantic schemas for Analytics Service API.

Issue #88: Backend Analytics Service & EFCSN Compliance Metrics (TDD)
EPIC #52: Analytics & Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

Provides schemas for:
- Monthly fact-check publication metrics
- Time-to-publication analytics
- Rating distribution statistics
- Source quality metrics
- Correction rate tracking
- EFCSN compliance checklist
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MonthlyFactCheckCount(BaseModel):
    """Monthly fact-check publication count for EFCSN compliance.

    EFCSN requires minimum 4 fact-checks published per month.
    """

    year: int = Field(..., description="Year of the count")
    month: int = Field(..., ge=1, le=12, description="Month of the count (1-12)")
    count: int = Field(..., ge=0, description="Number of fact-checks published")
    meets_efcsn_minimum: bool = Field(
        ...,
        description="Whether the count meets EFCSN minimum (4+ per month)",
    )


class MonthlyFactCheckCountResponse(BaseModel):
    """Response containing monthly fact-check counts."""

    months: list[MonthlyFactCheckCount] = Field(
        ..., description="List of monthly fact-check counts"
    )
    total_count: int = Field(..., ge=0, description="Total fact-checks in period")
    average_per_month: float = Field(..., ge=0, description="Average fact-checks per month")


class TimeToPublicationMetrics(BaseModel):
    """Time-to-publication metrics for fact-checks.

    Measures the time from submission to published fact-check.
    """

    average_hours: float = Field(..., ge=0, description="Average time to publication in hours")
    median_hours: float = Field(..., ge=0, description="Median time to publication in hours")
    min_hours: float = Field(..., ge=0, description="Minimum time to publication in hours")
    max_hours: float = Field(..., ge=0, description="Maximum time to publication in hours")
    total_published: int = Field(
        ..., ge=0, description="Total number of published fact-checks in period"
    )


class RatingDistributionItem(BaseModel):
    """Single rating distribution item."""

    rating: str = Field(..., description="Rating value (e.g., 'true', 'false')")
    count: int = Field(..., ge=0, description="Number of fact-checks with this rating")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of total fact-checks")


class RatingDistributionResponse(BaseModel):
    """Response containing rating distribution statistics."""

    ratings: list[RatingDistributionItem] = Field(..., description="Distribution of ratings")
    total_count: int = Field(..., ge=0, description="Total fact-checks analyzed")
    period_start: Optional[datetime] = Field(None, description="Start of analysis period")
    period_end: Optional[datetime] = Field(None, description="End of analysis period")


class SourceQualityMetrics(BaseModel):
    """Source quality metrics for EFCSN compliance.

    EFCSN requires minimum 2 sources per fact-check.
    """

    average_sources_per_fact_check: float = Field(
        ..., ge=0, description="Average number of sources per fact-check"
    )
    average_credibility_score: float = Field(
        ..., ge=0, le=5, description="Average source credibility score (1-5)"
    )
    total_sources: int = Field(..., ge=0, description="Total sources in database")
    sources_by_type: dict[str, int] = Field(
        ..., description="Count of sources by type (primary, secondary, etc.)"
    )
    sources_by_relevance: dict[str, int] = Field(
        ..., description="Count of sources by relevance (supports, contradicts, etc.)"
    )
    fact_checks_meeting_minimum: int = Field(
        ..., ge=0, description="Fact-checks with 2+ sources (EFCSN minimum)"
    )
    fact_checks_below_minimum: int = Field(
        ..., ge=0, description="Fact-checks with fewer than 2 sources"
    )


class CorrectionRateMetrics(BaseModel):
    """Correction rate metrics for quality tracking."""

    total_fact_checks: int = Field(..., ge=0, description="Total published fact-checks")
    total_corrections: int = Field(..., ge=0, description="Total correction requests")
    corrections_accepted: int = Field(..., ge=0, description="Accepted correction requests")
    corrections_rejected: int = Field(..., ge=0, description="Rejected correction requests")
    corrections_pending: int = Field(..., ge=0, description="Pending correction requests")
    correction_rate: float = Field(
        ..., ge=0, description="Correction rate (corrections per fact-check)"
    )
    corrections_by_type: dict[str, int] = Field(
        ..., description="Count of corrections by type (minor, update, substantial)"
    )


class EFCSNComplianceChecklistItem(BaseModel):
    """Single EFCSN compliance checklist item."""

    requirement: str = Field(..., description="EFCSN requirement description")
    status: str = Field(..., description="Status: 'compliant', 'non_compliant', or 'warning'")
    details: str = Field(..., description="Details about compliance status")
    value: Optional[str] = Field(None, description="Current value (e.g., '5' for fact-check count)")
    threshold: Optional[str] = Field(None, description="Required threshold (e.g., '4' for minimum)")


class EFCSNComplianceResponse(BaseModel):
    """EFCSN compliance checklist response.

    Real-time monitoring of EFCSN Code of Standards compliance.
    """

    overall_status: str = Field(
        ...,
        description="Overall compliance: 'compliant', 'non_compliant', or 'at_risk'",
    )
    checklist: list[EFCSNComplianceChecklistItem] = Field(
        ..., description="Individual compliance items"
    )
    last_checked: datetime = Field(..., description="Timestamp of compliance check")
    compliance_score: float = Field(..., ge=0, le=100, description="Compliance score percentage")


class AnalyticsDashboardResponse(BaseModel):
    """Complete analytics dashboard response combining all metrics."""

    monthly_fact_checks: MonthlyFactCheckCountResponse
    time_to_publication: TimeToPublicationMetrics
    rating_distribution: RatingDistributionResponse
    source_quality: SourceQualityMetrics
    correction_rate: CorrectionRateMetrics
    efcsn_compliance: EFCSNComplianceResponse
    generated_at: datetime = Field(..., description="Timestamp when dashboard was generated")
