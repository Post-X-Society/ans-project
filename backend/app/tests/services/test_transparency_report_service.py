"""
Tests for TransparencyReportService.

Issue #89: Backend - Automated Monthly Transparency Reports (TDD)
EPIC #52: Analytics & EFCSN Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

TDD - Tests written FIRST before implementation.
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

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


def get_mock_analytics_data() -> dict[str, Any]:
    """Get mock analytics data for testing."""
    return {
        "report_period": {
            "year": 2025,
            "month": 12,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "monthly_fact_checks": {
            "months": [{"year": 2025, "month": 12, "count": 5, "meets_efcsn_minimum": True}],
            "total_count": 5,
            "average_per_month": 5.0,
        },
        "time_to_publication": {
            "average_hours": 24.0,
            "median_hours": 20.0,
            "min_hours": 2.0,
            "max_hours": 72.0,
            "total_published": 5,
        },
        "rating_distribution": {
            "ratings": [
                {"rating": "true", "count": 2, "percentage": 40.0},
                {"rating": "false", "count": 2, "percentage": 40.0},
                {"rating": "partly_false", "count": 1, "percentage": 20.0},
            ],
            "total_count": 5,
        },
        "source_quality": {
            "average_sources_per_fact_check": 2.5,
            "average_credibility_score": 4.0,
            "total_sources": 10,
            "sources_by_type": {"primary": 5, "secondary": 5},
            "sources_by_relevance": {"supports": 8, "contradicts": 2},
            "fact_checks_meeting_minimum": 5,
            "fact_checks_below_minimum": 0,
        },
        "correction_rate": {
            "total_fact_checks": 5,
            "total_corrections": 1,
            "corrections_accepted": 1,
            "corrections_rejected": 0,
            "corrections_pending": 0,
            "correction_rate": 0.2,
            "corrections_by_type": {"minor": 1},
        },
        "efcsn_compliance": {
            "overall_status": "compliant",
            "checklist": [
                {
                    "requirement": "Monthly fact-check minimum",
                    "status": "compliant",
                    "details": "5 fact-checks published this month",
                    "value": "5",
                    "threshold": "4",
                }
            ],
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "compliance_score": 100.0,
        },
    }


# ==============================================================================
# SERVICE TESTS - REPORT GENERATION
# ==============================================================================


class TestTransparencyReportServiceGeneration:
    """Tests for transparency report generation."""

    @pytest.mark.asyncio
    async def test_generate_monthly_report_creates_report(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test that generate_monthly_report creates a report record."""
        from app.services.transparency_report_service import TransparencyReportService

        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=get_mock_analytics_data(),
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            # Generate report for current month
            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)

            # Verify report was created
            assert report is not None
            assert report.id is not None
            assert report.year == now.year
            assert report.month == now.month
            assert report.is_published is False
            assert report.report_data is not None

    @pytest.mark.asyncio
    async def test_generate_monthly_report_includes_fact_check_counts(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test that report includes fact-check publication counts."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)

            # Verify fact-check counts in report data
            assert "monthly_fact_checks" in report.report_data
            assert report.report_data["monthly_fact_checks"]["total_count"] == 5

    @pytest.mark.asyncio
    async def test_generate_monthly_report_includes_rating_distribution(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test that report includes rating distribution."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)

            # Verify rating distribution in report
            assert "rating_distribution" in report.report_data
            assert "ratings" in report.report_data["rating_distribution"]

    @pytest.mark.asyncio
    async def test_generate_monthly_report_includes_source_quality(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test that report includes source quality metrics."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)

            # Verify source quality metrics
            assert "source_quality" in report.report_data
            assert "total_sources" in report.report_data["source_quality"]

    @pytest.mark.asyncio
    async def test_generate_monthly_report_includes_correction_rate(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test that report includes correction rate metrics."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)

            # Verify correction rate metrics
            assert "correction_rate" in report.report_data
            assert "total_corrections" in report.report_data["correction_rate"]

    @pytest.mark.asyncio
    async def test_generate_monthly_report_includes_efcsn_compliance(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test that report includes EFCSN compliance status."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)

            # Verify EFCSN compliance in report
            assert "efcsn_compliance" in report.report_data
            assert "overall_status" in report.report_data["efcsn_compliance"]
            assert "checklist" in report.report_data["efcsn_compliance"]

    @pytest.mark.asyncio
    async def test_generate_monthly_report_prevents_duplicates(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test that generating report for same month returns existing report."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)

            # Generate first report
            report1 = await service.generate_monthly_report(now.year, now.month)

            # Generate again for same month
            report2 = await service.generate_monthly_report(
                now.year, now.month, force_regenerate=False
            )

            # Should return same report
            assert report1.id == report2.id

    @pytest.mark.asyncio
    async def test_generate_monthly_report_force_regenerate(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test that force_regenerate creates new report data."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)

            # Generate first report
            report1 = await service.generate_monthly_report(now.year, now.month)
            original_generated_at = report1.generated_at

            # Force regenerate
            report2 = await service.generate_monthly_report(
                now.year, now.month, force_regenerate=True
            )

            # Should update report data
            assert report2.id == report1.id
            assert report2.generated_at >= original_generated_at


# ==============================================================================
# SERVICE TESTS - REPORT RETRIEVAL
# ==============================================================================


class TestTransparencyReportServiceRetrieval:
    """Tests for retrieving transparency reports."""

    @pytest.mark.asyncio
    async def test_get_report_by_id(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test retrieving report by ID."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            created_report = await service.generate_monthly_report(now.year, now.month)

            # Retrieve by ID
            retrieved_report = await service.get_report_by_id(created_report.id)

            assert retrieved_report is not None
            assert retrieved_report.id == created_report.id

    @pytest.mark.asyncio
    async def test_get_report_by_id_not_found(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test retrieving non-existent report returns None."""
        from app.services.transparency_report_service import TransparencyReportService

        service: TransparencyReportService = TransparencyReportService(db_session)

        result = await service.get_report_by_id(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_report_by_month(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test retrieving report by year and month."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            created_report = await service.generate_monthly_report(now.year, now.month)

            # Retrieve by year/month
            retrieved_report = await service.get_report_by_month(now.year, now.month)

            assert retrieved_report is not None
            assert retrieved_report.id == created_report.id

    @pytest.mark.asyncio
    async def test_list_published_reports(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test listing only published reports."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)

            # Create and publish a report
            report = await service.generate_monthly_report(now.year, now.month)
            await service.publish_report(report.id)

            # List published reports
            published_reports = await service.list_reports(published_only=True)

            assert len(published_reports) == 1
            assert published_reports[0].is_published is True

    @pytest.mark.asyncio
    async def test_list_all_reports(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test listing all reports including unpublished."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)

            # Create report (unpublished by default)
            await service.generate_monthly_report(now.year, now.month)

            # List all reports
            all_reports = await service.list_reports(published_only=False)

            assert len(all_reports) >= 1


# ==============================================================================
# SERVICE TESTS - PUBLISHING
# ==============================================================================


class TestTransparencyReportServicePublishing:
    """Tests for publishing transparency reports."""

    @pytest.mark.asyncio
    async def test_publish_report(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test publishing a report."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)

            # Publish
            published_report = await service.publish_report(report.id)

            assert published_report.is_published is True
            assert published_report.published_at is not None

    @pytest.mark.asyncio
    async def test_unpublish_report(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test unpublishing a report."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)
            await service.publish_report(report.id)

            # Unpublish
            unpublished_report = await service.unpublish_report(report.id)

            assert unpublished_report.is_published is False

    @pytest.mark.asyncio
    async def test_publish_nonexistent_report_raises_error(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test publishing non-existent report raises ValueError."""
        from app.services.transparency_report_service import TransparencyReportService

        service: TransparencyReportService = TransparencyReportService(db_session)

        with pytest.raises(ValueError, match="Report not found"):
            await service.publish_report(uuid4())


# ==============================================================================
# SERVICE TESTS - EXPORT
# ==============================================================================


class TestTransparencyReportServiceExport:
    """Tests for exporting transparency reports."""

    @pytest.mark.asyncio
    async def test_export_report_csv(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test exporting report as CSV."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)

            # Export as CSV
            csv_content: str = await service.export_to_csv(report.id)

            # Verify CSV content
            assert csv_content is not None
            assert len(csv_content) > 0
            assert "," in csv_content  # CSV should contain commas

    @pytest.mark.asyncio
    async def test_export_report_pdf(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test exporting report as PDF."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)

            # Export as PDF
            pdf_content: bytes = await service.export_to_pdf(report.id)

            # Verify PDF content (PDF files start with %PDF)
            assert pdf_content is not None
            assert len(pdf_content) > 0
            assert pdf_content[:4] == b"%PDF"

    @pytest.mark.asyncio
    async def test_export_nonexistent_report_raises_error(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test exporting non-existent report raises ValueError."""
        from app.services.transparency_report_service import TransparencyReportService

        service: TransparencyReportService = TransparencyReportService(db_session)

        with pytest.raises(ValueError, match="Report not found"):
            await service.export_to_csv(uuid4())


# ==============================================================================
# SERVICE TESTS - EMAIL DISTRIBUTION
# ==============================================================================


class TestTransparencyReportServiceEmail:
    """Tests for email distribution of transparency reports."""

    @pytest.mark.asyncio
    async def test_send_report_to_admins(
        self,
        db_session: AsyncSession,
        admin_user: User,
    ) -> None:
        """Test sending report to admin users."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)

            # Mock email service
            with patch("app.services.transparency_report_service.email_service") as mock_email:
                mock_email.queue_email = MagicMock(return_value="task-123")

                result = await service.send_report_to_admins(report.id)

                # Verify email was queued
                assert result["emails_queued"] >= 1
                mock_email.queue_email.assert_called()

    @pytest.mark.asyncio
    async def test_send_report_to_admins_includes_attachments(
        self,
        db_session: AsyncSession,
        admin_user: User,
    ) -> None:
        """Test that admin email includes PDF and CSV attachments info."""
        from app.services.transparency_report_service import TransparencyReportService

        mock_data = get_mock_analytics_data()
        with patch.object(
            TransparencyReportService,
            "_generate_report_data",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            service: TransparencyReportService = TransparencyReportService(db_session)

            now: datetime = datetime.now(timezone.utc)
            report = await service.generate_monthly_report(now.year, now.month)

            with patch("app.services.transparency_report_service.email_service") as mock_email:
                mock_email.queue_email = MagicMock(return_value="task-123")

                result = await service.send_report_to_admins(report.id)

                # Verify result contains attachment info
                assert "pdf_generated" in result
                assert "csv_generated" in result
