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
    Workflow state enumeration for EFCSN compliance.

    States represent the lifecycle of a submission through the fact-checking process:
    - SUBMITTED: Initial state when user submits content
    - CLAIM_EXTRACTION: AI is extracting claims from the submission
    - PENDING_REVIEW: Ready for human reviewer assignment
    - UNDER_REVIEW: Actively being reviewed by assigned reviewer
    - PEER_REVIEW_REQUIRED: Flagged for additional peer review
    - PEER_REVIEW: Under peer review by second reviewer
    - COMPLETED: Fact-check complete with final verdict
    - REJECTED: Submission rejected (invalid, duplicate, etc.)
    """

    SUBMITTED = "submitted"
    CLAIM_EXTRACTION = "claim_extraction"
    PENDING_REVIEW = "pending_review"
    UNDER_REVIEW = "under_review"
    PEER_REVIEW_REQUIRED = "peer_review_required"
    PEER_REVIEW = "peer_review"
    COMPLETED = "completed"
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
