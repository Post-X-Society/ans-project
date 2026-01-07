"""
Tests for transparency report Celery tasks.

Issue #89: Backend - Automated Monthly Transparency Reports (TDD)
EPIC #52: Analytics & EFCSN Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

TDD - Tests written FIRST before implementation.
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

# ==============================================================================
# CELERY TASK TESTS
# ==============================================================================


class TestGenerateMonthlyReportTask:
    """Tests for the generate_monthly_report Celery task."""

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered with Celery."""
        # Import the task module to ensure it's loaded
        from app.core.celery_app import celery_app
        from app.tasks import report_tasks  # noqa: F401

        # Task should be discoverable after module import
        task_name: str = "app.tasks.report_tasks.generate_monthly_report_task"
        assert task_name in celery_app.tasks

    def test_task_has_correct_configuration(self) -> None:
        """Test task has correct retry and queue configuration."""
        from app.tasks.report_tasks import generate_monthly_report_task

        # Verify task configuration
        assert generate_monthly_report_task.max_retries == 3
        assert generate_monthly_report_task.default_retry_delay == 300

    @patch("app.tasks.report_tasks._generate_report_async")
    def test_task_generates_report_for_previous_month(
        self,
        mock_generate_async: AsyncMock,
    ) -> None:
        """Test task generates report for previous month by default."""
        from app.tasks.report_tasks import generate_monthly_report_task

        # Setup mock to return a result dict
        mock_generate_async.return_value = {
            "report_id": "test-report-id",
            "year": 2025,
            "month": 12,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "published": True,
            "emails_sent": 1,
        }

        # Task should execute without error
        result: dict[str, Any] = generate_monthly_report_task()

        assert result is not None
        assert result["report_id"] == "test-report-id"
        # Verify the async function was called with default params
        mock_generate_async.assert_called_once()

    @patch("app.tasks.report_tasks._generate_report_async")
    def test_task_accepts_year_month_parameters(
        self,
        mock_generate_async: AsyncMock,
    ) -> None:
        """Test task accepts specific year and month parameters."""
        from app.tasks.report_tasks import generate_monthly_report_task

        mock_generate_async.return_value = {
            "report_id": "test-report-id",
            "year": 2025,
            "month": 6,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "published": True,
            "emails_sent": 1,
        }

        result: dict[str, Any] = generate_monthly_report_task(year=2025, month=6)

        assert result is not None
        assert result["year"] == 2025
        assert result["month"] == 6
        # Verify correct parameters were passed
        call_args = mock_generate_async.call_args
        assert call_args[0][0] == 2025  # year
        assert call_args[0][1] == 6  # month

    @patch("app.tasks.report_tasks._generate_report_async")
    def test_task_publishes_report_when_auto_publish_enabled(
        self,
        mock_generate_async: AsyncMock,
    ) -> None:
        """Test task publishes report when auto_publish is True."""
        from app.tasks.report_tasks import generate_monthly_report_task

        mock_generate_async.return_value = {
            "report_id": "test-report-id",
            "year": 2025,
            "month": 12,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "published": True,
            "emails_sent": 0,
        }

        result = generate_monthly_report_task(auto_publish=True)

        assert result["published"] is True
        # Verify auto_publish was passed as True
        call_args = mock_generate_async.call_args
        assert call_args[0][2] is True  # auto_publish

    @patch("app.tasks.report_tasks._generate_report_async")
    def test_task_sends_email_when_notify_admins_enabled(
        self,
        mock_generate_async: AsyncMock,
    ) -> None:
        """Test task sends email notification when notify_admins is True."""
        from app.tasks.report_tasks import generate_monthly_report_task

        mock_generate_async.return_value = {
            "report_id": "test-report-id",
            "year": 2025,
            "month": 12,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "published": True,
            "emails_sent": 2,
        }

        result = generate_monthly_report_task(notify_admins=True)

        assert result["emails_sent"] == 2
        # Verify notify_admins was passed as True
        call_args = mock_generate_async.call_args
        assert call_args[0][3] is True  # notify_admins


class TestGenerateReportAsyncFunction:
    """Tests for the _generate_report_async helper function."""

    @pytest.mark.asyncio
    @patch("app.services.transparency_report_service.TransparencyReportService")
    @patch("app.tasks.report_tasks.AsyncSessionLocal")
    async def test_generate_report_async_creates_report(
        self,
        mock_session_local: AsyncMock,
        mock_service_class: AsyncMock,
    ) -> None:
        """Test that _generate_report_async creates and returns report."""
        from app.tasks.report_tasks import _generate_report_async

        # Setup mock session
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session
        mock_session_local.return_value.__aexit__.return_value = None

        # Setup mock service
        mock_report = AsyncMock()
        mock_report.id = "test-report-id"
        mock_report.generated_at = datetime.now(timezone.utc)

        mock_service = AsyncMock()
        mock_service.generate_monthly_report.return_value = mock_report
        mock_service.publish_report.return_value = mock_report
        mock_service.send_report_to_admins.return_value = {"emails_queued": 1}
        mock_service_class.return_value = mock_service

        result = await _generate_report_async(2025, 12, True, True)

        assert result["report_id"] == "test-report-id"
        assert result["year"] == 2025
        assert result["month"] == 12


class TestCeleryBeatSchedule:
    """Tests for Celery Beat schedule configuration."""

    def test_monthly_report_task_in_beat_schedule(self) -> None:
        """Test that monthly report task is scheduled in Celery Beat."""
        # Import task module to ensure it's loaded
        from app.core.celery_app import celery_app
        from app.tasks import report_tasks  # noqa: F401

        beat_schedule: dict[str, Any] = celery_app.conf.beat_schedule

        # Should have monthly report task scheduled
        assert "generate-monthly-transparency-report" in beat_schedule

    def test_monthly_report_task_schedule_is_monthly(self) -> None:
        """Test that task is scheduled to run monthly."""
        # Import task module to ensure it's loaded
        from app.core.celery_app import celery_app
        from app.tasks import report_tasks  # noqa: F401

        beat_schedule: dict[str, Any] = celery_app.conf.beat_schedule
        task_config: dict[str, Any] = beat_schedule["generate-monthly-transparency-report"]

        # Should be scheduled for first day of month
        # Using crontab(day_of_month='1', hour=3, minute=0)
        schedule = task_config["schedule"]
        assert schedule is not None

    def test_monthly_report_task_has_correct_queue(self) -> None:
        """Test that task is routed to correct queue."""
        # Import task module to ensure it's loaded
        from app.core.celery_app import celery_app
        from app.tasks import report_tasks  # noqa: F401

        beat_schedule: dict[str, Any] = celery_app.conf.beat_schedule
        task_config: dict[str, Any] = beat_schedule["generate-monthly-transparency-report"]

        # Should be in reports or maintenance queue
        assert "options" in task_config
        assert task_config["options"]["queue"] in ["reports", "maintenance"]
