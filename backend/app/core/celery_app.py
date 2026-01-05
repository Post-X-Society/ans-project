"""
Celery application configuration for async task processing

Used for email queuing, scheduled tasks, and background jobs
"""

from celery import Celery  # type: ignore[import-not-found]

from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "ans_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.email_tasks"],  # Auto-discover tasks
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Email task configuration
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "emails"},
    },
    task_acks_late=True,  # Acknowledge after task completion
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
)
