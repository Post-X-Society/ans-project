"""
FactCheckRating model for tracking versioned rating history with justifications
Issue #56: Database Schema for Fact Check Rating History
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.fact_check import FactCheck
    from app.models.user import User


class FactCheckRating(TimeStampedModel):
    """
    FactCheckRating model for storing versioned rating history.

    This model tracks the complete history of ratings assigned to fact checks,
    supporting EFCSN compliance requirements for rating justifications and audit trails.

    Attributes:
        fact_check_id: Reference to the fact check being rated
        assigned_by_id: User who assigned the rating
        rating: The rating value (e.g., "true", "false", "partially_true", "unverified")
        justification: Detailed explanation for the rating (minimum 50 characters)
        version: Version number for this rating (starts at 1)
        is_current: Whether this is the current/active rating
        assigned_at: Timestamp when the rating was assigned
    """

    __tablename__ = "fact_check_ratings"

    # Foreign key to fact_checks with cascade delete
    fact_check_id: Mapped[UUID] = mapped_column(
        ForeignKey("fact_checks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign key to users (who assigned the rating)
    assigned_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Rating value
    rating: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Justification for the rating (minimum 50 characters enforced at application level)
    justification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Versioning support
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    # Flag indicating if this is the current rating
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # Timestamp when rating was assigned
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    fact_check: Mapped["FactCheck"] = relationship(
        "FactCheck",
        back_populates="ratings",
        lazy="selectin",
    )

    assigned_by: Mapped["User"] = relationship(
        "User",
        back_populates="fact_check_ratings",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<FactCheckRating(id={self.id}, rating={self.rating}, "
            f"v{self.version}, current={self.is_current})>"
        )
