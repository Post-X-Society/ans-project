"""
Workflow Service for EFCSN-compliant state machine implementation.

This service implements a finite state machine with 15 states per ADR 0005,
including:
- Transition validation
- Role-based permissions
- Transition guards
- Audit logging to workflow_transitions table
- Auto-trigger peer review for political/health claims
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission
from app.models.user import User, UserRole
from app.models.workflow_transition import WorkflowState, WorkflowTransition


class WorkflowError(Exception):
    """Base exception for workflow errors."""

    pass


class InvalidTransitionError(WorkflowError):
    """Raised when an invalid state transition is attempted."""

    pass


class PermissionDeniedError(WorkflowError):
    """Raised when user doesn't have permission for a transition."""

    pass


class SubmissionNotFoundError(WorkflowError):
    """Raised when submission is not found."""

    pass


# Valid state transitions per ADR 0005 workflow diagram
VALID_TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.SUBMITTED: {
        WorkflowState.QUEUED,
        WorkflowState.DUPLICATE_DETECTED,
    },
    WorkflowState.QUEUED: {
        WorkflowState.ASSIGNED,
        WorkflowState.REJECTED,
    },
    WorkflowState.DUPLICATE_DETECTED: {
        WorkflowState.ARCHIVED,
    },
    WorkflowState.ARCHIVED: set(),  # Terminal state
    WorkflowState.ASSIGNED: {
        WorkflowState.IN_RESEARCH,
        WorkflowState.REJECTED,
    },
    WorkflowState.IN_RESEARCH: {
        WorkflowState.DRAFT_READY,
        WorkflowState.REJECTED,
    },
    WorkflowState.DRAFT_READY: {
        WorkflowState.ADMIN_REVIEW,
        WorkflowState.NEEDS_MORE_RESEARCH,
    },
    WorkflowState.NEEDS_MORE_RESEARCH: {
        WorkflowState.IN_RESEARCH,
    },
    WorkflowState.ADMIN_REVIEW: {
        WorkflowState.PEER_REVIEW,
        WorkflowState.FINAL_APPROVAL,
        WorkflowState.NEEDS_MORE_RESEARCH,
        WorkflowState.REJECTED,
    },
    WorkflowState.PEER_REVIEW: {
        WorkflowState.FINAL_APPROVAL,
        WorkflowState.NEEDS_MORE_RESEARCH,
        WorkflowState.REJECTED,
    },
    WorkflowState.FINAL_APPROVAL: {
        WorkflowState.PUBLISHED,
        WorkflowState.NEEDS_MORE_RESEARCH,
        WorkflowState.REJECTED,
    },
    WorkflowState.PUBLISHED: {
        WorkflowState.UNDER_CORRECTION,
    },
    WorkflowState.UNDER_CORRECTION: {
        WorkflowState.CORRECTED,
    },
    WorkflowState.CORRECTED: {
        WorkflowState.PUBLISHED,
    },
    WorkflowState.REJECTED: {
        WorkflowState.ARCHIVED,
    },
}

# Role-based permissions for transitions
# Maps (from_state, to_state) -> minimum required role
TRANSITION_PERMISSIONS: dict[tuple[WorkflowState, WorkflowState], set[UserRole]] = {
    # Submitter has no transition permissions
    # Reviewer transitions
    (WorkflowState.ASSIGNED, WorkflowState.IN_RESEARCH): {
        UserRole.REVIEWER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.IN_RESEARCH, WorkflowState.DRAFT_READY): {
        UserRole.REVIEWER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.NEEDS_MORE_RESEARCH, WorkflowState.IN_RESEARCH): {
        UserRole.REVIEWER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    # Admin transitions
    (WorkflowState.SUBMITTED, WorkflowState.QUEUED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.SUBMITTED, WorkflowState.DUPLICATE_DETECTED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.QUEUED, WorkflowState.ASSIGNED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.QUEUED, WorkflowState.REJECTED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.DUPLICATE_DETECTED, WorkflowState.ARCHIVED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.ASSIGNED, WorkflowState.REJECTED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.IN_RESEARCH, WorkflowState.REJECTED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.DRAFT_READY, WorkflowState.ADMIN_REVIEW): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.DRAFT_READY, WorkflowState.NEEDS_MORE_RESEARCH): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.ADMIN_REVIEW, WorkflowState.PEER_REVIEW): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.ADMIN_REVIEW, WorkflowState.FINAL_APPROVAL): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.ADMIN_REVIEW, WorkflowState.NEEDS_MORE_RESEARCH): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.ADMIN_REVIEW, WorkflowState.REJECTED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.PEER_REVIEW, WorkflowState.FINAL_APPROVAL): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.PEER_REVIEW, WorkflowState.NEEDS_MORE_RESEARCH): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.PEER_REVIEW, WorkflowState.REJECTED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.PUBLISHED, WorkflowState.UNDER_CORRECTION): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.UNDER_CORRECTION, WorkflowState.CORRECTED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.CORRECTED, WorkflowState.PUBLISHED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.REJECTED, WorkflowState.ARCHIVED): {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    },
    # Super Admin only transitions
    (WorkflowState.FINAL_APPROVAL, WorkflowState.PUBLISHED): {
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.FINAL_APPROVAL, WorkflowState.NEEDS_MORE_RESEARCH): {
        UserRole.SUPER_ADMIN,
    },
    (WorkflowState.FINAL_APPROVAL, WorkflowState.REJECTED): {
        UserRole.SUPER_ADMIN,
    },
}

# Keywords that trigger peer review requirement
POLITICAL_KEYWORDS: set[str] = {
    "president",
    "minister",
    "government",
    "election",
    "parliament",
    "political",
    "party",
    "vote",
    "voting",
    "politician",
    "policy",
    "legislation",
    "law",
    "congress",
    "senate",
    "campaign",
}

HEALTH_KEYWORDS: set[str] = {
    "vaccine",
    "vaccination",
    "covid",
    "coronavirus",
    "pandemic",
    "health",
    "medicine",
    "drug",
    "treatment",
    "cure",
    "disease",
    "virus",
    "hospital",
    "doctor",
    "medical",
    "side effect",
    "death",
    "mortality",
}


class WorkflowService:
    """
    Service for managing workflow state transitions.

    Implements EFCSN-compliant state machine with:
    - 15 workflow states
    - Transition validation
    - Role-based permissions
    - Audit logging
    - Auto-trigger peer review for sensitive claims
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the workflow service with a database session."""
        self.db = db

    def get_valid_transitions(self, from_state: WorkflowState) -> set[WorkflowState]:
        """
        Get all valid transitions from a given state.

        Args:
            from_state: The current workflow state

        Returns:
            Set of valid target states
        """
        return VALID_TRANSITIONS.get(from_state, set())

    def is_valid_transition(self, from_state: WorkflowState, to_state: WorkflowState) -> bool:
        """
        Check if a transition is valid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            True if transition is valid, False otherwise
        """
        valid_targets = self.get_valid_transitions(from_state)
        return to_state in valid_targets

    async def _get_user(self, user_id: UUID) -> User:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise PermissionDeniedError(f"User {user_id} not found")
        return user

    async def _get_submission(self, submission_id: UUID) -> Submission:
        """Get submission by ID."""
        result = await self.db.execute(select(Submission).where(Submission.id == submission_id))
        submission = result.scalar_one_or_none()
        if submission is None:
            raise SubmissionNotFoundError(f"Submission {submission_id} not found")
        return submission

    def _check_permission(
        self,
        user_role: UserRole,
        from_state: WorkflowState,
        to_state: WorkflowState,
    ) -> bool:
        """
        Check if a user role has permission for a transition.

        Args:
            user_role: Role of the user attempting the transition
            from_state: Current state
            to_state: Target state

        Returns:
            True if user has permission, False otherwise
        """
        transition_key = (from_state, to_state)
        allowed_roles = TRANSITION_PERMISSIONS.get(transition_key)

        if allowed_roles is None:
            # If not explicitly defined, default to admin+
            return user_role in {UserRole.ADMIN, UserRole.SUPER_ADMIN}

        return user_role in allowed_roles

    async def check_peer_review_required(self, submission: Submission) -> bool:
        """
        Check if a submission requires peer review based on content.

        Peer review is auto-triggered for:
        - Political claims
        - Health/safety claims
        - Claims with high engagement (future implementation)

        Args:
            submission: The submission to check

        Returns:
            True if peer review is required, False otherwise
        """
        content_lower = submission.content.lower()

        # Check for political keywords
        for keyword in POLITICAL_KEYWORDS:
            if keyword in content_lower:
                return True

        # Check for health keywords
        for keyword in HEALTH_KEYWORDS:
            if keyword in content_lower:
                return True

        # Check if already flagged
        if submission.requires_peer_review:
            return True

        return False

    async def transition(
        self,
        submission_id: UUID,
        to_state: WorkflowState,
        actor_id: UUID,
        reason: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Submission:
        """
        Perform a workflow state transition.

        This method:
        1. Validates the transition is allowed
        2. Checks user permissions
        3. Updates submission state
        4. Logs transition to workflow_transitions table

        Args:
            submission_id: ID of the submission to transition
            to_state: Target workflow state
            actor_id: ID of the user performing the transition
            reason: Optional reason for the transition
            metadata: Optional metadata to store with the transition

        Returns:
            Updated submission

        Raises:
            SubmissionNotFoundError: If submission not found
            InvalidTransitionError: If transition is not valid
            PermissionDeniedError: If user doesn't have permission
        """
        # Get submission and user
        submission = await self._get_submission(submission_id)
        user = await self._get_user(actor_id)

        from_state = submission.workflow_state

        # Validate transition
        if not self.is_valid_transition(from_state, to_state):
            raise InvalidTransitionError(
                f"Invalid transition from {from_state.value} to {to_state.value}"
            )

        # Check permissions
        if not self._check_permission(user.role, from_state, to_state):
            raise PermissionDeniedError(
                f"Permission denied: {user.role.value} cannot transition "
                f"from {from_state.value} to {to_state.value}"
            )

        # Update submission state
        submission.workflow_state = to_state

        # Check if peer review should be auto-triggered
        if to_state == WorkflowState.ADMIN_REVIEW:
            if await self.check_peer_review_required(submission):
                submission.requires_peer_review = True
                submission.peer_review_reason = (
                    "Auto-triggered: content contains sensitive keywords"
                )

        # Create transition log entry
        transition = WorkflowTransition(
            submission_id=submission_id,
            from_state=from_state,
            to_state=to_state,
            actor_id=actor_id,
            reason=reason,
            transition_metadata=metadata,
        )
        self.db.add(transition)

        # Commit changes
        await self.db.commit()
        await self.db.refresh(submission)

        return submission

    async def get_transition_history(self, submission_id: UUID) -> list[WorkflowTransition]:
        """
        Get the complete transition history for a submission.

        Args:
            submission_id: ID of the submission

        Returns:
            List of WorkflowTransition records, ordered by created_at
        """
        result = await self.db.execute(
            select(WorkflowTransition)
            .where(WorkflowTransition.submission_id == submission_id)
            .order_by(WorkflowTransition.created_at)
        )
        return list(result.scalars().all())

    async def get_current_state(self, submission_id: UUID) -> WorkflowState:
        """
        Get the current workflow state of a submission.

        Args:
            submission_id: ID of the submission

        Returns:
            Current WorkflowState

        Raises:
            SubmissionNotFoundError: If submission not found
        """
        submission = await self._get_submission(submission_id)
        return submission.workflow_state
