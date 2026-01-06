"""
Celery tasks for data retention and cleanup

Issue #91: Data Retention Policies & Auto-Cleanup
Scheduled task to automatically clean up old data per GDPR requirements
"""

import logging
from typing import Any

from celery import Task

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def run_retention_cleanup(self: "Task[Any, Any]") -> dict[str, Any]:
    """
    Celery task to run data retention cleanup

    Executes all retention cleanup tasks:
    - Unpublished submissions older than configured period
    - Rejected claims older than configured period
    - Resolved correction requests older than configured period

    Scheduled to run daily at 2 AM UTC via Celery Beat

    Returns:
        Dictionary with cleanup summary:
        {
            "success": bool,
            "unpublished_submissions": int,
            "rejected_claims": int,
            "correction_requests": int,
            "total_deleted": int,
            "error": str | None
        }

    Retry Logic:
        - Max retries: 3
        - Retry delay: 5 minutes (300 seconds)
        - Auto-retry on database errors
    """
    import asyncio

    from app.core.database import AsyncSessionLocal
    from app.services.retention_service import RetentionService

    async def _run_cleanup() -> dict[str, Any]:
        """Async wrapper for cleanup execution"""
        async with AsyncSessionLocal() as db:
            try:
                service: RetentionService = RetentionService()
                summary: dict[str, int] = await service.run_all(db)

                total_deleted: int = sum(summary.values())

                logger.info(
                    f"Retention cleanup completed: {total_deleted} records deleted",
                    extra={"summary": summary},
                )

                return {
                    "success": True,
                    "unpublished_submissions": summary.get("unpublished_submissions", 0),
                    "rejected_claims": summary.get("rejected_claims", 0),
                    "correction_requests": summary.get("correction_requests", 0),
                    "total_deleted": total_deleted,
                    "error": None,
                }

            except Exception as exc:
                logger.error(f"Retention cleanup failed: {exc}", exc_info=True)
                return {
                    "success": False,
                    "unpublished_submissions": 0,
                    "rejected_claims": 0,
                    "correction_requests": 0,
                    "total_deleted": 0,
                    "error": str(exc),
                }

    try:
        # Run async cleanup in event loop
        result: dict[str, Any] = asyncio.run(_run_cleanup())

        if not result["success"]:
            # Retry if cleanup failed
            raise self.retry(exc=Exception(result["error"]))

        return result

    except Exception as exc:
        logger.exception("Retention cleanup task failed")
        # Return failure - Celery will retry automatically based on max_retries setting
        return {
            "success": False,
            "unpublished_submissions": 0,
            "rejected_claims": 0,
            "correction_requests": 0,
            "total_deleted": 0,
            "error": f"Task failed: {exc}",
        }
