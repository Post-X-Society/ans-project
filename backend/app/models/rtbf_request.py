"""
Right to be Forgotten (RTBF) Request model for GDPR compliance

Issue #92: Backend: Right to be Forgotten Workflow (TDD)
Part of EPIC #53: GDPR & Data Retention Compliance

Per ADR 0005: EFCSN Compliance Architecture, this implements:
- Right to be forgotten request tracking
- Personal data deletion workflow
- Minor protection (automatic anonymization for users <18)
"""

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.user import User


# Cross-database compatible JSON type (SQLite for tests, PostgreSQL for production)
JSONType = JSON().with_variant(JSONB, "postgresql")


class RTBFRequestStatus(str, enum.Enum):
    """
    Status of Right to be Forgotten request.

    - PENDING: Request received, awaiting processing
    - PROCESSING: Request is being processed (data deletion in progress)
    - COMPLETED: Request fully processed, data deleted/anonymized
    - REJECTED: Request rejected with reason (e.g., legal hold)
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"


class RTBFRequest(TimeStampedModel):
    """
    Right to be Forgotten Request model for GDPR Article 17 compliance.

    Tracks user requests for personal data deletion and the processing
    workflow. Supports automatic approval for minors (age < 18).

    Attributes:
        user_id: The user requesting data deletion
        reason: User-provided reason for the request
        status: Current status of the request
        requester_date_of_birth: For minor detection (auto-approval)
        processed_by_id: Admin who processed the request
        completed_at: When processing was completed
        rejection_reason: Why the request was rejected (if applicable)
        deletion_summary: JSON summary of what was deleted/anonymized
    """

    __tablename__ = "rtbf_requests"

    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Reason for the deletion request
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Request status
    status: Mapped[RTBFRequestStatus] = mapped_column(
        Enum(RTBFRequestStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=RTBFRequestStatus.PENDING,
        index=True,
    )

    # Date of birth for minor detection (optional)
    requester_date_of_birth: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Processing information
    processed_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Rejection information
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Summary of what was deleted/anonymized (for audit trail)
    deletion_summary: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONType,
        nullable=True,
    )

    # Email for notification (stored separately in case user is deleted)
    notification_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    processed_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[processed_by_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<RTBFRequest(id={self.id}, "
            f"user_id={self.user_id}, "
            f"status={self.status.value})>"
        )
