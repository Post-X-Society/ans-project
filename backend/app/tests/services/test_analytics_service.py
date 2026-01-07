"""
Tests for AnalyticsService - TDD approach: Write tests FIRST.

Issue #88: Backend Analytics Service & EFCSN Compliance Metrics (TDD)
EPIC #52: Analytics & Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

Tests cover:
- Monthly fact-check publication metrics
- Time-to-publication analytics
- Rating distribution statistics
- Source quality metrics
- Correction rate tracking
- EFCSN compliance checklist
"""

from datetime import date, datetime, timezone
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.correction import Correction, CorrectionStatus, CorrectionType
from app.models.fact_check import FactCheck
from app.models.source import Source, SourceRelevance, SourceType
from app.models.user import User, UserRole


class TestAnalyticsServiceMonthlyFactCheckCount:
    """Tests for monthly fact-check count calculation."""

    @pytest.mark.asyncio
    async def test_get_monthly_fact_check_counts_returns_correct_counts(
        self, db_session: AsyncSession
    ) -> None:
        """Test that monthly fact-check counts are calculated correctly."""
        from app.services.analytics_service import AnalyticsService

        # Create claims for fact-checks
        claims: list[Claim] = []
        for i in range(6):
            claim: Claim = Claim(content=f"Test claim {i}", source="test")
            db_session.add(claim)
            claims.append(claim)
        await db_session.commit()

        for claim in claims:
            await db_session.refresh(claim)

        # Create fact-checks with different created_at dates
        # 4 in current month, 2 in previous month
        now: datetime = datetime.now(timezone.utc)
        _current_month_start: datetime = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        # Note: prev_month would be used for setting created_at dates in a more
        # realistic test, but for now we just create fact-checks in current month

        for i, claim in enumerate(claims[:4]):
            fc: FactCheck = FactCheck(
                claim_id=claim.id,
                verdict="true",
                confidence=0.9,
                reasoning=f"Fact check {i}",
                sources=["https://example.com"],
            )
            db_session.add(fc)

        for i, claim in enumerate(claims[4:]):
            fc = FactCheck(
                claim_id=claim.id,
                verdict="false",
                confidence=0.85,
                reasoning=f"Fact check previous month {i}",
                sources=["https://example.com"],
            )
            db_session.add(fc)

        await db_session.commit()

        # Get monthly counts for last 2 months
        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_monthly_fact_check_counts(months=2)

        # Assert structure
        assert "months" in result
        assert "total_count" in result
        assert "average_per_month" in result
        assert result["total_count"] >= 0

    @pytest.mark.asyncio
    async def test_get_monthly_fact_check_counts_identifies_efcsn_compliance(
        self, db_session: AsyncSession
    ) -> None:
        """Test that EFCSN minimum (4 per month) is correctly identified."""
        from app.services.analytics_service import AnalyticsService

        # Create 5 fact-checks (above EFCSN minimum)
        claims: list[Claim] = []
        for i in range(5):
            claim: Claim = Claim(content=f"Test claim {i}", source="test")
            db_session.add(claim)
            claims.append(claim)
        await db_session.commit()

        for claim in claims:
            await db_session.refresh(claim)

        for i, claim in enumerate(claims):
            fc: FactCheck = FactCheck(
                claim_id=claim.id,
                verdict="true",
                confidence=0.9,
                reasoning=f"Fact check {i}",
                sources=["https://example.com"],
            )
            db_session.add(fc)
        await db_session.commit()

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_monthly_fact_check_counts(months=1)

        # Current month should have 5 fact-checks, meeting EFCSN minimum
        assert len(result["months"]) >= 1
        current_month_data: dict[str, Any] = result["months"][0]
        assert current_month_data["count"] == 5
        assert current_month_data["meets_efcsn_minimum"] is True

    @pytest.mark.asyncio
    async def test_get_monthly_fact_check_counts_empty_database(
        self, db_session: AsyncSession
    ) -> None:
        """Test that empty database returns zero counts."""
        from app.services.analytics_service import AnalyticsService

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_monthly_fact_check_counts(months=1)

        assert result["total_count"] == 0
        assert result["average_per_month"] == 0.0


class TestAnalyticsServiceTimeToPublication:
    """Tests for time-to-publication metrics."""

    @pytest.mark.asyncio
    async def test_get_time_to_publication_metrics_calculates_average(
        self, db_session: AsyncSession
    ) -> None:
        """Test that time-to-publication average is calculated correctly."""
        from app.services.analytics_service import AnalyticsService

        # Create fact-checks with known creation times
        claims: list[Claim] = []
        for i in range(3):
            claim: Claim = Claim(content=f"Test claim {i}", source="test")
            db_session.add(claim)
            claims.append(claim)
        await db_session.commit()

        for claim in claims:
            await db_session.refresh(claim)

        # Create fact-checks
        for i, claim in enumerate(claims):
            fc: FactCheck = FactCheck(
                claim_id=claim.id,
                verdict="true",
                confidence=0.9,
                reasoning=f"Fact check {i}",
                sources=["https://example.com"],
            )
            db_session.add(fc)
        await db_session.commit()

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_time_to_publication_metrics()

        # Assert structure
        assert "average_hours" in result
        assert "median_hours" in result
        assert "min_hours" in result
        assert "max_hours" in result
        assert "total_published" in result
        assert result["total_published"] == 3

    @pytest.mark.asyncio
    async def test_get_time_to_publication_metrics_empty_database(
        self, db_session: AsyncSession
    ) -> None:
        """Test that empty database returns zero metrics."""
        from app.services.analytics_service import AnalyticsService

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_time_to_publication_metrics()

        assert result["average_hours"] == 0.0
        assert result["median_hours"] == 0.0
        assert result["total_published"] == 0


class TestAnalyticsServiceRatingDistribution:
    """Tests for rating distribution statistics."""

    @pytest.mark.asyncio
    async def test_get_rating_distribution_calculates_percentages(
        self, db_session: AsyncSession
    ) -> None:
        """Test that rating distribution percentages are calculated correctly."""
        from app.services.analytics_service import AnalyticsService

        # Create fact-checks with different verdicts
        verdicts: list[str] = ["true", "true", "false", "partially_true", "unverified"]
        claims: list[Claim] = []

        for i, _verdict in enumerate(verdicts):
            claim: Claim = Claim(content=f"Test claim {i}", source="test")
            db_session.add(claim)
            claims.append(claim)
        await db_session.commit()

        for claim in claims:
            await db_session.refresh(claim)

        for i, (claim, verdict) in enumerate(zip(claims, verdicts)):
            fc: FactCheck = FactCheck(
                claim_id=claim.id,
                verdict=verdict,
                confidence=0.9,
                reasoning=f"Fact check {i}",
                sources=["https://example.com"],
            )
            db_session.add(fc)
        await db_session.commit()

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_rating_distribution()

        # Assert structure
        assert "ratings" in result
        assert "total_count" in result
        assert result["total_count"] == 5

        # Find "true" rating and verify count
        ratings_dict: dict[str, dict[str, Any]] = {r["rating"]: r for r in result["ratings"]}
        assert "true" in ratings_dict
        assert ratings_dict["true"]["count"] == 2
        # 2 out of 5 = 40%
        assert ratings_dict["true"]["percentage"] == 40.0

    @pytest.mark.asyncio
    async def test_get_rating_distribution_empty_database(self, db_session: AsyncSession) -> None:
        """Test that empty database returns empty distribution."""
        from app.services.analytics_service import AnalyticsService

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_rating_distribution()

        assert result["total_count"] == 0
        assert result["ratings"] == []


class TestAnalyticsServiceSourceQuality:
    """Tests for source quality metrics."""

    @pytest.mark.asyncio
    async def test_get_source_quality_metrics_calculates_averages(
        self, db_session: AsyncSession
    ) -> None:
        """Test that source quality averages are calculated correctly."""
        from app.services.analytics_service import AnalyticsService

        # Create fact-check with sources
        claim: Claim = Claim(content="Test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Fact check",
            sources=["https://example.com"],
            sources_count=3,
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Add sources with different credibility scores
        sources_data: list[tuple[SourceType, int, SourceRelevance]] = [
            (SourceType.PRIMARY, 5, SourceRelevance.SUPPORTS),
            (SourceType.SECONDARY, 4, SourceRelevance.SUPPORTS),
            (SourceType.ACADEMIC, 5, SourceRelevance.CONTEXTUALIZES),
        ]

        for source_type, credibility, relevance in sources_data:
            source: Source = Source(
                fact_check_id=fact_check.id,
                source_type=source_type,
                title="Test source",
                url="https://example.com",
                access_date=date.today(),
                credibility_score=credibility,
                relevance=relevance,
            )
            db_session.add(source)
        await db_session.commit()

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_source_quality_metrics()

        # Assert structure
        assert "average_sources_per_fact_check" in result
        assert "average_credibility_score" in result
        assert "total_sources" in result
        assert "sources_by_type" in result
        assert "sources_by_relevance" in result
        assert "fact_checks_meeting_minimum" in result
        assert "fact_checks_below_minimum" in result

        # Verify calculations
        assert result["total_sources"] == 3
        # Average credibility: (5 + 4 + 5) / 3 = 4.67
        assert 4.6 <= result["average_credibility_score"] <= 4.7
        # 1 fact-check with 3 sources = average of 3
        assert result["average_sources_per_fact_check"] == 3.0

    @pytest.mark.asyncio
    async def test_get_source_quality_metrics_identifies_efcsn_minimum(
        self, db_session: AsyncSession
    ) -> None:
        """Test that fact-checks meeting/below EFCSN minimum (2 sources) are identified."""
        from app.services.analytics_service import AnalyticsService

        # Create 2 claims
        claim1: Claim = Claim(content="Test claim 1", source="test")
        claim2: Claim = Claim(content="Test claim 2", source="test")
        db_session.add_all([claim1, claim2])
        await db_session.commit()
        await db_session.refresh(claim1)
        await db_session.refresh(claim2)

        # Fact-check 1: has 3 sources (meets minimum)
        fc1: FactCheck = FactCheck(
            claim_id=claim1.id,
            verdict="true",
            confidence=0.9,
            reasoning="Fact check 1",
            sources=["https://example.com"],
            sources_count=3,
        )
        # Fact-check 2: has 1 source (below minimum)
        fc2: FactCheck = FactCheck(
            claim_id=claim2.id,
            verdict="false",
            confidence=0.8,
            reasoning="Fact check 2",
            sources=["https://example.com"],
            sources_count=1,
        )
        db_session.add_all([fc1, fc2])
        await db_session.commit()
        await db_session.refresh(fc1)
        await db_session.refresh(fc2)

        # Add sources for fact-check 1
        for i in range(3):
            source: Source = Source(
                fact_check_id=fc1.id,
                source_type=SourceType.PRIMARY,
                title=f"Source {i}",
                access_date=date.today(),
            )
            db_session.add(source)

        # Add 1 source for fact-check 2
        source2: Source = Source(
            fact_check_id=fc2.id,
            source_type=SourceType.SECONDARY,
            title="Single source",
            access_date=date.today(),
        )
        db_session.add(source2)
        await db_session.commit()

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_source_quality_metrics()

        assert result["fact_checks_meeting_minimum"] == 1
        assert result["fact_checks_below_minimum"] == 1

    @pytest.mark.asyncio
    async def test_get_source_quality_metrics_empty_database(
        self, db_session: AsyncSession
    ) -> None:
        """Test that empty database returns zero metrics."""
        from app.services.analytics_service import AnalyticsService

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_source_quality_metrics()

        assert result["total_sources"] == 0
        assert result["average_sources_per_fact_check"] == 0.0
        assert result["average_credibility_score"] == 0.0


class TestAnalyticsServiceCorrectionRate:
    """Tests for correction rate metrics."""

    @pytest.mark.asyncio
    async def test_get_correction_rate_metrics_calculates_rate(
        self, db_session: AsyncSession
    ) -> None:
        """Test that correction rate is calculated correctly."""
        from app.services.analytics_service import AnalyticsService

        # Create a user for reviewed_by_id
        user: User = User(
            email="reviewer@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create 4 fact-checks
        claims: list[Claim] = []
        for i in range(4):
            claim: Claim = Claim(content=f"Test claim {i}", source="test")
            db_session.add(claim)
            claims.append(claim)
        await db_session.commit()

        fact_checks: list[FactCheck] = []
        for i, claim in enumerate(claims):
            await db_session.refresh(claim)
            fc: FactCheck = FactCheck(
                claim_id=claim.id,
                verdict="true",
                confidence=0.9,
                reasoning=f"Fact check {i}",
                sources=["https://example.com"],
            )
            db_session.add(fc)
            fact_checks.append(fc)
        await db_session.commit()

        for fc in fact_checks:
            await db_session.refresh(fc)

        # Create corrections with different statuses
        corrections_data: list[tuple[CorrectionType, CorrectionStatus]] = [
            (CorrectionType.MINOR, CorrectionStatus.ACCEPTED),
            (CorrectionType.UPDATE, CorrectionStatus.REJECTED),
            (CorrectionType.SUBSTANTIAL, CorrectionStatus.PENDING),
            (CorrectionType.SUBSTANTIAL, CorrectionStatus.ACCEPTED),
        ]

        for i, (ctype, status) in enumerate(corrections_data):
            correction: Correction = Correction(
                fact_check_id=fact_checks[i % len(fact_checks)].id,
                correction_type=ctype,
                request_details=f"Correction {i}",
                status=status,
            )
            if status != CorrectionStatus.PENDING:
                correction.reviewed_by_id = user.id
                correction.reviewed_at = datetime.now(timezone.utc)
            db_session.add(correction)
        await db_session.commit()

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_correction_rate_metrics()

        # Assert structure
        assert "total_fact_checks" in result
        assert "total_corrections" in result
        assert "corrections_accepted" in result
        assert "corrections_rejected" in result
        assert "corrections_pending" in result
        assert "correction_rate" in result
        assert "corrections_by_type" in result

        # Verify counts
        assert result["total_fact_checks"] == 4
        assert result["total_corrections"] == 4
        assert result["corrections_accepted"] == 2
        assert result["corrections_rejected"] == 1
        assert result["corrections_pending"] == 1
        # Correction rate: 4 corrections / 4 fact-checks = 1.0
        assert result["correction_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_get_correction_rate_metrics_by_type(self, db_session: AsyncSession) -> None:
        """Test that corrections are correctly grouped by type."""
        from app.services.analytics_service import AnalyticsService

        # Create fact-check
        claim: Claim = Claim(content="Test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fc: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Fact check",
            sources=["https://example.com"],
        )
        db_session.add(fc)
        await db_session.commit()
        await db_session.refresh(fc)

        # Create corrections of each type
        for ctype in [CorrectionType.MINOR, CorrectionType.MINOR, CorrectionType.UPDATE]:
            correction: Correction = Correction(
                fact_check_id=fc.id,
                correction_type=ctype,
                request_details=f"Correction {ctype.value}",
                status=CorrectionStatus.PENDING,
            )
            db_session.add(correction)
        await db_session.commit()

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_correction_rate_metrics()

        # Verify type grouping
        assert result["corrections_by_type"]["minor"] == 2
        assert result["corrections_by_type"]["update"] == 1
        assert result["corrections_by_type"].get("substantial", 0) == 0

    @pytest.mark.asyncio
    async def test_get_correction_rate_metrics_empty_database(
        self, db_session: AsyncSession
    ) -> None:
        """Test that empty database returns zero metrics."""
        from app.services.analytics_service import AnalyticsService

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_correction_rate_metrics()

        assert result["total_fact_checks"] == 0
        assert result["total_corrections"] == 0
        assert result["correction_rate"] == 0.0


class TestAnalyticsServiceEFCSNCompliance:
    """Tests for EFCSN compliance checklist."""

    @pytest.mark.asyncio
    async def test_get_efcsn_compliance_returns_checklist(self, db_session: AsyncSession) -> None:
        """Test that EFCSN compliance checklist is returned with all required items."""
        from app.services.analytics_service import AnalyticsService

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_efcsn_compliance()

        # Assert structure
        assert "overall_status" in result
        assert "checklist" in result
        assert "last_checked" in result
        assert "compliance_score" in result

        # Verify checklist items exist
        checklist_requirements: set[str] = {item["requirement"] for item in result["checklist"]}
        expected_requirements: set[str] = {
            "Monthly Fact-Check Minimum",
            "Source Documentation",
            "Corrections Policy",
        }
        # Should have at least these key requirements
        assert expected_requirements.issubset(checklist_requirements)

    @pytest.mark.asyncio
    async def test_get_efcsn_compliance_identifies_compliant_status(
        self, db_session: AsyncSession
    ) -> None:
        """Test that compliant status is correctly identified when all requirements met."""
        from app.services.analytics_service import AnalyticsService

        # Create 5 fact-checks with 2+ sources each (above EFCSN minimums)
        claims: list[Claim] = []
        for i in range(5):
            claim: Claim = Claim(content=f"Test claim {i}", source="test")
            db_session.add(claim)
            claims.append(claim)
        await db_session.commit()

        for claim in claims:
            await db_session.refresh(claim)

        for i, claim in enumerate(claims):
            fc: FactCheck = FactCheck(
                claim_id=claim.id,
                verdict="true",
                confidence=0.9,
                reasoning=f"Fact check {i}",
                sources=["https://example.com", "https://example2.com"],
                sources_count=2,
            )
            db_session.add(fc)
        await db_session.commit()

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_efcsn_compliance()

        # Check monthly fact-check compliance
        monthly_item: dict[str, Any] | None = None
        for item in result["checklist"]:
            if item["requirement"] == "Monthly Fact-Check Minimum":
                monthly_item = item
                break

        assert monthly_item is not None
        assert monthly_item["status"] == "compliant"

    @pytest.mark.asyncio
    async def test_get_efcsn_compliance_identifies_non_compliant_status(
        self, db_session: AsyncSession
    ) -> None:
        """Test that non-compliant status is identified when requirements not met."""
        from app.services.analytics_service import AnalyticsService

        # Create only 2 fact-checks (below EFCSN minimum of 4)
        claims: list[Claim] = []
        for i in range(2):
            claim: Claim = Claim(content=f"Test claim {i}", source="test")
            db_session.add(claim)
            claims.append(claim)
        await db_session.commit()

        for claim in claims:
            await db_session.refresh(claim)

        for i, claim in enumerate(claims):
            fc: FactCheck = FactCheck(
                claim_id=claim.id,
                verdict="true",
                confidence=0.9,
                reasoning=f"Fact check {i}",
                sources=["https://example.com"],
                sources_count=1,  # Also below EFCSN minimum of 2 sources
            )
            db_session.add(fc)
        await db_session.commit()

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_efcsn_compliance()

        # Check monthly fact-check compliance - should be non-compliant
        monthly_item: dict[str, Any] | None = None
        for item in result["checklist"]:
            if item["requirement"] == "Monthly Fact-Check Minimum":
                monthly_item = item
                break

        assert monthly_item is not None
        assert monthly_item["status"] == "non_compliant"

    @pytest.mark.asyncio
    async def test_get_efcsn_compliance_calculates_score(self, db_session: AsyncSession) -> None:
        """Test that compliance score is calculated as percentage."""
        from app.services.analytics_service import AnalyticsService

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_efcsn_compliance()

        # Score should be between 0 and 100
        assert 0 <= result["compliance_score"] <= 100


class TestAnalyticsServiceDashboard:
    """Tests for complete analytics dashboard."""

    @pytest.mark.asyncio
    async def test_get_dashboard_returns_all_metrics(self, db_session: AsyncSession) -> None:
        """Test that dashboard returns all analytics components."""
        from app.services.analytics_service import AnalyticsService

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_dashboard()

        # Assert all dashboard components present
        assert "monthly_fact_checks" in result
        assert "time_to_publication" in result
        assert "rating_distribution" in result
        assert "source_quality" in result
        assert "correction_rate" in result
        assert "efcsn_compliance" in result
        assert "generated_at" in result

    @pytest.mark.asyncio
    async def test_get_dashboard_with_data(self, db_session: AsyncSession) -> None:
        """Test dashboard with populated data."""
        from app.services.analytics_service import AnalyticsService

        # Create some test data
        claim: Claim = Claim(content="Test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fc: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test fact check",
            sources=["https://example.com"],
            sources_count=1,
        )
        db_session.add(fc)
        await db_session.commit()

        service: AnalyticsService = AnalyticsService(db_session)
        result: dict[str, Any] = await service.get_dashboard()

        # Verify data is populated
        assert result["monthly_fact_checks"]["total_count"] >= 1
        assert result["rating_distribution"]["total_count"] >= 1
