"""
Tests for WorkflowTransition model and Submission workflow fields - TDD approach: Tests FIRST

This test module covers:
- WorkflowTransition table creation and fields
- Submission workflow_state, requires_peer_review, peer_review_reason columns
- Foreign key relationships and cascade behavior
- JSONB metadata storage
- Index optimization for submission_id queries
"""

from datetime import datetime
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class TestWorkflowStateEnum:
    """Tests for WorkflowState enumeration (15 states per ADR 0005)"""

    def test_workflow_state_values(self) -> None:
        """Test that WorkflowState enum has all 15 expected values from ADR 0005"""
        from app.models.workflow_transition import WorkflowState

        # Verify all 15 expected states exist (per ADR 0005)
        expected_states = [
            "submitted",
            "queued",
            "duplicate_detected",
            "archived",
            "assigned",
            "in_research",
            "draft_ready",
            "needs_more_research",
            "admin_review",
            "peer_review",
            "final_approval",
            "published",
            "under_correction",
            "corrected",
            "rejected",
        ]

        actual_values = [state.value for state in WorkflowState]
        assert len(actual_values) == 15, f"Expected 15 states, got {len(actual_values)}"
        for expected in expected_states:
            assert expected in actual_values, f"Missing state: {expected}"

    def test_workflow_state_is_string_enum(self) -> None:
        """Test that WorkflowState inherits from str for JSON serialization"""
        from app.models.workflow_transition import WorkflowState

        # Should be usable as string via .value
        assert WorkflowState.SUBMITTED.value == "submitted"


class TestWorkflowTransitionModel:
    """Tests for WorkflowTransition model"""

    @pytest.mark.asyncio
    async def test_create_workflow_transition(self, db_session: AsyncSession) -> None:
        """Test creating a workflow transition with all required fields"""
        from app.models.submission import Submission
        from app.models.workflow_transition import WorkflowState, WorkflowTransition

        # Create a user first
        user = User(
            email="actor@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create a submission
        submission = Submission(
            user_id=user.id,
            content="Test claim to fact-check",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Create workflow transition
        transition = WorkflowTransition(
            submission_id=submission.id,
            from_state=WorkflowState.SUBMITTED,
            to_state=WorkflowState.QUEUED,
            actor_id=user.id,
            reason="Adding to review queue",
        )
        db_session.add(transition)
        await db_session.commit()
        await db_session.refresh(transition)

        assert transition.id is not None
        assert isinstance(transition.id, UUID)
        assert transition.submission_id == submission.id
        assert transition.from_state == WorkflowState.SUBMITTED
        assert transition.to_state == WorkflowState.QUEUED
        assert transition.actor_id == user.id
        assert transition.reason == "Adding to review queue"
        assert isinstance(transition.created_at, datetime)

    @pytest.mark.asyncio
    async def test_workflow_transition_initial_state_null_from(
        self, db_session: AsyncSession
    ) -> None:
        """Test that initial transition can have null from_state"""
        from app.models.submission import Submission
        from app.models.workflow_transition import WorkflowState, WorkflowTransition

        user = User(email="user@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Test content",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Initial transition - from_state is null
        transition = WorkflowTransition(
            submission_id=submission.id,
            from_state=None,  # Initial state
            to_state=WorkflowState.SUBMITTED,
            actor_id=user.id,
            reason="Submission created",
        )
        db_session.add(transition)
        await db_session.commit()
        await db_session.refresh(transition)

        assert transition.from_state is None
        assert transition.to_state == WorkflowState.SUBMITTED

    @pytest.mark.asyncio
    async def test_workflow_transition_with_metadata(self, db_session: AsyncSession) -> None:
        """Test storing JSONB metadata in workflow transition"""
        from app.models.submission import Submission
        from app.models.workflow_transition import WorkflowState, WorkflowTransition

        user = User(email="user@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Test content",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        transition_metadata: dict[str, Any] = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "additional_notes": "Escalated due to complex claim",
            "related_claims": ["claim-1", "claim-2"],
        }

        transition = WorkflowTransition(
            submission_id=submission.id,
            from_state=WorkflowState.ADMIN_REVIEW,
            to_state=WorkflowState.PEER_REVIEW,
            actor_id=user.id,
            reason="Needs peer review",
            transition_metadata=transition_metadata,
        )
        db_session.add(transition)
        await db_session.commit()
        await db_session.refresh(transition)

        assert transition.transition_metadata is not None
        assert transition.transition_metadata["ip_address"] == "192.168.1.1"
        assert transition.transition_metadata["related_claims"] == ["claim-1", "claim-2"]

    @pytest.mark.asyncio
    async def test_workflow_transition_submission_relationship(
        self, db_session: AsyncSession
    ) -> None:
        """Test relationship between transition and submission"""
        from app.models.submission import Submission
        from app.models.workflow_transition import WorkflowState, WorkflowTransition

        user = User(email="user@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Test content",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        transition = WorkflowTransition(
            submission_id=submission.id,
            from_state=WorkflowState.SUBMITTED,
            to_state=WorkflowState.QUEUED,
            actor_id=user.id,
        )
        db_session.add(transition)
        await db_session.commit()

        # Query and verify relationship
        result = await db_session.execute(
            select(WorkflowTransition).where(WorkflowTransition.submission_id == submission.id)
        )
        loaded_transition = result.scalar_one()
        assert loaded_transition.submission_id == submission.id

    @pytest.mark.asyncio
    async def test_workflow_transition_actor_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between transition and actor (user)"""
        from app.models.submission import Submission
        from app.models.workflow_transition import WorkflowState, WorkflowTransition

        submitter = User(
            email="submitter@example.com", password_hash="hash", role=UserRole.SUBMITTER
        )
        reviewer = User(email="reviewer@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add_all([submitter, reviewer])
        await db_session.commit()
        await db_session.refresh(submitter)
        await db_session.refresh(reviewer)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Transition by reviewer (different from submitter)
        transition = WorkflowTransition(
            submission_id=submission.id,
            from_state=WorkflowState.ASSIGNED,
            to_state=WorkflowState.IN_RESEARCH,
            actor_id=reviewer.id,
            reason="Reviewer picked up the submission",
        )
        db_session.add(transition)
        await db_session.commit()

        result = await db_session.execute(
            select(WorkflowTransition).where(WorkflowTransition.actor_id == reviewer.id)
        )
        loaded_transition = result.scalar_one()
        assert loaded_transition.actor_id == reviewer.id

    @pytest.mark.asyncio
    async def test_multiple_transitions_for_submission(self, db_session: AsyncSession) -> None:
        """Test that a submission can have multiple workflow transitions (audit trail)"""
        from app.models.submission import Submission
        from app.models.workflow_transition import WorkflowState, WorkflowTransition

        user = User(email="user@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Test content",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Create multiple transitions (audit trail) using new 15-state workflow
        transitions_data = [
            (None, WorkflowState.SUBMITTED, "Created"),
            (WorkflowState.SUBMITTED, WorkflowState.QUEUED, "Added to queue"),
            (WorkflowState.QUEUED, WorkflowState.ASSIGNED, "Assigned to reviewer"),
            (WorkflowState.ASSIGNED, WorkflowState.IN_RESEARCH, "Research started"),
            (WorkflowState.IN_RESEARCH, WorkflowState.DRAFT_READY, "Draft completed"),
            (WorkflowState.DRAFT_READY, WorkflowState.ADMIN_REVIEW, "Submitted for review"),
            (WorkflowState.ADMIN_REVIEW, WorkflowState.FINAL_APPROVAL, "Admin approved"),
            (WorkflowState.FINAL_APPROVAL, WorkflowState.PUBLISHED, "Published"),
        ]

        for from_state, to_state, reason in transitions_data:
            transition = WorkflowTransition(
                submission_id=submission.id,
                from_state=from_state,
                to_state=to_state,
                actor_id=user.id,
                reason=reason,
            )
            db_session.add(transition)

        await db_session.commit()

        # Query all transitions for this submission
        result = await db_session.execute(
            select(WorkflowTransition)
            .where(WorkflowTransition.submission_id == submission.id)
            .order_by(WorkflowTransition.created_at)
        )
        all_transitions = result.scalars().all()

        assert len(all_transitions) == 8
        assert all_transitions[0].to_state == WorkflowState.SUBMITTED
        assert all_transitions[-1].to_state == WorkflowState.PUBLISHED


class TestSubmissionWorkflowFields:
    """Tests for new workflow-related fields on Submission model"""

    @pytest.mark.asyncio
    async def test_submission_workflow_state_field(self, db_session: AsyncSession) -> None:
        """Test submission has workflow_state field"""
        from app.models.submission import Submission
        from app.models.workflow_transition import WorkflowState

        user = User(email="user@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Test content",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        assert submission.workflow_state == WorkflowState.SUBMITTED

    @pytest.mark.asyncio
    async def test_submission_workflow_state_default(self, db_session: AsyncSession) -> None:
        """Test submission workflow_state defaults to SUBMITTED"""
        from app.models.submission import Submission
        from app.models.workflow_transition import WorkflowState

        user = User(email="user@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Test content",
            submission_type="text",
            status="pending",
            # Not setting workflow_state - should default
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        assert submission.workflow_state == WorkflowState.SUBMITTED

    @pytest.mark.asyncio
    async def test_submission_requires_peer_review_field(self, db_session: AsyncSession) -> None:
        """Test submission has requires_peer_review boolean field"""
        from app.models.submission import Submission

        user = User(email="user@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Complex claim requiring peer review",
            submission_type="text",
            status="pending",
            requires_peer_review=True,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        assert submission.requires_peer_review is True

    @pytest.mark.asyncio
    async def test_submission_requires_peer_review_default(self, db_session: AsyncSession) -> None:
        """Test submission requires_peer_review defaults to False"""
        from app.models.submission import Submission

        user = User(email="user@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Test content",
            submission_type="text",
            status="pending",
            # Not setting requires_peer_review - should default to False
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        assert submission.requires_peer_review is False

    @pytest.mark.asyncio
    async def test_submission_peer_review_reason_field(self, db_session: AsyncSession) -> None:
        """Test submission has peer_review_reason text field"""
        from app.models.submission import Submission

        user = User(email="user@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Complex claim",
            submission_type="text",
            status="pending",
            requires_peer_review=True,
            peer_review_reason="Claim involves complex scientific data requiring expert verification",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        assert submission.peer_review_reason is not None
        assert "complex scientific data" in submission.peer_review_reason

    @pytest.mark.asyncio
    async def test_submission_peer_review_reason_nullable(self, db_session: AsyncSession) -> None:
        """Test submission peer_review_reason can be null"""
        from app.models.submission import Submission

        user = User(email="user@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Simple claim",
            submission_type="text",
            status="pending",
            requires_peer_review=False,
            # peer_review_reason not set
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        assert submission.peer_review_reason is None

    @pytest.mark.asyncio
    async def test_submission_workflow_transitions_relationship(
        self, db_session: AsyncSession
    ) -> None:
        """Test submission has relationship to workflow_transitions"""
        from app.models.submission import Submission
        from app.models.workflow_transition import WorkflowState, WorkflowTransition

        user = User(email="user@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Test content",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Add transitions
        transition1 = WorkflowTransition(
            submission_id=submission.id,
            from_state=None,
            to_state=WorkflowState.SUBMITTED,
            actor_id=user.id,
        )
        transition2 = WorkflowTransition(
            submission_id=submission.id,
            from_state=WorkflowState.SUBMITTED,
            to_state=WorkflowState.QUEUED,
            actor_id=user.id,
        )
        db_session.add_all([transition1, transition2])
        await db_session.commit()

        # Reload submission and check relationship
        result = await db_session.execute(select(Submission).where(Submission.id == submission.id))
        loaded_submission = result.scalar_one()

        # Access the relationship
        assert hasattr(loaded_submission, "workflow_transitions")
