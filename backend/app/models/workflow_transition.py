"""
WorkflowTransition model for immutable audit logging of state transitions.

This model tracks all state changes within submission workflows for EFCSN compliance.
Each transition records the from/to states, the actor who made the change,
timestamp, optional reason, and flexible JSONB metadata for extensibility.
"""

import enum
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.submission import Submission
    from app.models.user import User


class WorkflowState(str, enum.Enum):
    """
    Workflow state enumeration for EFCSN compliance (ADR 0005).

    States represent the lifecycle of a submission through the fact-checking process:
    - SUBMITTED: Initial state when user submits content
    - QUEUED: Awaiting assignment to reviewer
    - DUPLICATE_DETECTED: Identified as duplicate of existing submission
    - ARCHIVED: Permanently archived (from duplicate or rejection)
    - ASSIGNED: Reviewer has been assigned
    - IN_RESEARCH: Reviewer actively collecting evidence
    - DRAFT_READY: Reviewer submitted draft fact-check
    - NEEDS_MORE_RESEARCH: Admin requests additional research
    - ADMIN_REVIEW: Admin evaluating draft
    - PEER_REVIEW: Under peer review (2+ editors for substantial claims)
    - FINAL_APPROVAL: Super Admin final check
    - PUBLISHED: Public-facing fact-check
    - UNDER_CORRECTION: Correction in progress
    - CORRECTED: Correction applied, awaiting republish
    - REJECTED: Submission rejected (invalid, out of scope, etc.)
    """

    SUBMITTED = "submitted"
    QUEUED = "queued"
    DUPLICATE_DETECTED = "duplicate_detected"
    ARCHIVED = "archived"
    ASSIGNED = "assigned"
    IN_RESEARCH = "in_research"
    DRAFT_READY = "draft_ready"
    NEEDS_MORE_RESEARCH = "needs_more_research"
    ADMIN_REVIEW = "admin_review"
    PEER_REVIEW = "peer_review"
    FINAL_APPROVAL = "final_approval"
    PUBLISHED = "published"
    UNDER_CORRECTION = "under_correction"
    CORRECTED = "corrected"
    REJECTED = "rejected"


# Cross-database compatible JSONB type (JSONB for PostgreSQL, JSON for SQLite)
JSONType = JSON().with_variant(JSONB, "postgresql")


class WorkflowTransition(TimeStampedModel):
    """
    Immutable audit log for workflow state transitions.

    This table provides a complete audit trail of all state changes for submissions,
    supporting EFCSN compliance requirements for transparency and accountability.

    Attributes:
        submission_id: FK to the submission this transition belongs to
        from_state: Previous workflow state (null for initial transition)
        to_state: New workflow state (required)
        actor_id: FK to the user who triggered the transition
        reason: Optional human-readable reason for the transition
        transition_metadata: JSONB field for additional contextual information
    """

    __tablename__ = "workflow_transitions"

    submission_id: Mapped[UUID] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_state: Mapped[Optional[WorkflowState]] = mapped_column(
        Enum(WorkflowState, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,  # Null for initial transition
    )
    to_state: Mapped[WorkflowState] = mapped_column(
        Enum(WorkflowState, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transition_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONType,
        nullable=True,
        default=None,
    )

    # Relationships
    submission: Mapped["Submission"] = relationship(
        "Submission",
        back_populates="workflow_transitions",
        lazy="selectin",
    )
    actor: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )

    # Indexes for optimized queries
    __table_args__ = (
        Index("idx_workflow_transitions_submission_id", "submission_id"),
        Index("idx_workflow_transitions_actor_id", "actor_id"),
        Index("idx_workflow_transitions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowTransition(id={self.id}, " f"from={self.from_state}, to={self.to_state})>"
