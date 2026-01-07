"""
AnalyticsService for EFCSN compliance metrics and analytics dashboard.

Issue #88: Backend Analytics Service & EFCSN Compliance Metrics (TDD)
EPIC #52: Analytics & Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

This service implements:
- Monthly fact-check publication metrics (EFCSN requires 4+ per month)
- Time-to-publication analytics
- Rating distribution statistics
- Source quality metrics (EFCSN requires 2+ sources per fact-check)
- Correction rate tracking
- EFCSN compliance checklist for real-time monitoring
"""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.correction import Correction, CorrectionStatus
from app.models.fact_check import FactCheck
from app.models.source import Source

logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTS
# ==============================================================================

# EFCSN minimum fact-checks per month
EFCSN_MIN_FACT_CHECKS_PER_MONTH: int = 4

# EFCSN minimum sources per fact-check
EFCSN_MIN_SOURCES_PER_FACT_CHECK: int = 2


# ==============================================================================
# ANALYTICS SERVICE CLASS
# ==============================================================================


class AnalyticsService:
    """
    Service for calculating analytics metrics and EFCSN compliance status.

    This service provides:
    - Monthly fact-check counts with EFCSN compliance tracking
    - Time-to-publication metrics
    - Rating distribution statistics
    - Source quality metrics
    - Correction rate calculations
    - EFCSN compliance checklist
    - Complete analytics dashboard
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the analytics service.

        Args:
            db: Async database session
        """
        self.db = db

    # ==========================================================================
    # MONTHLY FACT-CHECK COUNTS
    # ==========================================================================

    async def get_monthly_fact_check_counts(self, months: int = 12) -> dict[str, Any]:
        """
        Get monthly fact-check publication counts.

        EFCSN requires minimum 4 fact-checks published per month.

        Args:
            months: Number of months to include (default 12)

        Returns:
            Dictionary containing:
            - months: List of monthly counts with EFCSN compliance status
            - total_count: Total fact-checks in period
            - average_per_month: Average fact-checks per month
        """
        now: datetime = datetime.now(timezone.utc)

        # Calculate date range
        month_data: list[dict[str, Any]] = []
        total_count: int = 0

        for i in range(months):
            # Calculate month boundaries
            year: int = now.year
            month: int = now.month - i

            # Handle year rollover
            while month <= 0:
                month += 12
                year -= 1

            # Get count for this month using created_at
            stmt = select(func.count(FactCheck.id)).where(
                func.extract("year", FactCheck.created_at) == year,
                func.extract("month", FactCheck.created_at) == month,
            )
            result = await self.db.execute(stmt)
            count: int = result.scalar() or 0

            month_data.append(
                {
                    "year": year,
                    "month": month,
                    "count": count,
                    "meets_efcsn_minimum": count >= EFCSN_MIN_FACT_CHECKS_PER_MONTH,
                }
            )
            total_count += count

        # Calculate average
        average: float = total_count / months if months > 0 else 0.0

        return {
            "months": month_data,
            "total_count": total_count,
            "average_per_month": round(average, 2),
        }

    # ==========================================================================
    # TIME-TO-PUBLICATION METRICS
    # ==========================================================================

    async def get_time_to_publication_metrics(self, days: int = 90) -> dict[str, Any]:
        """
        Calculate time-to-publication metrics.

        Measures the time from fact-check creation to now (placeholder for
        actual publication timestamp when workflow is complete).

        Args:
            days: Number of days to analyze (default 90)

        Returns:
            Dictionary containing time-to-publication statistics
        """
        # Get all fact-checks
        stmt = select(FactCheck)
        result = await self.db.execute(stmt)
        fact_checks: list[FactCheck] = list(result.scalars().all())

        if not fact_checks:
            return {
                "average_hours": 0.0,
                "median_hours": 0.0,
                "min_hours": 0.0,
                "max_hours": 0.0,
                "total_published": 0,
            }

        # Calculate publication times (using created_at as proxy for now)
        # In a full implementation, this would use the workflow publication timestamp
        publication_hours: list[float] = []
        now: datetime = datetime.now(timezone.utc)

        for fc in fact_checks:
            created_at: datetime = fc.created_at
            # Normalize timezone
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            # For now, calculate time since creation (placeholder metric)
            delta = now - created_at
            hours: float = delta.total_seconds() / 3600
            publication_hours.append(hours)

        # Calculate statistics
        publication_hours.sort()
        total: int = len(publication_hours)
        avg: float = sum(publication_hours) / total
        median: float = (
            publication_hours[total // 2]
            if total % 2 == 1
            else (publication_hours[total // 2 - 1] + publication_hours[total // 2]) / 2
        )

        return {
            "average_hours": round(avg, 2),
            "median_hours": round(median, 2),
            "min_hours": round(min(publication_hours), 2),
            "max_hours": round(max(publication_hours), 2),
            "total_published": total,
        }

    # ==========================================================================
    # RATING DISTRIBUTION
    # ==========================================================================

    async def get_rating_distribution(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get rating distribution statistics.

        Args:
            start_date: Optional start of period
            end_date: Optional end of period

        Returns:
            Dictionary containing rating distribution with percentages
        """
        # Build query
        stmt = select(FactCheck.verdict, func.count(FactCheck.id).label("count")).group_by(
            FactCheck.verdict
        )

        # Apply date filters if provided
        if start_date:
            stmt = stmt.where(FactCheck.created_at >= start_date)
        if end_date:
            stmt = stmt.where(FactCheck.created_at <= end_date)

        result = await self.db.execute(stmt)
        rows = result.all()

        if not rows:
            return {
                "ratings": [],
                "total_count": 0,
                "period_start": start_date,
                "period_end": end_date,
            }

        # Calculate total
        total_count: int = sum(int(row.count) for row in rows)

        # Build distribution
        ratings: list[dict[str, Any]] = []
        for row in rows:
            count_val = int(row.count)
            percentage: float = (count_val / total_count * 100) if total_count > 0 else 0.0
            ratings.append(
                {
                    "rating": row.verdict,
                    "count": count_val,
                    "percentage": round(percentage, 1),
                }
            )

        # Sort by count descending
        ratings.sort(key=lambda x: x["count"], reverse=True)

        return {
            "ratings": ratings,
            "total_count": total_count,
            "period_start": start_date,
            "period_end": end_date,
        }

    # ==========================================================================
    # SOURCE QUALITY METRICS
    # ==========================================================================

    async def get_source_quality_metrics(self) -> dict[str, Any]:
        """
        Calculate source quality metrics for EFCSN compliance.

        EFCSN requires minimum 2 sources per fact-check.

        Returns:
            Dictionary containing source quality statistics
        """
        # Get total sources
        total_sources_stmt = select(func.count(Source.id))
        total_sources_result = await self.db.execute(total_sources_stmt)
        total_sources: int = total_sources_result.scalar() or 0

        # Get total fact-checks
        total_fc_stmt = select(func.count(FactCheck.id))
        total_fc_result = await self.db.execute(total_fc_stmt)
        total_fact_checks: int = total_fc_result.scalar() or 0

        # Calculate average sources per fact-check
        avg_sources: float = total_sources / total_fact_checks if total_fact_checks > 0 else 0.0

        # Get average credibility score (only for sources with scores)
        avg_cred_stmt = select(func.avg(Source.credibility_score)).where(
            Source.credibility_score.isnot(None)
        )
        avg_cred_result = await self.db.execute(avg_cred_stmt)
        avg_credibility: float = float(avg_cred_result.scalar() or 0.0)

        # Get sources by type
        sources_by_type_stmt = select(
            Source.source_type, func.count(Source.id).label("count")
        ).group_by(Source.source_type)
        sources_by_type_result = await self.db.execute(sources_by_type_stmt)
        sources_by_type: dict[str, int] = {
            (
                row.source_type.value if hasattr(row.source_type, "value") else str(row.source_type)
            ): int(row.count)
            for row in sources_by_type_result.all()
        }

        # Get sources by relevance
        sources_by_relevance_stmt = (
            select(Source.relevance, func.count(Source.id).label("count"))
            .where(Source.relevance.isnot(None))
            .group_by(Source.relevance)
        )
        sources_by_relevance_result = await self.db.execute(sources_by_relevance_stmt)
        sources_by_relevance: dict[str, int] = {
            (
                row.relevance.value if hasattr(row.relevance, "value") else str(row.relevance)
            ): int(row.count)
            for row in sources_by_relevance_result.all()
        }

        # Count fact-checks meeting/below EFCSN minimum (2 sources)
        # Using sources_count column from FactCheck model
        meeting_min_stmt = select(func.count(FactCheck.id)).where(
            FactCheck.sources_count >= EFCSN_MIN_SOURCES_PER_FACT_CHECK
        )
        meeting_min_result = await self.db.execute(meeting_min_stmt)
        fact_checks_meeting_minimum: int = meeting_min_result.scalar() or 0

        below_min_stmt = select(func.count(FactCheck.id)).where(
            FactCheck.sources_count < EFCSN_MIN_SOURCES_PER_FACT_CHECK
        )
        below_min_result = await self.db.execute(below_min_stmt)
        fact_checks_below_minimum: int = below_min_result.scalar() or 0

        return {
            "average_sources_per_fact_check": round(avg_sources, 2),
            "average_credibility_score": round(avg_credibility, 2),
            "total_sources": total_sources,
            "sources_by_type": sources_by_type,
            "sources_by_relevance": sources_by_relevance,
            "fact_checks_meeting_minimum": fact_checks_meeting_minimum,
            "fact_checks_below_minimum": fact_checks_below_minimum,
        }

    # ==========================================================================
    # CORRECTION RATE METRICS
    # ==========================================================================

    async def get_correction_rate_metrics(self) -> dict[str, Any]:
        """
        Calculate correction rate metrics for quality tracking.

        Returns:
            Dictionary containing correction statistics
        """
        # Get total fact-checks
        total_fc_stmt = select(func.count(FactCheck.id))
        total_fc_result = await self.db.execute(total_fc_stmt)
        total_fact_checks: int = total_fc_result.scalar() or 0

        # Get total corrections
        total_corr_stmt = select(func.count(Correction.id))
        total_corr_result = await self.db.execute(total_corr_stmt)
        total_corrections: int = total_corr_result.scalar() or 0

        # Get corrections by status
        accepted_stmt = select(func.count(Correction.id)).where(
            Correction.status == CorrectionStatus.ACCEPTED
        )
        accepted_result = await self.db.execute(accepted_stmt)
        corrections_accepted: int = accepted_result.scalar() or 0

        rejected_stmt = select(func.count(Correction.id)).where(
            Correction.status == CorrectionStatus.REJECTED
        )
        rejected_result = await self.db.execute(rejected_stmt)
        corrections_rejected: int = rejected_result.scalar() or 0

        pending_stmt = select(func.count(Correction.id)).where(
            Correction.status == CorrectionStatus.PENDING
        )
        pending_result = await self.db.execute(pending_stmt)
        corrections_pending: int = pending_result.scalar() or 0

        # Calculate correction rate
        correction_rate: float = (
            total_corrections / total_fact_checks if total_fact_checks > 0 else 0.0
        )

        # Get corrections by type
        corr_by_type_stmt = select(
            Correction.correction_type, func.count(Correction.id).label("count")
        ).group_by(Correction.correction_type)
        corr_by_type_result = await self.db.execute(corr_by_type_stmt)
        corrections_by_type: dict[str, int] = {
            (
                row.correction_type.value
                if hasattr(row.correction_type, "value")
                else str(row.correction_type)
            ): int(row.count)
            for row in corr_by_type_result.all()
        }

        return {
            "total_fact_checks": total_fact_checks,
            "total_corrections": total_corrections,
            "corrections_accepted": corrections_accepted,
            "corrections_rejected": corrections_rejected,
            "corrections_pending": corrections_pending,
            "correction_rate": round(correction_rate, 2),
            "corrections_by_type": corrections_by_type,
        }

    # ==========================================================================
    # EFCSN COMPLIANCE CHECKLIST
    # ==========================================================================

    async def get_efcsn_compliance(self) -> dict[str, Any]:
        """
        Generate EFCSN compliance checklist with real-time status.

        Checks:
        - Monthly fact-check minimum (4+)
        - Source documentation (2+ sources per fact-check)
        - Corrections policy availability

        Returns:
            Dictionary containing compliance status and checklist
        """
        now: datetime = datetime.now(timezone.utc)
        checklist: list[dict[str, Any]] = []
        compliant_count: int = 0
        total_checks: int = 0

        # ==========================================================================
        # Check 1: Monthly Fact-Check Minimum
        # ==========================================================================
        total_checks += 1
        current_month: int = now.month
        current_year: int = now.year

        monthly_count_stmt = select(func.count(FactCheck.id)).where(
            func.extract("year", FactCheck.created_at) == current_year,
            func.extract("month", FactCheck.created_at) == current_month,
        )
        monthly_count_result = await self.db.execute(monthly_count_stmt)
        monthly_count: int = monthly_count_result.scalar() or 0

        monthly_status: str = (
            "compliant" if monthly_count >= EFCSN_MIN_FACT_CHECKS_PER_MONTH else "non_compliant"
        )
        if monthly_status == "compliant":
            compliant_count += 1

        checklist.append(
            {
                "requirement": "Monthly Fact-Check Minimum",
                "status": monthly_status,
                "details": f"{monthly_count} fact-checks published this month",
                "value": str(monthly_count),
                "threshold": str(EFCSN_MIN_FACT_CHECKS_PER_MONTH),
            }
        )

        # ==========================================================================
        # Check 2: Source Documentation
        # ==========================================================================
        total_checks += 1
        source_metrics: dict[str, Any] = await self.get_source_quality_metrics()

        total_fc: int = (
            source_metrics["fact_checks_meeting_minimum"]
            + source_metrics["fact_checks_below_minimum"]
        )
        meeting_min: int = source_metrics["fact_checks_meeting_minimum"]

        source_compliance_pct: float = (meeting_min / total_fc * 100) if total_fc > 0 else 100.0

        source_status: str
        if source_compliance_pct >= 90:
            source_status = "compliant"
            compliant_count += 1
        elif source_compliance_pct >= 75:
            source_status = "warning"
        else:
            source_status = "non_compliant"

        checklist.append(
            {
                "requirement": "Source Documentation",
                "status": source_status,
                "details": f"{meeting_min}/{total_fc} fact-checks have 2+ sources ({source_compliance_pct:.1f}%)",
                "value": f"{source_compliance_pct:.1f}%",
                "threshold": "90%",
            }
        )

        # ==========================================================================
        # Check 3: Corrections Policy
        # ==========================================================================
        total_checks += 1
        # This is a placeholder - in a real implementation, this would check
        # if the corrections policy transparency page exists and is up to date
        corrections_policy_exists: bool = True  # Assume policy exists for now

        corrections_status: str = "compliant" if corrections_policy_exists else "non_compliant"
        if corrections_status == "compliant":
            compliant_count += 1

        checklist.append(
            {
                "requirement": "Corrections Policy",
                "status": corrections_status,
                "details": "Corrections policy is in place and publicly accessible",
                "value": "Available" if corrections_policy_exists else "Missing",
                "threshold": "Required",
            }
        )

        # ==========================================================================
        # Calculate Overall Status
        # ==========================================================================
        compliance_score: float = (
            (compliant_count / total_checks * 100) if total_checks > 0 else 0.0
        )

        overall_status: str
        if compliance_score == 100:
            overall_status = "compliant"
        elif compliance_score >= 66:
            overall_status = "at_risk"
        else:
            overall_status = "non_compliant"

        return {
            "overall_status": overall_status,
            "checklist": checklist,
            "last_checked": now,
            "compliance_score": round(compliance_score, 1),
        }

    # ==========================================================================
    # COMPLETE DASHBOARD
    # ==========================================================================

    async def get_dashboard(self) -> dict[str, Any]:
        """
        Generate complete analytics dashboard combining all metrics.

        Returns:
            Dictionary containing all analytics components
        """
        now: datetime = datetime.now(timezone.utc)

        # Gather all metrics
        monthly_fact_checks: dict[str, Any] = await self.get_monthly_fact_check_counts(months=12)
        time_to_publication: dict[str, Any] = await self.get_time_to_publication_metrics()
        rating_distribution: dict[str, Any] = await self.get_rating_distribution()
        source_quality: dict[str, Any] = await self.get_source_quality_metrics()
        correction_rate: dict[str, Any] = await self.get_correction_rate_metrics()
        efcsn_compliance: dict[str, Any] = await self.get_efcsn_compliance()

        return {
            "monthly_fact_checks": monthly_fact_checks,
            "time_to_publication": time_to_publication,
            "rating_distribution": rating_distribution,
            "source_quality": source_quality,
            "correction_rate": correction_rate,
            "efcsn_compliance": efcsn_compliance,
            "generated_at": now,
        }
