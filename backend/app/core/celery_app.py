"""
Celery application configuration for async task processing

Used for email queuing, scheduled tasks, and background jobs

Issue #89: Added report_tasks for automated monthly transparency reports
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "ans_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.retention_tasks",
        "app.tasks.report_tasks",  # Issue #89: Monthly transparency reports
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task routing configuration
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "emails"},
        "app.tasks.report_tasks.*": {"queue": "reports"},  # Issue #89
    },
    task_acks_late=True,  # Acknowledge after task completion
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Issue #91: Daily data retention cleanup
    "retention-cleanup-daily": {
        "task": "app.tasks.retention_tasks.run_retention_cleanup",
        "schedule": 86400.0,  # Run daily (24 hours in seconds)
        # Alternative: use crontab for specific time
        # "schedule": crontab(hour=2, minute=0),  # Run daily at 2 AM UTC
        "options": {"queue": "maintenance"},
    },
    # Issue #89: Monthly transparency report generation
    # Runs on the 1st day of each month at 3 AM UTC
    "generate-monthly-transparency-report": {
        "task": "app.tasks.report_tasks.generate_monthly_report_task",
        "schedule": crontab(day_of_month="1", hour=3, minute=0),
        "kwargs": {
            "auto_publish": True,
            "notify_admins": True,
        },
        "options": {"queue": "reports"},
    },
}
