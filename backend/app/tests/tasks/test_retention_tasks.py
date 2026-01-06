"""
Tests for retention cleanup Celery task

Issue #91: Data Retention Policies & Auto-Cleanup
Tests for scheduled retention cleanup task configuration
"""

from typing import Any


class TestRetentionCleanupTask:
    """Test retention cleanup Celery Beat schedule configuration"""

    def test_beat_schedule_is_configured(self) -> None:
        """Test that Celery Beat schedule includes retention cleanup"""
        from app.core.celery_app import celery_app

        # Check beat schedule exists
        assert hasattr(celery_app.conf, "beat_schedule")
        assert "retention-cleanup-daily" in celery_app.conf.beat_schedule

        # Check schedule configuration
        schedule_config: dict[str, Any] = celery_app.conf.beat_schedule["retention-cleanup-daily"]
        assert schedule_config["task"] == "app.tasks.retention_tasks.run_retention_cleanup"
        assert schedule_config["schedule"] == 86400.0  # Daily (24 hours)
        assert schedule_config["options"]["queue"] == "maintenance"
