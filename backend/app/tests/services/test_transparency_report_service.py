"""
Tests for TransparencyReportService.

Issue #89: Backend - Automated Monthly Transparency Reports (TDD)
EPIC #52: Analytics & EFCSN Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

TDD - Tests written FIRST before implementation.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fact_check import FactCheck
from app.models.source import Source, SourceRelevance, SourceType
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
async def sample_fact_checks(db_session: AsyncSession) -> list[FactCheck]:
    """Create sample fact-checks for testing."""
    fact_checks: list[FactCheck] = []
    verdicts: list[str] = ["true", "false", "partly_false", "true", "false"]

    for i, verdict in enumerate(verdicts):
        fc: FactCheck = FactCheck(
            title=f"Test Fact Check {i + 1}",
            claim=f"Test claim {i + 1}",
            verdict=verdict,
            explanation=f"Test explanation {i + 1}",
            sources_count=2,
        )
        db_session.add(fc)
        fact_checks.append(fc)

    await db_session.commit()
    for fc in fact_checks:
        await db_session.refresh(fc)

    return fact_checks


@pytest_asyncio.fixture
async def sample_sources(
    db_session: AsyncSession, sample_fact_checks: list[FactCheck]
) -> list[Source]:
    """Create sample sources for testing."""
    sources: list[Source] = []

    for fc in sample_fact_checks:
        for j in range(2):
            source: Source = Source(
                fact_check_id=fc.id,
                source_type=SourceType.PRIMARY if j == 0 else SourceType.SECONDARY,
                title=f"Source {j + 1} for FC {fc.id}",
                url=f"https://example.com/source-{fc.id}-{j}",
                credibility_score=4,
                relevance=SourceRelevance.SUPPORTS,
            )
            db_session.add(source)
            sources.append(source)

    await db_session.commit()
    return sources


# ==============================================================================
# SERVICE TESTS - REPORT GENERATION
# ==============================================================================


class TestTransparencyReportServiceGeneration:
    """Tests for transparency report generation."""

    @pytest.mark.asyncio
    async def test_generate_monthly_report_creates_report(
        self,
        db_session: AsyncSession,
        sample_fact_checks: list[FactCheck],
        sample_sources: list[Source],
    ) -> None:
        """Test that generate_monthly_report creates a report record."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test that report includes fact-check publication counts."""
        from app.services.transparency_report_service import TransparencyReportService

        service: TransparencyReportService = TransparencyReportService(db_session)

        now: datetime = datetime.now(timezone.utc)
        report = await service.generate_monthly_report(now.year, now.month)

        # Verify fact-check counts in report data
        assert "monthly_fact_checks" in report.report_data
        assert report.report_data["monthly_fact_checks"]["total_count"] >= 0

    @pytest.mark.asyncio
    async def test_generate_monthly_report_includes_rating_distribution(
        self,
        db_session: AsyncSession,
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test that report includes rating distribution."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
        sample_sources: list[Source],
    ) -> None:
        """Test that report includes source quality metrics."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test that report includes correction rate metrics."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test that report includes EFCSN compliance status."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test that generating report for same month returns existing report."""
        from app.services.transparency_report_service import TransparencyReportService

        service: TransparencyReportService = TransparencyReportService(db_session)

        now: datetime = datetime.now(timezone.utc)

        # Generate first report
        report1 = await service.generate_monthly_report(now.year, now.month)

        # Generate again for same month
        report2 = await service.generate_monthly_report(now.year, now.month, force_regenerate=False)

        # Should return same report
        assert report1.id == report2.id

    @pytest.mark.asyncio
    async def test_generate_monthly_report_force_regenerate(
        self,
        db_session: AsyncSession,
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test that force_regenerate creates new report data."""
        from app.services.transparency_report_service import TransparencyReportService

        service: TransparencyReportService = TransparencyReportService(db_session)

        now: datetime = datetime.now(timezone.utc)

        # Generate first report
        report1 = await service.generate_monthly_report(now.year, now.month)
        original_generated_at = report1.generated_at

        # Force regenerate
        report2 = await service.generate_monthly_report(now.year, now.month, force_regenerate=True)

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test retrieving report by ID."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test retrieving report by year and month."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test listing only published reports."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test listing all reports including unpublished."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test publishing a report."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test unpublishing a report."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test exporting report as CSV."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test exporting report as PDF."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test sending report to admin users."""
        from app.services.transparency_report_service import TransparencyReportService

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
        sample_fact_checks: list[FactCheck],
    ) -> None:
        """Test that admin email includes PDF and CSV attachments info."""
        from app.services.transparency_report_service import TransparencyReportService

        service: TransparencyReportService = TransparencyReportService(db_session)

        now: datetime = datetime.now(timezone.utc)
        report = await service.generate_monthly_report(now.year, now.month)

        with patch("app.services.transparency_report_service.email_service") as mock_email:
            mock_email.queue_email = MagicMock(return_value="task-123")

            result = await service.send_report_to_admins(report.id)

            # Verify result contains attachment info
            assert "pdf_generated" in result
            assert "csv_generated" in result
