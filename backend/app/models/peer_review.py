"""
PeerReview model for tracking peer reviews on fact checks
Issue #63: Database Schema for Peer Review Tables
"""

import enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.fact_check import FactCheck
    from app.models.user import User


class ApprovalStatus(str, enum.Enum):
    """Approval status enumeration for peer reviews"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PeerReview(TimeStampedModel):
    """
    PeerReview model for tracking peer reviews on fact checks.

    This model supports the EFCSN compliance requirement for peer review
    of sensitive or high-impact fact checks. Each peer review tracks:
    - Which fact check is being reviewed
    - Who is performing the peer review
    - The approval status (pending, approved, rejected)
    - Optional comments from the reviewer

    Attributes:
        fact_check_id: Reference to the fact check being reviewed
        reviewer_id: User who is performing the peer review
        approval_status: Current status of the peer review
        comments: Optional detailed comments from the reviewer
    """

    __tablename__ = "peer_reviews"

    # Foreign key to fact_checks with cascade delete
    fact_check_id: Mapped[UUID] = mapped_column(
        ForeignKey("fact_checks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign key to users (peer reviewer)
    reviewer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Approval status
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ApprovalStatus.PENDING,
        index=True,
    )

    # Optional comments from the reviewer
    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    fact_check: Mapped["FactCheck"] = relationship(
        "FactCheck",
        back_populates="peer_reviews",
        lazy="selectin",
    )

    reviewer: Mapped["User"] = relationship(
        "User",
        back_populates="peer_reviews",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PeerReview(id={self.id}, status={self.approval_status.value})>"
