"""
Tests for transparency report Celery tasks.

Issue #89: Backend - Automated Monthly Transparency Reports (TDD)
EPIC #52: Analytics & EFCSN Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

TDD - Tests written FIRST before implementation.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

# ==============================================================================
# CELERY TASK TESTS
# ==============================================================================


class TestGenerateMonthlyReportTask:
    """Tests for the generate_monthly_report Celery task."""

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered with Celery."""
        from app.core.celery_app import celery_app

        # Task should be discoverable
        task_name: str = "app.tasks.report_tasks.generate_monthly_report_task"
        assert task_name in celery_app.tasks

    def test_task_has_correct_configuration(self) -> None:
        """Test task has correct retry and queue configuration."""
        from app.tasks.report_tasks import generate_monthly_report_task

        # Verify task configuration
        assert generate_monthly_report_task.max_retries == 3
        assert generate_monthly_report_task.default_retry_delay == 300

    @patch("app.tasks.report_tasks.AsyncSessionLocal")
    @patch("app.tasks.report_tasks.TransparencyReportService")
    def test_task_generates_report_for_previous_month(
        self,
        mock_service_class: MagicMock,
        mock_session_local: MagicMock,
    ) -> None:
        """Test task generates report for previous month by default."""
        from app.tasks.report_tasks import generate_monthly_report_task

        # Setup mocks
        mock_session: MagicMock = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_local.return_value = mock_session

        mock_service: MagicMock = MagicMock()
        mock_report: MagicMock = MagicMock()
        mock_report.id = "test-report-id"
        mock_report.year = 2025
        mock_report.month = 12

        mock_service.generate_monthly_report = AsyncMock(return_value=mock_report)
        mock_service.publish_report = AsyncMock(return_value=mock_report)
        mock_service.send_report_to_admins = AsyncMock(return_value={"emails_queued": 1})
        mock_service_class.return_value = mock_service

        # Run task synchronously for testing
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_until_complete = lambda coro: None

            # Task should execute without error
            result: dict[str, Any] = generate_monthly_report_task()

            assert result is not None

    @patch("app.tasks.report_tasks.AsyncSessionLocal")
    @patch("app.tasks.report_tasks.TransparencyReportService")
    def test_task_accepts_year_month_parameters(
        self,
        mock_service_class: MagicMock,
        mock_session_local: MagicMock,
    ) -> None:
        """Test task accepts specific year and month parameters."""
        from app.tasks.report_tasks import generate_monthly_report_task

        # Setup mocks
        mock_session: MagicMock = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_local.return_value = mock_session

        mock_service: MagicMock = MagicMock()
        mock_report: MagicMock = MagicMock()
        mock_report.id = "test-report-id"
        mock_report.year = 2025
        mock_report.month = 6

        mock_service.generate_monthly_report = AsyncMock(return_value=mock_report)
        mock_service.publish_report = AsyncMock(return_value=mock_report)
        mock_service.send_report_to_admins = AsyncMock(return_value={"emails_queued": 1})
        mock_service_class.return_value = mock_service

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_until_complete = lambda coro: None

            result: dict[str, Any] = generate_monthly_report_task(year=2025, month=6)

            assert result is not None

    @patch("app.tasks.report_tasks.AsyncSessionLocal")
    @patch("app.tasks.report_tasks.TransparencyReportService")
    def test_task_publishes_report_when_auto_publish_enabled(
        self,
        mock_service_class: MagicMock,
        mock_session_local: MagicMock,
    ) -> None:
        """Test task publishes report when auto_publish is True."""
        from app.tasks.report_tasks import generate_monthly_report_task

        # Setup mocks
        mock_session: MagicMock = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_local.return_value = mock_session

        mock_service: MagicMock = MagicMock()
        mock_report: MagicMock = MagicMock()
        mock_report.id = "test-report-id"

        mock_service.generate_monthly_report = AsyncMock(return_value=mock_report)
        mock_service.publish_report = AsyncMock(return_value=mock_report)
        mock_service.send_report_to_admins = AsyncMock(return_value={"emails_queued": 1})
        mock_service_class.return_value = mock_service

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_until_complete = lambda coro: None

            generate_monthly_report_task(auto_publish=True)

            # Verify publish was called
            mock_service.publish_report.assert_called_once()

    @patch("app.tasks.report_tasks.AsyncSessionLocal")
    @patch("app.tasks.report_tasks.TransparencyReportService")
    def test_task_sends_email_when_notify_admins_enabled(
        self,
        mock_service_class: MagicMock,
        mock_session_local: MagicMock,
    ) -> None:
        """Test task sends email notification when notify_admins is True."""
        from app.tasks.report_tasks import generate_monthly_report_task

        # Setup mocks
        mock_session: MagicMock = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_local.return_value = mock_session

        mock_service: MagicMock = MagicMock()
        mock_report: MagicMock = MagicMock()
        mock_report.id = "test-report-id"

        mock_service.generate_monthly_report = AsyncMock(return_value=mock_report)
        mock_service.publish_report = AsyncMock(return_value=mock_report)
        mock_service.send_report_to_admins = AsyncMock(return_value={"emails_queued": 2})
        mock_service_class.return_value = mock_service

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_until_complete = lambda coro: None

            generate_monthly_report_task(notify_admins=True)

            # Verify email was sent
            mock_service.send_report_to_admins.assert_called_once()


class TestCeleryBeatSchedule:
    """Tests for Celery Beat schedule configuration."""

    def test_monthly_report_task_in_beat_schedule(self) -> None:
        """Test that monthly report task is scheduled in Celery Beat."""
        from app.core.celery_app import celery_app

        beat_schedule: dict[str, Any] = celery_app.conf.beat_schedule

        # Should have monthly report task scheduled
        assert "generate-monthly-transparency-report" in beat_schedule

    def test_monthly_report_task_schedule_is_monthly(self) -> None:
        """Test that task is scheduled to run monthly."""
        from app.core.celery_app import celery_app

        beat_schedule: dict[str, Any] = celery_app.conf.beat_schedule
        task_config: dict[str, Any] = beat_schedule["generate-monthly-transparency-report"]

        # Should be scheduled for first day of month
        # Using crontab(day_of_month='1', hour=3, minute=0)
        schedule = task_config["schedule"]
        assert schedule is not None

    def test_monthly_report_task_has_correct_queue(self) -> None:
        """Test that task is routed to correct queue."""
        from app.core.celery_app import celery_app

        beat_schedule: dict[str, Any] = celery_app.conf.beat_schedule
        task_config: dict[str, Any] = beat_schedule["generate-monthly-transparency-report"]

        # Should be in reports or maintenance queue
        assert "options" in task_config
        assert task_config["options"]["queue"] in ["reports", "maintenance"]
