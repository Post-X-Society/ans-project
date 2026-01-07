"""
Tests for Analytics API endpoints - TDD approach: Write tests FIRST.

Issue #88: Backend Analytics Service & EFCSN Compliance Metrics (TDD)
EPIC #52: Analytics & Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

Tests cover:
- GET /api/v1/analytics/compliance - EFCSN compliance checklist
- GET /api/v1/analytics/dashboard - Complete analytics dashboard
- GET /api/v1/analytics/monthly-fact-checks - Monthly publication counts
- GET /api/v1/analytics/rating-distribution - Rating statistics
- GET /api/v1/analytics/source-quality - Source quality metrics
- GET /api/v1/analytics/correction-rate - Correction rate metrics
"""

from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.correction import Correction, CorrectionStatus, CorrectionType
from app.models.fact_check import FactCheck
from app.models.source import Source, SourceRelevance, SourceType
from app.models.user import User, UserRole


class TestEFCSNComplianceEndpoint:
    """Tests for EFCSN compliance checklist endpoint."""

    @pytest.mark.asyncio
    async def test_get_efcsn_compliance_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that EFCSN compliance endpoint requires authentication."""
        response = client.get("/api/v1/analytics/compliance")

        # Assert 401 Unauthorized
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_efcsn_compliance_requires_admin(
        self,
        client: TestClient,
        db_session: AsyncSession,
        auth_user: tuple[User, str],
    ) -> None:
        """Test that EFCSN compliance endpoint requires admin role."""
        user, token = auth_user

        response = client.get(
            "/api/v1/analytics/compliance",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert 403 Forbidden (user is SUBMITTER, not ADMIN)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_efcsn_compliance_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can access EFCSN compliance checklist."""
        # Create admin user
        admin: User = User(
            email="admin_compliance@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        response = client.get(
            "/api/v1/analytics/compliance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert success
        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        # Verify structure
        assert "overall_status" in data
        assert "checklist" in data
        assert "last_checked" in data
        assert "compliance_score" in data

        # Verify checklist items
        assert len(data["checklist"]) >= 3
        requirements: set[str] = {item["requirement"] for item in data["checklist"]}
        assert "Monthly Fact-Check Minimum" in requirements
        assert "Source Documentation" in requirements
        assert "Corrections Policy" in requirements

    @pytest.mark.asyncio
    async def test_get_efcsn_compliance_with_data(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test EFCSN compliance with fact-check data."""
        # Create admin user
        admin: User = User(
            email="admin_compliance_data@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        # Create 5 fact-checks (above EFCSN minimum of 4)
        claims: list[Claim] = []
        for i in range(5):
            claim: Claim = Claim(content=f"Compliance test claim {i}", source="test")
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

        response = client.get(
            "/api/v1/analytics/compliance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert compliance status
        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        # Should be compliant for monthly minimum
        monthly_item: dict[str, Any] | None = None
        for item in data["checklist"]:
            if item["requirement"] == "Monthly Fact-Check Minimum":
                monthly_item = item
                break

        assert monthly_item is not None
        assert monthly_item["status"] == "compliant"


class TestAnalyticsDashboardEndpoint:
    """Tests for complete analytics dashboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_dashboard_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that dashboard endpoint requires authentication."""
        response = client.get("/api/v1/analytics/dashboard")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_dashboard_requires_admin(
        self,
        client: TestClient,
        db_session: AsyncSession,
        auth_user: tuple[User, str],
    ) -> None:
        """Test that dashboard endpoint requires admin role."""
        user, token = auth_user

        response = client.get(
            "/api/v1/analytics/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_dashboard_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can access complete analytics dashboard."""
        # Create admin user
        admin: User = User(
            email="admin_dashboard@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        response = client.get(
            "/api/v1/analytics/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert success
        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        # Verify all dashboard components
        assert "monthly_fact_checks" in data
        assert "time_to_publication" in data
        assert "rating_distribution" in data
        assert "source_quality" in data
        assert "correction_rate" in data
        assert "efcsn_compliance" in data
        assert "generated_at" in data


class TestMonthlyFactChecksEndpoint:
    """Tests for monthly fact-check counts endpoint."""

    @pytest.mark.asyncio
    async def test_get_monthly_fact_checks_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that monthly fact-checks endpoint requires authentication."""
        response = client.get("/api/v1/analytics/monthly-fact-checks")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_monthly_fact_checks_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can access monthly fact-check counts."""
        # Create admin user
        admin: User = User(
            email="admin_monthly@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        # Create some fact-checks
        claim: Claim = Claim(content="Monthly test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fc: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fc)
        await db_session.commit()

        response = client.get(
            "/api/v1/analytics/monthly-fact-checks",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert success
        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        assert "months" in data
        assert "total_count" in data
        assert "average_per_month" in data
        assert data["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_get_monthly_fact_checks_with_months_param(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test monthly fact-checks with months parameter."""
        # Create admin user
        admin: User = User(
            email="admin_monthly_param@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        response = client.get(
            "/api/v1/analytics/monthly-fact-checks",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"months": 6},
        )

        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert len(data["months"]) == 6


class TestRatingDistributionEndpoint:
    """Tests for rating distribution endpoint."""

    @pytest.mark.asyncio
    async def test_get_rating_distribution_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that rating distribution endpoint requires authentication."""
        response = client.get("/api/v1/analytics/rating-distribution")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_rating_distribution_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can access rating distribution."""
        # Create admin user
        admin: User = User(
            email="admin_rating@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        # Create fact-checks with different verdicts
        verdicts: list[str] = ["true", "false", "partially_true"]
        for i, verdict in enumerate(verdicts):
            claim: Claim = Claim(content=f"Rating test {i}", source="test")
            db_session.add(claim)
            await db_session.commit()
            await db_session.refresh(claim)

            fc: FactCheck = FactCheck(
                claim_id=claim.id,
                verdict=verdict,
                confidence=0.9,
                reasoning=f"Test {i}",
                sources=["https://example.com"],
            )
            db_session.add(fc)
        await db_session.commit()

        response = client.get(
            "/api/v1/analytics/rating-distribution",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert success
        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        assert "ratings" in data
        assert "total_count" in data
        assert data["total_count"] == 3


class TestSourceQualityEndpoint:
    """Tests for source quality metrics endpoint."""

    @pytest.mark.asyncio
    async def test_get_source_quality_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that source quality endpoint requires authentication."""
        response = client.get("/api/v1/analytics/source-quality")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_source_quality_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can access source quality metrics."""
        # Create admin user
        admin: User = User(
            email="admin_source@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        # Create fact-check with sources
        claim: Claim = Claim(content="Source quality test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fc: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
            sources_count=2,
        )
        db_session.add(fc)
        await db_session.commit()
        await db_session.refresh(fc)

        # Add sources
        source1: Source = Source(
            fact_check_id=fc.id,
            source_type=SourceType.PRIMARY,
            title="Primary source",
            access_date=date.today(),
            credibility_score=5,
            relevance=SourceRelevance.SUPPORTS,
        )
        source2: Source = Source(
            fact_check_id=fc.id,
            source_type=SourceType.SECONDARY,
            title="Secondary source",
            access_date=date.today(),
            credibility_score=4,
            relevance=SourceRelevance.CONTEXTUALIZES,
        )
        db_session.add_all([source1, source2])
        await db_session.commit()

        response = client.get(
            "/api/v1/analytics/source-quality",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert success
        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        assert "average_sources_per_fact_check" in data
        assert "average_credibility_score" in data
        assert "total_sources" in data
        assert "sources_by_type" in data
        assert "fact_checks_meeting_minimum" in data
        assert data["total_sources"] == 2


class TestCorrectionRateEndpoint:
    """Tests for correction rate metrics endpoint."""

    @pytest.mark.asyncio
    async def test_get_correction_rate_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that correction rate endpoint requires authentication."""
        response = client.get("/api/v1/analytics/correction-rate")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_correction_rate_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can access correction rate metrics."""
        # Create admin user
        admin: User = User(
            email="admin_correction@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        # Create fact-check
        claim: Claim = Claim(content="Correction rate test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fc: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fc)
        await db_session.commit()
        await db_session.refresh(fc)

        # Create corrections
        correction: Correction = Correction(
            fact_check_id=fc.id,
            correction_type=CorrectionType.MINOR,
            request_details="Test correction",
            status=CorrectionStatus.PENDING,
        )
        db_session.add(correction)
        await db_session.commit()

        response = client.get(
            "/api/v1/analytics/correction-rate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert success
        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        assert "total_fact_checks" in data
        assert "total_corrections" in data
        assert "corrections_accepted" in data
        assert "corrections_rejected" in data
        assert "corrections_pending" in data
        assert "correction_rate" in data
        assert "corrections_by_type" in data
        assert data["total_corrections"] == 1
