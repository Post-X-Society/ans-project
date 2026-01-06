"""
User model for authentication and authorization
"""

import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.correction import Correction, CorrectionApplication
    from app.models.fact_check_rating import FactCheckRating
    from app.models.peer_review import PeerReview
    from app.models.rtbf_request import RTBFRequest
    from app.models.submission import Submission
    from app.models.submission_reviewer import SubmissionReviewer
    from app.models.volunteer import Volunteer


class UserRole(str, enum.Enum):
    """User role enumeration for role-based access control"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    REVIEWER = "reviewer"
    SUBMITTER = "submitter"


class User(TimeStampedModel):
    """User model for authentication and role-based access control"""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=UserRole.SUBMITTER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_opt_out: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )  # User preference to opt out of email notifications

    # Relationships
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission", back_populates="user", lazy="selectin"
    )
    volunteer: Mapped[Optional["Volunteer"]] = relationship(
        "Volunteer", back_populates="user", uselist=False, lazy="selectin"
    )
    reviewer_assignments: Mapped[List["SubmissionReviewer"]] = relationship(
        "SubmissionReviewer",
        foreign_keys="SubmissionReviewer.reviewer_id",
        back_populates="reviewer",
        lazy="selectin",
    )
    assigned_reviews: Mapped[List["SubmissionReviewer"]] = relationship(
        "SubmissionReviewer",
        foreign_keys="SubmissionReviewer.assigned_by_id",
        back_populates="assigned_by",
        lazy="selectin",
    )
    fact_check_ratings: Mapped[List["FactCheckRating"]] = relationship(
        "FactCheckRating",
        back_populates="assigned_by",
        lazy="selectin",
    )
    peer_reviews: Mapped[List["PeerReview"]] = relationship(
        "PeerReview",
        back_populates="reviewer",
        lazy="selectin",
    )
    corrections_reviewed: Mapped[List["Correction"]] = relationship(
        "Correction",
        back_populates="reviewed_by",
        lazy="selectin",
    )
    correction_applications: Mapped[List["CorrectionApplication"]] = relationship(
        "CorrectionApplication",
        back_populates="applied_by",
        lazy="selectin",
    )
    rtbf_requests: Mapped[List["RTBFRequest"]] = relationship(
        "RTBFRequest",
        foreign_keys="RTBFRequest.user_id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"
