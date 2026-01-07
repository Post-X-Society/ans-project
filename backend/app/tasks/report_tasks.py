"""
Celery tasks for transparency report automation.

Issue #89: Backend - Automated Monthly Transparency Reports (TDD)
EPIC #52: Analytics & EFCSN Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

Handles:
- Automated monthly report generation
- Report publication
- Email notification to administrators
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from celery import Task

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    name="app.tasks.report_tasks.generate_monthly_report_task",
)
def generate_monthly_report_task(
    self: "Task[Any, Any]",
    year: Optional[int] = None,
    month: Optional[int] = None,
    auto_publish: bool = True,
    notify_admins: bool = True,
) -> dict[str, Any]:
    """
    Celery task to generate monthly transparency report.

    By default, generates report for the previous month if year/month not specified.

    Args:
        self: Celery task instance (bound)
        year: Report year (optional, defaults to previous month's year)
        month: Report month (optional, defaults to previous month)
        auto_publish: If True, automatically publish the report
        notify_admins: If True, send email notifications to admins

    Returns:
        Dictionary with task results

    Retry Logic:
        - Max retries: 3
        - Retry delay: 300 seconds (5 minutes)
    """
    try:
        # Run async code in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result: dict[str, Any] = loop.run_until_complete(
                _generate_report_async(year, month, auto_publish, notify_admins)
            )
            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Failed to generate monthly report: {e}")
        raise self.retry(exc=e) from e


async def _generate_report_async(
    year: Optional[int],
    month: Optional[int],
    auto_publish: bool,
    notify_admins: bool,
) -> dict[str, Any]:
    """
    Async implementation of report generation.

    Args:
        year: Report year
        month: Report month
        auto_publish: Whether to publish automatically
        notify_admins: Whether to send email notifications

    Returns:
        Dictionary with results
    """
    from app.services.transparency_report_service import TransparencyReportService

    # Calculate target month (previous month if not specified)
    now: datetime = datetime.now(timezone.utc)

    if year is None or month is None:
        # Default to previous month
        if now.month == 1:
            target_year: int = now.year - 1
            target_month: int = 12
        else:
            target_year = now.year
            target_month = now.month - 1
    else:
        target_year = year
        target_month = month

    logger.info(f"Generating transparency report for {target_year}-{target_month:02d}")

    async with AsyncSessionLocal() as session:
        service = TransparencyReportService(session)

        # Generate report
        report = await service.generate_monthly_report(
            target_year, target_month, force_regenerate=True
        )

        result: dict[str, Any] = {
            "report_id": str(report.id),
            "year": target_year,
            "month": target_month,
            "generated_at": report.generated_at.isoformat(),
            "published": False,
            "emails_sent": 0,
        }

        # Auto-publish if enabled
        if auto_publish:
            await service.publish_report(report.id)
            result["published"] = True
            logger.info(f"Auto-published report {report.id}")

        # Send notifications if enabled
        if notify_admins:
            email_result: dict[str, Any] = await service.send_report_to_admins(report.id)
            result["emails_sent"] = email_result.get("emails_queued", 0)
            logger.info(f"Sent {result['emails_sent']} notification emails")

    return result


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="app.tasks.report_tasks.send_report_email_task",
)
def send_report_email_task(
    self: "Task[Any, Any]",
    report_id: str,
) -> dict[str, Any]:
    """
    Celery task to send report email notifications.

    Args:
        self: Celery task instance (bound)
        report_id: UUID of the report to send

    Returns:
        Dictionary with email sending results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result: dict[str, Any] = loop.run_until_complete(_send_report_email_async(report_id))
            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Failed to send report email: {e}")
        raise self.retry(exc=e) from e


async def _send_report_email_async(report_id: str) -> dict[str, Any]:
    """
    Async implementation of report email sending.

    Args:
        report_id: UUID of the report

    Returns:
        Dictionary with results
    """
    from uuid import UUID

    from app.services.transparency_report_service import TransparencyReportService

    async with AsyncSessionLocal() as session:
        service = TransparencyReportService(session)
        result: dict[str, Any] = await service.send_report_to_admins(UUID(report_id))

    return result
