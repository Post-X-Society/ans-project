"""
CorrectionService for managing correction request workflows.

Issue #76: Backend: Correction Request Service (TDD)
EPIC #50: Corrections & Complaints System
ADR 0005: EFCSN Compliance Architecture

This service implements:
- Public correction request submission (no auth required)
- SLA deadline calculation (7-day deadline per EFCSN)
- Acknowledgment email sending
- Correction routing/triage logic
- Prioritization based on correction type and age

EFCSN Correction Categories:
- MINOR: Typos, grammar, formatting (no public notice)
- UPDATE: New information, additional sources (appended note)
- SUBSTANTIAL: Rating change, major error (prominent notice)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.correction import Correction, CorrectionStatus, CorrectionType
from app.models.fact_check import FactCheck
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTS
# ==============================================================================

# SLA deadline in days (EFCSN requires timely response)
SLA_DEADLINE_DAYS: int = 7

# Priority ordering for correction types (higher = more urgent)
CORRECTION_TYPE_PRIORITY: dict[CorrectionType, int] = {
    CorrectionType.SUBSTANTIAL: 3,  # Highest priority
    CorrectionType.UPDATE: 2,
    CorrectionType.MINOR: 1,  # Lowest priority
}


# ==============================================================================
# CUSTOM EXCEPTIONS
# ==============================================================================


class CorrectionServiceError(Exception):
    """Base exception for Correction Service errors."""

    pass


class FactCheckNotFoundError(CorrectionServiceError):
    """Raised when a fact-check is not found."""

    pass


class CorrectionNotFoundError(CorrectionServiceError):
    """Raised when a correction is not found."""

    pass


# ==============================================================================
# EMAIL HELPER FUNCTIONS
# ==============================================================================


def send_correction_acknowledgment_email(
    to_email: str,
    correction_id: UUID,
    correction_type: CorrectionType,
    sla_deadline: datetime,
) -> bool:
    """
    Send acknowledgment email for a correction request.

    Args:
        to_email: Recipient email address
        correction_id: UUID of the correction request
        correction_type: Type of correction (minor/update/substantial)
        sla_deadline: Expected processing deadline

    Returns:
        True if email was sent successfully, False otherwise
    """
    email_service = EmailService()

    if not email_service.is_configured:
        logger.warning("SMTP not configured, skipping acknowledgment email")
        return False

    subject = "[AnsCheckt] Correction Request Received"

    deadline_str: str = sla_deadline.strftime("%B %d, %Y")
    type_display: str = correction_type.value.replace("_", " ").title()

    body_html: str = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Correction Request Received</h2>

        <p>Thank you for submitting a correction request to AnsCheckt.</p>

        <table style="margin: 20px 0; border-collapse: collapse;">
            <tr>
                <td style="padding: 8px; font-weight: bold;">Reference ID:</td>
                <td style="padding: 8px;"><code>{correction_id}</code></td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">Type:</td>
                <td style="padding: 8px;">{type_display}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">Expected Response By:</td>
                <td style="padding: 8px;">{deadline_str}</td>
            </tr>
        </table>

        <p><strong>What happens next?</strong></p>
        <ul>
            <li>Our editorial team will review your correction request</li>
            <li>You will receive an update when a decision is made</li>
            <li>If approved, the correction will be applied and publicly noted</li>
        </ul>

        <p>If you have questions about your request, please include your
        Reference ID in any correspondence.</p>

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
# CORRECTION SERVICE CLASS
# ==============================================================================


class CorrectionService:
    """
    Service for managing correction request workflows.

    This service handles:
    - Public correction request submission
    - SLA deadline calculation and tracking
    - Email notifications
    - Correction triage and prioritization
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the correction service.

        Args:
            db: Async database session
        """
        self.db = db

    # ==========================================================================
    # SLA DEADLINE CALCULATION
    # ==========================================================================

    def calculate_sla_deadline(self) -> datetime:
        """
        Calculate the SLA deadline for a new correction request.

        Per EFCSN requirements, correction requests should be processed
        within 7 days.

        Returns:
            Datetime representing the SLA deadline (7 days from now)
        """
        return datetime.now(timezone.utc) + timedelta(days=SLA_DEADLINE_DAYS)

    # ==========================================================================
    # CORRECTION SUBMISSION
    # ==========================================================================

    async def submit_request(
        self,
        fact_check_id: UUID,
        correction_type: CorrectionType,
        request_details: str,
        requester_email: Optional[str] = None,
    ) -> Correction:
        """
        Submit a new correction request.

        This is a public endpoint - no authentication required.
        Creates a correction record with PENDING status and calculates
        the SLA deadline.

        Args:
            fact_check_id: UUID of the fact-check to correct
            correction_type: Type of correction (minor/update/substantial)
            request_details: Detailed description of the correction
            requester_email: Optional email for acknowledgment

        Returns:
            The created Correction record

        Raises:
            FactCheckNotFoundError: If fact_check_id doesn't exist
        """
        # Verify fact-check exists
        fact_check: Optional[FactCheck] = await self._get_fact_check(fact_check_id)
        if fact_check is None:
            raise FactCheckNotFoundError(f"Fact-check {fact_check_id} not found")

        # Calculate SLA deadline
        sla_deadline: datetime = self.calculate_sla_deadline()

        # Create correction record
        correction = Correction(
            fact_check_id=fact_check_id,
            correction_type=correction_type,
            request_details=request_details,
            requester_email=requester_email,
            status=CorrectionStatus.PENDING,
            sla_deadline=sla_deadline,
        )

        self.db.add(correction)
        await self.db.commit()
        await self.db.refresh(correction)

        # Send acknowledgment email if email provided
        if requester_email:
            try:
                send_correction_acknowledgment_email(
                    to_email=requester_email,
                    correction_id=correction.id,
                    correction_type=correction_type,
                    sla_deadline=sla_deadline,
                )
            except Exception as e:
                # Log error but don't fail the request
                logger.error(f"Failed to send acknowledgment email: {e}")

        return correction

    # ==========================================================================
    # CORRECTION RETRIEVAL
    # ==========================================================================

    async def get_correction_by_id(self, correction_id: UUID) -> Optional[Correction]:
        """
        Get a correction by its ID.

        Args:
            correction_id: UUID of the correction

        Returns:
            Correction if found, None otherwise
        """
        stmt = select(Correction).where(Correction.id == correction_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_corrections_for_fact_check(
        self,
        fact_check_id: UUID,
        correction_type: Optional[CorrectionType] = None,
    ) -> list[Correction]:
        """
        Get all corrections for a specific fact-check.

        Args:
            fact_check_id: UUID of the fact-check
            correction_type: Optional filter by correction type

        Returns:
            List of Correction records
        """
        stmt = select(Correction).where(Correction.fact_check_id == fact_check_id)

        if correction_type is not None:
            stmt = stmt.where(Correction.correction_type == correction_type)

        stmt = stmt.order_by(Correction.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ==========================================================================
    # TRIAGE AND ROUTING
    # ==========================================================================

    async def get_pending_corrections(self) -> list[Correction]:
        """
        Get all pending corrections for triage.

        Returns:
            List of pending Correction records
        """
        stmt = (
            select(Correction)
            .where(Correction.status == CorrectionStatus.PENDING)
            .order_by(Correction.created_at.asc())
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_corrections_by_type(
        self,
        correction_type: CorrectionType,
    ) -> list[Correction]:
        """
        Get corrections filtered by type.

        Args:
            correction_type: Type of correction to filter by

        Returns:
            List of Correction records matching the type
        """
        stmt = (
            select(Correction)
            .where(Correction.correction_type == correction_type)
            .order_by(Correction.created_at.asc())
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_overdue_corrections(self) -> list[Correction]:
        """
        Get corrections that have passed their SLA deadline.

        Returns:
            List of overdue Correction records
        """
        now: datetime = datetime.now(timezone.utc)

        stmt = (
            select(Correction)
            .where(Correction.status == CorrectionStatus.PENDING)
            .where(Correction.sla_deadline.isnot(None))
            .where(Correction.sla_deadline < now)
            .order_by(Correction.sla_deadline.asc())
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_prioritized_pending_corrections(self) -> list[Correction]:
        """
        Get pending corrections prioritized by type and age.

        Substantial corrections come first, then Update, then Minor.
        Within each type, older corrections come first.

        Returns:
            List of prioritized Correction records
        """
        pending: list[Correction] = await self.get_pending_corrections()

        # Sort by type priority (descending) then by created_at (ascending)
        sorted_corrections: list[Correction] = sorted(
            pending,
            key=lambda c: (
                -CORRECTION_TYPE_PRIORITY.get(c.correction_type, 0),
                c.created_at,
            ),
        )

        return sorted_corrections

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    async def _get_fact_check(self, fact_check_id: UUID) -> Optional[FactCheck]:
        """Get a fact-check by ID."""
        stmt = select(FactCheck).where(FactCheck.id == fact_check_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
