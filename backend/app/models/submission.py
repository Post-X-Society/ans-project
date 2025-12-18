"""
Submission model for user-submitted content
"""

from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimeStampedModel, submission_claims

if TYPE_CHECKING:
    from app.models.claim import Claim
    from app.models.spotlight import SpotlightContent
    from app.models.submission_reviewer import SubmissionReviewer
    from app.models.user import User


class Submission(TimeStampedModel):
    """Submission model for content submitted by users for fact-checking"""

    __tablename__ = "submissions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    submission_type: Mapped[str] = mapped_column(String(50), nullable=False)  # text, image, video
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # pending, processing, completed

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="submissions", lazy="selectin")
    claims: Mapped[List["Claim"]] = relationship(
        "Claim",
        secondary=submission_claims,
        back_populates="submissions",
        lazy="selectin",
    )
    spotlight_content: Mapped[Optional["SpotlightContent"]] = relationship(
        "SpotlightContent", back_populates="submission", lazy="selectin", uselist=False
    )
    reviewer_assignments: Mapped[List["SubmissionReviewer"]] = relationship(
        "SubmissionReviewer",
        foreign_keys="SubmissionReviewer.submission_id",
        back_populates="submission",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Submission(id={self.id}, type={self.submission_type}, status={self.status})>"
