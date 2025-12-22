"""
Correction and CorrectionApplication models for EFCSN-compliant corrections system
Issue #75: Database Schema for Corrections Tables
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.fact_check import FactCheck
    from app.models.user import User


# Cross-database compatible JSON type (SQLite for tests, PostgreSQL for production)
JSONType = JSON().with_variant(JSONB, "postgresql")


class CorrectionType(str, enum.Enum):
    """
    Type of correction per EFCSN standards.
    - MINOR: Typos, grammar, formatting (no public notice)
    - UPDATE: New information, additional sources (appended note)
    - SUBSTANTIAL: Rating change, major error (prominent notice)
    """

    MINOR = "minor"
    UPDATE = "update"
    SUBSTANTIAL = "substantial"


class CorrectionStatus(str, enum.Enum):
    """
    Status of correction request.
    - PENDING: Awaiting review
    - ACCEPTED: Approved and will be/has been applied
    - REJECTED: Declined with explanation
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Correction(TimeStampedModel):
    """
    Correction model for tracking correction requests on fact-checks.
    Supports EFCSN-compliant corrections workflow with SLA tracking.
    """

    __tablename__ = "corrections"

    # Foreign key to fact_check
    fact_check_id: Mapped[UUID] = mapped_column(
        ForeignKey("fact_checks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Correction type (minor/update/substantial)
    correction_type: Mapped[CorrectionType] = mapped_column(
        Enum(CorrectionType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )

    # Requester information (optional for anonymous corrections)
    requester_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Request details (required)
    request_details: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Status of the correction request
    status: Mapped[CorrectionStatus] = mapped_column(
        Enum(CorrectionStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=CorrectionStatus.PENDING,
        index=True,
    )

    # Reviewer information (nullable until reviewed)
    reviewed_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # SLA deadline for processing the correction
    sla_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    fact_check: Mapped["FactCheck"] = relationship(
        "FactCheck",
        back_populates="corrections",
        lazy="selectin",
    )
    reviewed_by: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="corrections_reviewed",
        lazy="selectin",
    )
    applications: Mapped[List["CorrectionApplication"]] = relationship(
        "CorrectionApplication",
        back_populates="correction",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Correction(id={self.id}, "
            f"type={self.correction_type.value}, "
            f"status={self.status.value})>"
        )


class CorrectionApplication(TimeStampedModel):
    """
    CorrectionApplication model for tracking applied corrections with versioning.
    Stores snapshots of previous and new content for audit trail.
    """

    __tablename__ = "correction_applications"

    # Foreign key to correction
    correction_id: Mapped[UUID] = mapped_column(
        ForeignKey("corrections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User who applied the correction
    applied_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )

    # Version number for tracking correction history
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # When the correction was applied
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Summary of changes made
    changes_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Snapshot of content before correction (for audit trail)
    previous_content: Mapped[dict[str, Any]] = mapped_column(
        JSONType,
        nullable=False,
    )

    # Snapshot of content after correction (for audit trail)
    new_content: Mapped[dict[str, Any]] = mapped_column(
        JSONType,
        nullable=False,
    )

    # Flag indicating if this is the current version
    is_current: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    # Relationships
    correction: Mapped["Correction"] = relationship(
        "Correction",
        back_populates="applications",
        lazy="selectin",
    )
    applied_by: Mapped["User"] = relationship(
        "User",
        back_populates="correction_applications",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<CorrectionApplication(id={self.id}, v{self.version})>"
