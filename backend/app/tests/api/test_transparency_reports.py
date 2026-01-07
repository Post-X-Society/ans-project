"""
Tests for transparency reports API endpoints.

Issue #89: Backend - Automated Monthly Transparency Reports (TDD)
EPIC #52: Analytics & EFCSN Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

TDD - Tests written FIRST before implementation.
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.fact_check import FactCheck
from app.models.user import User, UserRole

# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing."""
    user: User = User(
        email="admin@example.com",
        password_hash="hashed_password",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def super_admin_user(db_session: AsyncSession) -> User:
    """Create a super admin user for testing."""
    user: User = User(
        email="superadmin@example.com",
        password_hash="hashed_password",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession) -> User:
    """Create a regular user for testing."""
    user: User = User(
        email="user@example.com",
        password_hash="hashed_password",
        role=UserRole.SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_fact_checks(db_session: AsyncSession) -> list[FactCheck]:
    """Create sample fact-checks for testing."""
    fact_checks: list[FactCheck] = []

    for i in range(5):
        fc: FactCheck = FactCheck(
            title=f"Test Fact Check {i + 1}",
            claim=f"Test claim {i + 1}",
            verdict="true",
            explanation=f"Test explanation {i + 1}",
            sources_count=2,
        )
        db_session.add(fc)
        fact_checks.append(fc)

    await db_session.commit()
    for fc in fact_checks:
        await db_session.refresh(fc)

    return fact_checks


def get_auth_headers(user: User) -> dict[str, str]:
    """Generate auth headers for a user."""
    token: str = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# PUBLIC ENDPOINTS - LIST PUBLISHED REPORTS
# ==============================================================================


class TestListPublishedReports:
    """Tests for listing published transparency reports."""

    def test_list_published_reports_no_auth_required(
        self,
        client: TestClient,
    ) -> None:
        """Test that listing published reports doesn't require authentication."""
        response = client.get("/api/v1/reports/transparency")

        # Should not return 401 Unauthorized
        assert response.status_code != 401

    def test_list_published_reports_returns_empty_list(
        self,
        client: TestClient,
    ) -> None:
        """Test listing returns empty list when no published reports exist."""
        response = client.get("/api/v1/reports/transparency")

        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert "reports" in data
        assert isinstance(data["reports"], list)

    @pytest.mark.asyncio
    async def test_list_published_reports_excludes_unpublished(
        self,
        client: TestClient,
        db_session: AsyncSession,
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test that unpublished reports are not returned in public list."""
        from app.services.transparency_report_service import TransparencyReportService

        service: TransparencyReportService = TransparencyReportService(db_session)
        now: datetime = datetime.now(timezone.utc)

        # Create unpublished report
        await service.generate_monthly_report(now.year, now.month)

        response = client.get("/api/v1/reports/transparency")

        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        # Unpublished report should not appear
        assert len(data["reports"]) == 0


# ==============================================================================
# PUBLIC ENDPOINTS - GET SINGLE REPORT
# ==============================================================================


class TestGetPublishedReport:
    """Tests for getting a single published report."""

    def test_get_published_report_by_id(
        self,
        client: TestClient,
    ) -> None:
        """Test getting a published report by ID."""
        # First need to create and publish a report
        # This test will fail until implementation exists
        report_id: str = str(uuid4())
        response = client.get(f"/api/v1/reports/transparency/{report_id}")

        # Should return 404 for non-existent report
        assert response.status_code == 404

    def test_get_unpublished_report_returns_404_for_public(
        self,
        client: TestClient,
    ) -> None:
        """Test that unpublished reports return 404 for public access."""
        report_id: str = str(uuid4())
        response = client.get(f"/api/v1/reports/transparency/{report_id}")

        assert response.status_code == 404


# ==============================================================================
# PUBLIC ENDPOINTS - EXPORT
# ==============================================================================


class TestExportPublishedReport:
    """Tests for exporting published reports."""

    def test_export_csv_requires_published_report(
        self,
        client: TestClient,
    ) -> None:
        """Test CSV export requires report to be published."""
        report_id: str = str(uuid4())
        response = client.get(f"/api/v1/reports/transparency/{report_id}/csv")

        assert response.status_code == 404

    def test_export_pdf_requires_published_report(
        self,
        client: TestClient,
    ) -> None:
        """Test PDF export requires report to be published."""
        report_id: str = str(uuid4())
        response = client.get(f"/api/v1/reports/transparency/{report_id}/pdf")

        assert response.status_code == 404


# ==============================================================================
# ADMIN ENDPOINTS - GENERATE REPORT
# ==============================================================================


class TestGenerateReport:
    """Tests for generating transparency reports (admin only)."""

    @pytest.mark.asyncio
    async def test_generate_report_requires_admin(
        self,
        client: TestClient,
        regular_user: User,
    ) -> None:
        """Test that generating reports requires admin role."""
        headers: dict[str, str] = get_auth_headers(regular_user)

        response = client.post(
            "/api/v1/reports/transparency/generate",
            headers=headers,
            json={"year": 2025, "month": 1},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_generate_report_as_admin(
        self,
        client: TestClient,
        admin_user: User,
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test admin can generate report."""
        headers: dict[str, str] = get_auth_headers(admin_user)

        now: datetime = datetime.now(timezone.utc)
        response = client.post(
            "/api/v1/reports/transparency/generate",
            headers=headers,
            json={"year": now.year, "month": now.month},
        )

        assert response.status_code == 201
        data: dict[str, Any] = response.json()
        assert "id" in data
        assert data["year"] == now.year
        assert data["month"] == now.month

    @pytest.mark.asyncio
    async def test_generate_report_validates_month(
        self,
        client: TestClient,
        admin_user: User,
    ) -> None:
        """Test that invalid month is rejected."""
        headers: dict[str, str] = get_auth_headers(admin_user)

        response = client.post(
            "/api/v1/reports/transparency/generate",
            headers=headers,
            json={"year": 2025, "month": 13},  # Invalid month
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_generate_report_without_auth_returns_401(
        self,
        client: TestClient,
    ) -> None:
        """Test generating report without auth returns 401."""
        response = client.post(
            "/api/v1/reports/transparency/generate",
            json={"year": 2025, "month": 1},
        )

        assert response.status_code == 401


# ==============================================================================
# ADMIN ENDPOINTS - PUBLISH REPORT
# ==============================================================================


class TestPublishReport:
    """Tests for publishing transparency reports (admin only)."""

    @pytest.mark.asyncio
    async def test_publish_report_requires_admin(
        self,
        client: TestClient,
        regular_user: User,
    ) -> None:
        """Test that publishing requires admin role."""
        headers: dict[str, str] = get_auth_headers(regular_user)
        report_id: str = str(uuid4())

        response = client.patch(
            f"/api/v1/reports/transparency/{report_id}/publish",
            headers=headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_publish_report_as_admin(
        self,
        client: TestClient,
        admin_user: User,
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test admin can publish a report."""
        headers: dict[str, str] = get_auth_headers(admin_user)

        # First generate a report
        now: datetime = datetime.now(timezone.utc)
        gen_response = client.post(
            "/api/v1/reports/transparency/generate",
            headers=headers,
            json={"year": now.year, "month": now.month},
        )
        report_id: str = gen_response.json()["id"]

        # Then publish it
        response = client.patch(
            f"/api/v1/reports/transparency/{report_id}/publish",
            headers=headers,
        )

        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["is_published"] is True

    @pytest.mark.asyncio
    async def test_publish_nonexistent_report_returns_404(
        self,
        client: TestClient,
        admin_user: User,
    ) -> None:
        """Test publishing non-existent report returns 404."""
        headers: dict[str, str] = get_auth_headers(admin_user)
        report_id: str = str(uuid4())

        response = client.patch(
            f"/api/v1/reports/transparency/{report_id}/publish",
            headers=headers,
        )

        assert response.status_code == 404


# ==============================================================================
# ADMIN ENDPOINTS - UNPUBLISH REPORT
# ==============================================================================


class TestUnpublishReport:
    """Tests for unpublishing transparency reports (admin only)."""

    @pytest.mark.asyncio
    async def test_unpublish_report_requires_admin(
        self,
        client: TestClient,
        regular_user: User,
    ) -> None:
        """Test that unpublishing requires admin role."""
        headers: dict[str, str] = get_auth_headers(regular_user)
        report_id: str = str(uuid4())

        response = client.patch(
            f"/api/v1/reports/transparency/{report_id}/unpublish",
            headers=headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unpublish_report_as_admin(
        self,
        client: TestClient,
        admin_user: User,
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test admin can unpublish a report."""
        headers: dict[str, str] = get_auth_headers(admin_user)

        # Generate and publish a report
        now: datetime = datetime.now(timezone.utc)
        gen_response = client.post(
            "/api/v1/reports/transparency/generate",
            headers=headers,
            json={"year": now.year, "month": now.month},
        )
        report_id: str = gen_response.json()["id"]

        client.patch(
            f"/api/v1/reports/transparency/{report_id}/publish",
            headers=headers,
        )

        # Unpublish
        response = client.patch(
            f"/api/v1/reports/transparency/{report_id}/unpublish",
            headers=headers,
        )

        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["is_published"] is False


# ==============================================================================
# ADMIN ENDPOINTS - LIST ALL REPORTS
# ==============================================================================


class TestAdminListReports:
    """Tests for admin listing all reports (including unpublished)."""

    @pytest.mark.asyncio
    async def test_admin_list_all_reports(
        self,
        client: TestClient,
        admin_user: User,
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test admin can list all reports including unpublished."""
        headers: dict[str, str] = get_auth_headers(admin_user)

        # Generate an unpublished report
        now: datetime = datetime.now(timezone.utc)
        client.post(
            "/api/v1/reports/transparency/generate",
            headers=headers,
            json={"year": now.year, "month": now.month},
        )

        # Admin list should include unpublished
        response = client.get(
            "/api/v1/reports/transparency/admin/all",
            headers=headers,
        )

        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert len(data["reports"]) >= 1

    @pytest.mark.asyncio
    async def test_admin_list_requires_admin(
        self,
        client: TestClient,
        regular_user: User,
    ) -> None:
        """Test that admin list requires admin role."""
        headers: dict[str, str] = get_auth_headers(regular_user)

        response = client.get(
            "/api/v1/reports/transparency/admin/all",
            headers=headers,
        )

        assert response.status_code == 403


# ==============================================================================
# ADMIN ENDPOINTS - SEND EMAIL
# ==============================================================================


class TestSendReportEmail:
    """Tests for sending report emails to admins."""

    @pytest.mark.asyncio
    async def test_send_email_requires_admin(
        self,
        client: TestClient,
        regular_user: User,
    ) -> None:
        """Test that sending email requires admin role."""
        headers: dict[str, str] = get_auth_headers(regular_user)
        report_id: str = str(uuid4())

        response = client.post(
            f"/api/v1/reports/transparency/{report_id}/send-email",
            headers=headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_send_email_as_admin(
        self,
        client: TestClient,
        admin_user: User,
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test admin can trigger email sending."""
        headers: dict[str, str] = get_auth_headers(admin_user)

        # Generate a report first
        now: datetime = datetime.now(timezone.utc)
        gen_response = client.post(
            "/api/v1/reports/transparency/generate",
            headers=headers,
            json={"year": now.year, "month": now.month},
        )
        report_id: str = gen_response.json()["id"]

        # Send email
        with patch("app.services.transparency_report_service.email_service") as mock_email:
            mock_email.queue_email = MagicMock(return_value="task-123")

            response = client.post(
                f"/api/v1/reports/transparency/{report_id}/send-email",
                headers=headers,
            )

            assert response.status_code == 200
            data: dict[str, Any] = response.json()
            assert "emails_queued" in data
