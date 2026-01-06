"""
Data Retention Service

Issue #91: Data Retention Policies & Auto-Cleanup
Implements automated data retention policies per GDPR requirements
"""

from datetime import datetime, timedelta, timezone
from typing import cast

from sqlalchemy import delete
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.correction import Correction, CorrectionStatus
from app.models.submission import Submission
from app.models.workflow_transition import WorkflowState


class RetentionService:
    """Service for managing data retention and automated cleanup"""

    def __init__(self) -> None:
        """Initialize retention service with periods from configuration"""
        self.unpublished_submissions_days: int = settings.RETENTION_UNPUBLISHED_SUBMISSIONS_DAYS
        self.audit_logs_days: int = settings.RETENTION_AUDIT_LOGS_DAYS
        self.draft_evidence_days: int = settings.RETENTION_DRAFT_EVIDENCE_DAYS
        self.rejected_claims_days: int = settings.RETENTION_REJECTED_CLAIMS_DAYS
        self.correction_requests_days: int = settings.RETENTION_CORRECTION_REQUESTS_DAYS

    async def cleanup_unpublished_submissions(self, db: AsyncSession) -> int:
        """
        Delete unpublished submissions older than retention period

        Args:
            db: Database session

        Returns:
            Number of submissions deleted
        """
        cutoff_date: datetime = datetime.now(timezone.utc) - timedelta(
            days=self.unpublished_submissions_days
        )

        # Delete old unpublished submissions (not PUBLISHED, ARCHIVED, or REJECTED)
        stmt = delete(Submission).where(
            Submission.created_at < cutoff_date,
            Submission.workflow_state.in_(
                [
                    WorkflowState.SUBMITTED,
                    WorkflowState.QUEUED,
                    WorkflowState.ASSIGNED,
                    WorkflowState.IN_RESEARCH,
                    WorkflowState.DRAFT_READY,
                    WorkflowState.NEEDS_MORE_RESEARCH,
                    WorkflowState.ADMIN_REVIEW,
                    WorkflowState.PEER_REVIEW,
                    WorkflowState.FINAL_APPROVAL,
                ]
            ),
        )

        result = cast(CursorResult[tuple[int]], await db.execute(stmt))
        await db.commit()

        return result.rowcount or 0

    async def cleanup_rejected_claims(self, db: AsyncSession) -> int:
        """
        Delete rejected claims older than retention period

        Args:
            db: Database session

        Returns:
            Number of rejected claims deleted
        """
        cutoff_date: datetime = datetime.now(timezone.utc) - timedelta(
            days=self.rejected_claims_days
        )

        # Delete old rejected submissions
        stmt = delete(Submission).where(
            Submission.created_at < cutoff_date,
            Submission.workflow_state == WorkflowState.REJECTED,
        )

        result = cast(CursorResult[tuple[int]], await db.execute(stmt))
        await db.commit()

        return result.rowcount or 0

    async def cleanup_correction_requests(self, db: AsyncSession) -> int:
        """
        Delete resolved correction requests older than retention period

        Args:
            db: Database session

        Returns:
            Number of correction requests deleted
        """
        cutoff_date: datetime = datetime.now(timezone.utc) - timedelta(
            days=self.correction_requests_days
        )

        # Delete old resolved correction requests (keep pending ones)
        # CorrectionStatus enum has: PENDING, ACCEPTED, REJECTED
        stmt = delete(Correction).where(
            Correction.created_at < cutoff_date,
            Correction.status.in_(
                [
                    CorrectionStatus.ACCEPTED,
                    CorrectionStatus.REJECTED,
                ]
            ),
        )

        result = cast(CursorResult[tuple[int]], await db.execute(stmt))
        await db.commit()

        return result.rowcount or 0

    async def run_all(self, db: AsyncSession) -> dict[str, int]:
        """
        Run all cleanup tasks and return summary

        Args:
            db: Database session

        Returns:
            Dictionary with counts of deleted records per category
        """
        summary: dict[str, int] = {}

        summary["unpublished_submissions"] = await self.cleanup_unpublished_submissions(db)
        summary["rejected_claims"] = await self.cleanup_rejected_claims(db)
        summary["correction_requests"] = await self.cleanup_correction_requests(db)

        return summary
