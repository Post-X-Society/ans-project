"""
Analytics API Endpoints for EFCSN compliance metrics and dashboard.

Issue #88: Backend Analytics Service & EFCSN Compliance Metrics (TDD)
EPIC #52: Analytics & Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- GET /analytics/compliance - EFCSN compliance checklist (admin only)
- GET /analytics/dashboard - Complete analytics dashboard (admin only)
- GET /analytics/monthly-fact-checks - Monthly publication counts (admin only)
- GET /analytics/rating-distribution - Rating statistics (admin only)
- GET /analytics/source-quality - Source quality metrics (admin only)
- GET /analytics/correction-rate - Correction rate metrics (admin only)
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsDashboardResponse,
    CorrectionRateMetrics,
    EFCSNComplianceChecklistItem,
    EFCSNComplianceResponse,
    MonthlyFactCheckCount,
    MonthlyFactCheckCountResponse,
    RatingDistributionItem,
    RatingDistributionResponse,
    SourceQualityMetrics,
    TimeToPublicationMetrics,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


# =============================================================================
# EFCSN Compliance Endpoint
# =============================================================================


@router.get(
    "/analytics/compliance",
    response_model=EFCSNComplianceResponse,
    tags=["analytics"],
    summary="Get EFCSN compliance checklist",
    description="Get real-time EFCSN compliance status and checklist. Admin only.",
)
async def get_efcsn_compliance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> EFCSNComplianceResponse:
    """
    Get EFCSN compliance checklist with real-time status.

    Checks:
    - Monthly fact-check minimum (4+ per month)
    - Source documentation (2+ sources per fact-check)
    - Corrections policy availability

    Admin only.
    """
    service: AnalyticsService = AnalyticsService(db)
    result: dict[str, Any] = await service.get_efcsn_compliance()

    # Convert checklist items to Pydantic models
    checklist_items: list[EFCSNComplianceChecklistItem] = [
        EFCSNComplianceChecklistItem(
            requirement=item["requirement"],
            status=item["status"],
            details=item["details"],
            value=item.get("value"),
            threshold=item.get("threshold"),
        )
        for item in result["checklist"]
    ]

    return EFCSNComplianceResponse(
        overall_status=result["overall_status"],
        checklist=checklist_items,
        last_checked=result["last_checked"],
        compliance_score=result["compliance_score"],
    )


# =============================================================================
# Complete Dashboard Endpoint
# =============================================================================


@router.get(
    "/analytics/dashboard",
    response_model=AnalyticsDashboardResponse,
    tags=["analytics"],
    summary="Get complete analytics dashboard",
    description="Get complete analytics dashboard with all metrics. Admin only.",
)
async def get_analytics_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AnalyticsDashboardResponse:
    """
    Get complete analytics dashboard combining all metrics.

    Includes:
    - Monthly fact-check counts
    - Time-to-publication metrics
    - Rating distribution
    - Source quality metrics
    - Correction rate metrics
    - EFCSN compliance checklist

    Admin only.
    """
    service: AnalyticsService = AnalyticsService(db)
    result: dict[str, Any] = await service.get_dashboard()

    # Convert to Pydantic models
    monthly_fc: dict[str, Any] = result["monthly_fact_checks"]
    monthly_counts: list[MonthlyFactCheckCount] = [
        MonthlyFactCheckCount(
            year=m["year"],
            month=m["month"],
            count=m["count"],
            meets_efcsn_minimum=m["meets_efcsn_minimum"],
        )
        for m in monthly_fc["months"]
    ]

    time_pub: dict[str, Any] = result["time_to_publication"]
    rating_dist: dict[str, Any] = result["rating_distribution"]
    source_qual: dict[str, Any] = result["source_quality"]
    corr_rate: dict[str, Any] = result["correction_rate"]
    compliance: dict[str, Any] = result["efcsn_compliance"]

    # Build rating distribution items
    rating_items: list[RatingDistributionItem] = [
        RatingDistributionItem(
            rating=r["rating"],
            count=r["count"],
            percentage=r["percentage"],
        )
        for r in rating_dist["ratings"]
    ]

    # Build compliance checklist items
    compliance_items: list[EFCSNComplianceChecklistItem] = [
        EFCSNComplianceChecklistItem(
            requirement=item["requirement"],
            status=item["status"],
            details=item["details"],
            value=item.get("value"),
            threshold=item.get("threshold"),
        )
        for item in compliance["checklist"]
    ]

    return AnalyticsDashboardResponse(
        monthly_fact_checks=MonthlyFactCheckCountResponse(
            months=monthly_counts,
            total_count=monthly_fc["total_count"],
            average_per_month=monthly_fc["average_per_month"],
        ),
        time_to_publication=TimeToPublicationMetrics(
            average_hours=time_pub["average_hours"],
            median_hours=time_pub["median_hours"],
            min_hours=time_pub["min_hours"],
            max_hours=time_pub["max_hours"],
            total_published=time_pub["total_published"],
        ),
        rating_distribution=RatingDistributionResponse(
            ratings=rating_items,
            total_count=rating_dist["total_count"],
            period_start=rating_dist.get("period_start"),
            period_end=rating_dist.get("period_end"),
        ),
        source_quality=SourceQualityMetrics(
            average_sources_per_fact_check=source_qual["average_sources_per_fact_check"],
            average_credibility_score=source_qual["average_credibility_score"],
            total_sources=source_qual["total_sources"],
            sources_by_type=source_qual["sources_by_type"],
            sources_by_relevance=source_qual["sources_by_relevance"],
            fact_checks_meeting_minimum=source_qual["fact_checks_meeting_minimum"],
            fact_checks_below_minimum=source_qual["fact_checks_below_minimum"],
        ),
        correction_rate=CorrectionRateMetrics(
            total_fact_checks=corr_rate["total_fact_checks"],
            total_corrections=corr_rate["total_corrections"],
            corrections_accepted=corr_rate["corrections_accepted"],
            corrections_rejected=corr_rate["corrections_rejected"],
            corrections_pending=corr_rate["corrections_pending"],
            correction_rate=corr_rate["correction_rate"],
            corrections_by_type=corr_rate["corrections_by_type"],
        ),
        efcsn_compliance=EFCSNComplianceResponse(
            overall_status=compliance["overall_status"],
            checklist=compliance_items,
            last_checked=compliance["last_checked"],
            compliance_score=compliance["compliance_score"],
        ),
        generated_at=result["generated_at"],
    )


# =============================================================================
# Monthly Fact-Checks Endpoint
# =============================================================================


@router.get(
    "/analytics/monthly-fact-checks",
    response_model=MonthlyFactCheckCountResponse,
    tags=["analytics"],
    summary="Get monthly fact-check counts",
    description="Get monthly fact-check publication counts. Admin only.",
)
async def get_monthly_fact_checks(
    months: int = Query(default=12, ge=1, le=36, description="Number of months to include"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> MonthlyFactCheckCountResponse:
    """
    Get monthly fact-check publication counts.

    EFCSN requires minimum 4 fact-checks published per month.

    Admin only.
    """
    service: AnalyticsService = AnalyticsService(db)
    result: dict[str, Any] = await service.get_monthly_fact_check_counts(months=months)

    monthly_counts: list[MonthlyFactCheckCount] = [
        MonthlyFactCheckCount(
            year=m["year"],
            month=m["month"],
            count=m["count"],
            meets_efcsn_minimum=m["meets_efcsn_minimum"],
        )
        for m in result["months"]
    ]

    return MonthlyFactCheckCountResponse(
        months=monthly_counts,
        total_count=result["total_count"],
        average_per_month=result["average_per_month"],
    )


# =============================================================================
# Rating Distribution Endpoint
# =============================================================================


@router.get(
    "/analytics/rating-distribution",
    response_model=RatingDistributionResponse,
    tags=["analytics"],
    summary="Get rating distribution",
    description="Get fact-check rating distribution statistics. Admin only.",
)
async def get_rating_distribution(
    start_date: Optional[datetime] = Query(default=None, description="Start of analysis period"),
    end_date: Optional[datetime] = Query(default=None, description="End of analysis period"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> RatingDistributionResponse:
    """
    Get rating distribution statistics.

    Optionally filter by date range.

    Admin only.
    """
    service: AnalyticsService = AnalyticsService(db)
    result: dict[str, Any] = await service.get_rating_distribution(
        start_date=start_date,
        end_date=end_date,
    )

    rating_items: list[RatingDistributionItem] = [
        RatingDistributionItem(
            rating=r["rating"],
            count=r["count"],
            percentage=r["percentage"],
        )
        for r in result["ratings"]
    ]

    return RatingDistributionResponse(
        ratings=rating_items,
        total_count=result["total_count"],
        period_start=result.get("period_start"),
        period_end=result.get("period_end"),
    )


# =============================================================================
# Source Quality Endpoint
# =============================================================================


@router.get(
    "/analytics/source-quality",
    response_model=SourceQualityMetrics,
    tags=["analytics"],
    summary="Get source quality metrics",
    description="Get source quality metrics for EFCSN compliance. Admin only.",
)
async def get_source_quality(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SourceQualityMetrics:
    """
    Get source quality metrics.

    EFCSN requires minimum 2 sources per fact-check.

    Admin only.
    """
    service: AnalyticsService = AnalyticsService(db)
    result: dict[str, Any] = await service.get_source_quality_metrics()

    return SourceQualityMetrics(
        average_sources_per_fact_check=result["average_sources_per_fact_check"],
        average_credibility_score=result["average_credibility_score"],
        total_sources=result["total_sources"],
        sources_by_type=result["sources_by_type"],
        sources_by_relevance=result["sources_by_relevance"],
        fact_checks_meeting_minimum=result["fact_checks_meeting_minimum"],
        fact_checks_below_minimum=result["fact_checks_below_minimum"],
    )


# =============================================================================
# Correction Rate Endpoint
# =============================================================================


@router.get(
    "/analytics/correction-rate",
    response_model=CorrectionRateMetrics,
    tags=["analytics"],
    summary="Get correction rate metrics",
    description="Get correction rate metrics for quality tracking. Admin only.",
)
async def get_correction_rate(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> CorrectionRateMetrics:
    """
    Get correction rate metrics.

    Includes:
    - Total corrections and breakdown by status
    - Correction rate per fact-check
    - Corrections grouped by type

    Admin only.
    """
    service: AnalyticsService = AnalyticsService(db)
    result: dict[str, Any] = await service.get_correction_rate_metrics()

    return CorrectionRateMetrics(
        total_fact_checks=result["total_fact_checks"],
        total_corrections=result["total_corrections"],
        corrections_accepted=result["corrections_accepted"],
        corrections_rejected=result["corrections_rejected"],
        corrections_pending=result["corrections_pending"],
        correction_rate=result["correction_rate"],
        corrections_by_type=result["corrections_by_type"],
    )
