"""
Submission reviewer model for assigning reviewers to submissions
"""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.submission import Submission
    from app.models.user import User


class SubmissionReviewer(TimeStampedModel):
    """Association model for assigning reviewers to submissions with assignment tracking"""

    __tablename__ = "submission_reviewers"

    submission_id: Mapped[UUID] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    submission: Mapped["Submission"] = relationship(
        "Submission", foreign_keys=[submission_id], lazy="selectin"
    )
    reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewer_id], lazy="selectin")
    assigned_by: Mapped["User"] = relationship(
        "User", foreign_keys=[assigned_by_id], lazy="selectin"
    )

    # Unique constraint to prevent duplicate assignments
    __table_args__ = (
        UniqueConstraint("submission_id", "reviewer_id", name="uq_submission_reviewer"),
    )

    def __repr__(self) -> str:
        return f"<SubmissionReviewer(submission_id={self.submission_id}, reviewer_id={self.reviewer_id})>"
