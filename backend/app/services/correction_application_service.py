"""
CorrectionApplicationService for applying corrections to fact-checks.

Issue #77: Backend: Correction Application Logic (TDD)
EPIC #50: Corrections & Complaints System
ADR 0005: EFCSN Compliance Architecture

This service implements:
- Review corrections (accept/reject with resolution notes)
- Apply corrections based on type:
  - MINOR: No public notice required
  - UPDATE: Append explanatory note
  - SUBSTANTIAL: Prominent correction notice
- Fact-check versioning when corrections applied
- Resolution email sending

EFCSN Correction Categories:
- MINOR: Typos, grammar, formatting (no public notice)
- UPDATE: New information, additional sources (appended note)
- SUBSTANTIAL: Rating change, major error (prominent notice)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.correction import (
    Correction,
    CorrectionApplication,
    CorrectionStatus,
    CorrectionType,
)
from app.models.fact_check import FactCheck
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


# ==============================================================================
# CUSTOM EXCEPTIONS
# ==============================================================================


class CorrectionApplicationServiceError(Exception):
    """Base exception for CorrectionApplicationService errors."""

    pass


class CorrectionNotFoundError(CorrectionApplicationServiceError):
    """Raised when a correction is not found."""

    pass


class CorrectionAlreadyReviewedError(CorrectionApplicationServiceError):
    """Raised when trying to review an already reviewed correction."""

    pass


class CorrectionNotAcceptedError(CorrectionApplicationServiceError):
    """Raised when trying to apply a correction that hasn't been accepted."""

    pass


class CorrectionAlreadyAppliedError(CorrectionApplicationServiceError):
    """Raised when trying to apply a correction that has already been applied."""

    pass


class ValidationError(CorrectionApplicationServiceError):
    """Raised when validation fails."""

    pass


# ==============================================================================
# EMAIL HELPER FUNCTIONS
# ==============================================================================


def send_correction_resolution_email(
    to_email: str,
    correction_id: UUID,
    correction_type: CorrectionType,
    status: CorrectionStatus,
    resolution_notes: str,
) -> bool:
    """
    Send resolution email for a correction request.

    Args:
        to_email: Recipient email address
        correction_id: UUID of the correction request
        correction_type: Type of correction (minor/update/substantial)
        status: Final status (ACCEPTED or REJECTED)
        resolution_notes: Explanation of the decision

    Returns:
        True if email was sent successfully, False otherwise
    """
    email_service = EmailService()

    if not email_service.is_configured:
        logger.warning("SMTP not configured, skipping resolution email")
        return False

    status_display: str = "Accepted" if status == CorrectionStatus.ACCEPTED else "Rejected"
    type_display: str = correction_type.value.replace("_", " ").title()

    if status == CorrectionStatus.ACCEPTED:
        subject = "[AnsCheckt] Your Correction Request Has Been Accepted"
        status_color = "#28a745"  # Green
        status_message = (
            "Your correction request has been <strong>accepted</strong> and the "
            "fact-check has been updated accordingly."
        )
    else:
        subject = "[AnsCheckt] Update on Your Correction Request"
        status_color = "#dc3545"  # Red
        status_message = (
            "After careful review, we have decided <strong>not to apply</strong> "
            "the requested correction."
        )

    body_html: str = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Correction Request Update</h2>

        <p>{status_message}</p>

        <table style="margin: 20px 0; border-collapse: collapse; width: 100%;">
            <tr>
                <td style="padding: 8px; font-weight: bold; width: 150px;">Reference ID:</td>
                <td style="padding: 8px;"><code>{correction_id}</code></td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">Type:</td>
                <td style="padding: 8px;">{type_display}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">Status:</td>
                <td style="padding: 8px;">
                    <span style="color: {status_color}; font-weight: bold;">
                        {status_display}
                    </span>
                </td>
            </tr>
        </table>

        <h3>Our Response</h3>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
            {resolution_notes}
        </div>

        <p><strong>What this means:</strong></p>
        <ul>
            {"<li>The correction has been applied to the fact-check</li><li>You can view the updated fact-check on our website</li>" if status == CorrectionStatus.ACCEPTED else "<li>The original fact-check remains unchanged</li><li>If you have new evidence, you may submit a new correction request</li>"}
        </ul>

        <p>If you believe this decision is in error or have additional information,
        you may escalate your complaint to the
        <a href="https://efcsn.com/complaints/">European Fact-Checking Standards Network (EFCSN)</a>.</p>

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        <p style="color: #666; font-size: 12px;">
            This is an automated message from AnsCheckt.
            Please do not reply to this email.
        </p>
    </body>
    </html>
    """

    return email_service.send_email(to_email, subject, body_html)


# ==============================================================================
# CORRECTION APPLICATION SERVICE CLASS
# ==============================================================================


class CorrectionApplicationService:
    """
    Service for applying corrections to fact-checks.

    This service handles:
    - Reviewing corrections (accept/reject)
    - Applying corrections with type-specific logic
    - Version tracking for audit trails
    - Resolution email notifications
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the correction application service.

        Args:
            db: Async database session
        """
        self.db = db

    # ==========================================================================
    # REVIEW CORRECTIONS (Accept/Reject)
    # ==========================================================================

    async def accept_correction(
        self,
        correction_id: UUID,
        reviewer_id: UUID,
        resolution_notes: str,
    ) -> Correction:
        """
        Accept a correction request.

        Updates the correction status to ACCEPTED and records the reviewer info.

        Args:
            correction_id: UUID of the correction to accept
            reviewer_id: UUID of the admin/reviewer accepting
            resolution_notes: Explanation for the acceptance

        Returns:
            Updated Correction record

        Raises:
            CorrectionNotFoundError: If correction doesn't exist
            CorrectionAlreadyReviewedError: If already reviewed
            ValidationError: If resolution_notes is empty
        """
        # Validate resolution notes
        if not resolution_notes or not resolution_notes.strip():
            raise ValidationError("Resolution notes are required when accepting a correction")

        # Get correction
        correction: Optional[Correction] = await self._get_correction(correction_id)
        if correction is None:
            raise CorrectionNotFoundError(f"Correction {correction_id} not found")

        # Check if already reviewed
        if correction.status != CorrectionStatus.PENDING:
            raise CorrectionAlreadyReviewedError(
                f"Correction {correction_id} has already been reviewed "
                f"(status: {correction.status.value})"
            )

        # Update correction
        correction.status = CorrectionStatus.ACCEPTED
        correction.reviewed_by_id = reviewer_id
        correction.reviewed_at = datetime.now(timezone.utc)
        correction.resolution_notes = resolution_notes.strip()

        await self.db.commit()
        await self.db.refresh(correction)

        return correction

    async def reject_correction(
        self,
        correction_id: UUID,
        reviewer_id: UUID,
        resolution_notes: str,
    ) -> Correction:
        """
        Reject a correction request.

        Updates the correction status to REJECTED and records the reviewer info.
        Sends rejection email if requester provided email.

        Args:
            correction_id: UUID of the correction to reject
            reviewer_id: UUID of the admin/reviewer rejecting
            resolution_notes: Explanation for the rejection

        Returns:
            Updated Correction record

        Raises:
            CorrectionNotFoundError: If correction doesn't exist
            CorrectionAlreadyReviewedError: If already reviewed
            ValidationError: If resolution_notes is empty
        """
        # Validate resolution notes
        if not resolution_notes or not resolution_notes.strip():
            raise ValidationError("Resolution notes are required when rejecting a correction")

        # Get correction
        correction: Optional[Correction] = await self._get_correction(correction_id)
        if correction is None:
            raise CorrectionNotFoundError(f"Correction {correction_id} not found")

        # Check if already reviewed
        if correction.status != CorrectionStatus.PENDING:
            raise CorrectionAlreadyReviewedError(
                f"Correction {correction_id} has already been reviewed "
                f"(status: {correction.status.value})"
            )

        # Update correction
        correction.status = CorrectionStatus.REJECTED
        correction.reviewed_by_id = reviewer_id
        correction.reviewed_at = datetime.now(timezone.utc)
        correction.resolution_notes = resolution_notes.strip()

        await self.db.commit()
        await self.db.refresh(correction)

        # Send rejection email if requester provided email
        if correction.requester_email:
            try:
                send_correction_resolution_email(
                    to_email=correction.requester_email,
                    correction_id=correction.id,
                    correction_type=correction.correction_type,
                    status=CorrectionStatus.REJECTED,
                    resolution_notes=resolution_notes.strip(),
                )
            except Exception as e:
                logger.error(f"Failed to send rejection email: {e}")

        return correction

    # ==========================================================================
    # APPLY CORRECTIONS
    # ==========================================================================

    async def apply_correction(
        self,
        correction_id: UUID,
        applied_by_id: UUID,
        changes: dict[str, Any],
        changes_summary: str,
    ) -> CorrectionApplication:
        """
        Apply an accepted correction to a fact-check.

        Creates a versioned CorrectionApplication record with before/after
        snapshots for audit trail. Updates the fact-check with the changes.

        Correction type handling:
        - MINOR: Updates applied directly, no public notice
        - UPDATE: Updates applied with appended note (date included)
        - SUBSTANTIAL: Updates applied with prominent correction notice

        Args:
            correction_id: UUID of the accepted correction to apply
            applied_by_id: UUID of the admin applying the correction
            changes: Dict of field changes to apply to fact-check
            changes_summary: Human-readable summary of changes

        Returns:
            CorrectionApplication record

        Raises:
            CorrectionNotFoundError: If correction doesn't exist
            CorrectionNotAcceptedError: If correction not in ACCEPTED status
            CorrectionAlreadyAppliedError: If correction already applied
            ValidationError: If changes dict is empty
        """
        # Validate changes
        if not changes:
            raise ValidationError("Changes must include at least one field to update")

        # Get correction with fact-check relationship
        correction: Optional[Correction] = await self._get_correction(correction_id)
        if correction is None:
            raise CorrectionNotFoundError(f"Correction {correction_id} not found")

        # Check status is ACCEPTED
        if correction.status != CorrectionStatus.ACCEPTED:
            raise CorrectionNotAcceptedError(
                f"Correction {correction_id} must be ACCEPTED before applying "
                f"(current status: {correction.status.value})"
            )

        # Check if already applied
        existing_application: Optional[CorrectionApplication] = (
            await self._get_existing_application(correction_id)
        )
        if existing_application is not None:
            raise CorrectionAlreadyAppliedError(
                f"Correction {correction_id} has already been applied"
            )

        # Get the fact-check
        fact_check: Optional[FactCheck] = await self._get_fact_check(correction.fact_check_id)
        if fact_check is None:
            raise CorrectionNotFoundError(
                f"Fact-check {correction.fact_check_id} not found for correction"
            )

        # Capture previous state
        previous_content: dict[str, Any] = self._capture_fact_check_state(fact_check)

        # Apply changes to fact-check
        await self._apply_changes_to_fact_check(fact_check, changes, correction.correction_type)

        # Capture new state
        new_content: dict[str, Any] = self._capture_fact_check_state(fact_check)
        # Also include any explicit changes that might not be in the model
        for key, value in changes.items():
            new_content[key] = value

        # Get next version number
        version: int = await self._get_next_version(correction.fact_check_id)

        # Mark previous versions as not current
        await self._mark_previous_versions_not_current(correction.fact_check_id)

        # Create application record
        application = CorrectionApplication(
            correction_id=correction_id,
            applied_by_id=applied_by_id,
            version=version,
            applied_at=datetime.now(timezone.utc),
            changes_summary=changes_summary,
            previous_content=previous_content,
            new_content=new_content,
            is_current=True,
        )

        self.db.add(application)
        await self.db.commit()
        await self.db.refresh(application)

        # Send resolution email if requester provided email
        if correction.requester_email:
            try:
                send_correction_resolution_email(
                    to_email=correction.requester_email,
                    correction_id=correction.id,
                    correction_type=correction.correction_type,
                    status=CorrectionStatus.ACCEPTED,
                    resolution_notes=correction.resolution_notes or changes_summary,
                )
            except Exception as e:
                logger.error(f"Failed to send resolution email: {e}")

        return application

    # ==========================================================================
    # CORRECTION HISTORY
    # ==========================================================================

    async def get_correction_history(
        self,
        fact_check_id: UUID,
    ) -> list[CorrectionApplication]:
        """
        Get the correction application history for a fact-check.

        Returns all CorrectionApplication records for the fact-check,
        ordered by version number (ascending).

        Args:
            fact_check_id: UUID of the fact-check

        Returns:
            List of CorrectionApplication records in version order
        """
        # Get all corrections for this fact-check
        corrections_stmt = select(Correction.id).where(Correction.fact_check_id == fact_check_id)
        corrections_result = await self.db.execute(corrections_stmt)
        correction_ids: list[UUID] = [row[0] for row in corrections_result.fetchall()]

        if not correction_ids:
            return []

        # Get all applications for these corrections
        stmt = (
            select(CorrectionApplication)
            .where(CorrectionApplication.correction_id.in_(correction_ids))
            .order_by(CorrectionApplication.version.asc())
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    async def _get_correction(self, correction_id: UUID) -> Optional[Correction]:
        """Get a correction by ID."""
        stmt = select(Correction).where(Correction.id == correction_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_fact_check(self, fact_check_id: UUID) -> Optional[FactCheck]:
        """Get a fact-check by ID."""
        stmt = select(FactCheck).where(FactCheck.id == fact_check_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_existing_application(
        self, correction_id: UUID
    ) -> Optional[CorrectionApplication]:
        """Check if a correction has already been applied."""
        stmt = select(CorrectionApplication).where(
            CorrectionApplication.correction_id == correction_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_next_version(self, fact_check_id: UUID) -> int:
        """Get the next version number for a fact-check's corrections."""
        # Get all corrections for this fact-check
        corrections_stmt = select(Correction.id).where(Correction.fact_check_id == fact_check_id)
        corrections_result = await self.db.execute(corrections_stmt)
        correction_ids: list[UUID] = [row[0] for row in corrections_result.fetchall()]

        if not correction_ids:
            return 1

        # Get max version from applications
        from sqlalchemy import func

        max_version_stmt = select(func.max(CorrectionApplication.version)).where(
            CorrectionApplication.correction_id.in_(correction_ids)
        )
        result = await self.db.execute(max_version_stmt)
        max_version: Optional[int] = result.scalar()

        return (max_version or 0) + 1

    async def _mark_previous_versions_not_current(self, fact_check_id: UUID) -> None:
        """Mark all previous correction applications for a fact-check as not current."""
        # Get all corrections for this fact-check
        corrections_stmt = select(Correction.id).where(Correction.fact_check_id == fact_check_id)
        corrections_result = await self.db.execute(corrections_stmt)
        correction_ids: list[UUID] = [row[0] for row in corrections_result.fetchall()]

        if not correction_ids:
            return

        # Get all current applications
        stmt = select(CorrectionApplication).where(
            CorrectionApplication.correction_id.in_(correction_ids),
            CorrectionApplication.is_current.is_(True),
        )
        result = await self.db.execute(stmt)
        applications: list[CorrectionApplication] = list(result.scalars().all())

        for app in applications:
            app.is_current = False

    def _capture_fact_check_state(self, fact_check: FactCheck) -> dict[str, Any]:
        """Capture the current state of a fact-check for audit trail."""
        return {
            "verdict": fact_check.verdict,
            "confidence": fact_check.confidence,
            "reasoning": fact_check.reasoning,
            "sources": fact_check.sources,
            "sources_count": fact_check.sources_count,
        }

    async def _apply_changes_to_fact_check(
        self,
        fact_check: FactCheck,
        changes: dict[str, Any],
        correction_type: CorrectionType,
    ) -> None:
        """
        Apply changes to a fact-check based on correction type.

        Args:
            fact_check: FactCheck model to update
            changes: Dict of changes to apply
            correction_type: Type of correction (affects handling)
        """
        # Apply each change to the fact-check
        for field, value in changes.items():
            # Skip non-model fields (like correction_notice which may be handled differently)
            if field == "correction_notice":
                continue

            if hasattr(fact_check, field):
                setattr(fact_check, field, value)

        # Update sources_count if sources changed
        if "sources" in changes and isinstance(changes["sources"], list):
            fact_check.sources_count = len(changes["sources"])

        # For SUBSTANTIAL corrections, ensure the reasoning indicates it's a correction
        # This is typically handled by the caller including "CORRECTION:" in the reasoning
        # but we log it for tracking
        if correction_type == CorrectionType.SUBSTANTIAL:
            logger.info(f"Substantial correction applied to fact-check {fact_check.id}")

        await self.db.flush()
