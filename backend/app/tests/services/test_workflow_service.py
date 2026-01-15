"""
Tests for WorkflowService - TDD approach: Tests FIRST

This test module covers:
- Extended WorkflowState enum (15 states per ADR 0005)
- Valid state transitions
- Transition guards (e.g., can't publish without rating)
- Role-based transition permissions
- Transition logging to workflow_transitions table
- Auto-trigger peer review for political claims
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission
from app.models.user import User, UserRole
from app.models.workflow_transition import WorkflowState, WorkflowTransition


class TestExtendedWorkflowStateEnum:
    """Tests for the extended WorkflowState enumeration (15 states per ADR 0005)"""

    def test_workflow_state_has_15_states(self) -> None:
        """Test that WorkflowState enum has all 15 required states from ADR 0005"""
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

    def test_workflow_state_enum_values(self) -> None:
        """Test specific enum values exist and have correct string values"""
        assert WorkflowState.SUBMITTED.value == "submitted"
        assert WorkflowState.QUEUED.value == "queued"
        assert WorkflowState.DUPLICATE_DETECTED.value == "duplicate_detected"
        assert WorkflowState.ARCHIVED.value == "archived"
        assert WorkflowState.ASSIGNED.value == "assigned"
        assert WorkflowState.IN_RESEARCH.value == "in_research"
        assert WorkflowState.DRAFT_READY.value == "draft_ready"
        assert WorkflowState.NEEDS_MORE_RESEARCH.value == "needs_more_research"
        assert WorkflowState.ADMIN_REVIEW.value == "admin_review"
        assert WorkflowState.PEER_REVIEW.value == "peer_review"
        assert WorkflowState.FINAL_APPROVAL.value == "final_approval"
        assert WorkflowState.PUBLISHED.value == "published"
        assert WorkflowState.UNDER_CORRECTION.value == "under_correction"
        assert WorkflowState.CORRECTED.value == "corrected"
        assert WorkflowState.REJECTED.value == "rejected"


class TestWorkflowServiceTransitions:
    """Tests for WorkflowService transition validation"""

    @pytest.mark.asyncio
    async def test_valid_transition_submitted_to_queued(self, db_session: AsyncSession) -> None:
        """Test valid transition from SUBMITTED to QUEUED"""
        from app.services.workflow_service import WorkflowService

        # Create user and submission
        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        submission = Submission(
            user_id=admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Perform transition
        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.QUEUED,
            actor_id=admin.id,
            reason="Ready for review queue",
        )

        assert result.workflow_state == WorkflowState.QUEUED

    @pytest.mark.asyncio
    async def test_valid_transition_submitted_to_duplicate_detected(
        self, db_session: AsyncSession
    ) -> None:
        """Test valid transition from SUBMITTED to DUPLICATE_DETECTED"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        submission = Submission(
            user_id=admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.DUPLICATE_DETECTED,
            actor_id=admin.id,
            reason="Duplicate of submission #123",
        )

        assert result.workflow_state == WorkflowState.DUPLICATE_DETECTED

    @pytest.mark.asyncio
    async def test_valid_transition_queued_to_assigned(self, db_session: AsyncSession) -> None:
        """Test valid transition from QUEUED to ASSIGNED"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        submission = Submission(
            user_id=admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.QUEUED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.ASSIGNED,
            actor_id=admin.id,
            reason="Assigned to reviewer",
        )

        assert result.workflow_state == WorkflowState.ASSIGNED

    @pytest.mark.asyncio
    async def test_invalid_transition_raises_error(self, db_session: AsyncSession) -> None:
        """Test that invalid transition raises ValueError"""
        from app.services.workflow_service import InvalidTransitionError, WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        submission = Submission(
            user_id=admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Try invalid transition: SUBMITTED -> PUBLISHED (skipping all intermediate states)
        service = WorkflowService(db_session)
        with pytest.raises(InvalidTransitionError) as exc_info:
            await service.transition(
                submission_id=submission.id,
                to_state=WorkflowState.PUBLISHED,
                actor_id=admin.id,
            )

        assert "Invalid transition" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_full_workflow_happy_path(self, db_session: AsyncSession) -> None:
        """Test complete workflow from SUBMITTED to PUBLISHED"""
        from app.services.workflow_service import WorkflowService

        super_admin = User(
            email="superadmin@example.com", password_hash="hash", role=UserRole.SUPER_ADMIN
        )
        db_session.add(super_admin)
        await db_session.commit()
        await db_session.refresh(super_admin)

        submission = Submission(
            user_id=super_admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)

        # Full workflow path
        transitions = [
            (WorkflowState.QUEUED, "Added to queue"),
            (WorkflowState.ASSIGNED, "Assigned to reviewer"),
            (WorkflowState.IN_RESEARCH, "Research started"),
            (WorkflowState.DRAFT_READY, "Draft completed"),
            (WorkflowState.ADMIN_REVIEW, "Submitted for admin review"),
            (WorkflowState.FINAL_APPROVAL, "Admin approved"),
            (WorkflowState.PUBLISHED, "Published"),
        ]

        for to_state, reason in transitions:
            result = await service.transition(
                submission_id=submission.id,
                to_state=to_state,
                actor_id=super_admin.id,
                reason=reason,
            )
            assert result.workflow_state == to_state


class TestWorkflowServiceRolePermissions:
    """Tests for role-based transition permissions"""

    @pytest.mark.asyncio
    async def test_reviewer_can_transition_to_in_research(self, db_session: AsyncSession) -> None:
        """Test that reviewer can transition from ASSIGNED to IN_RESEARCH"""
        from app.services.workflow_service import WorkflowService

        reviewer = User(email="reviewer@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        submission = Submission(
            user_id=reviewer.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.ASSIGNED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.IN_RESEARCH,
            actor_id=reviewer.id,
            reason="Starting research",
        )

        assert result.workflow_state == WorkflowState.IN_RESEARCH

    @pytest.mark.asyncio
    async def test_reviewer_cannot_publish(self, db_session: AsyncSession) -> None:
        """Test that reviewer cannot transition to PUBLISHED"""
        from app.services.workflow_service import PermissionDeniedError, WorkflowService

        reviewer = User(email="reviewer@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        submission = Submission(
            user_id=reviewer.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.FINAL_APPROVAL,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)
        with pytest.raises(PermissionDeniedError) as exc_info:
            await service.transition(
                submission_id=submission.id,
                to_state=WorkflowState.PUBLISHED,
                actor_id=reviewer.id,
            )

        assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_admin_can_approve_for_peer_review(self, db_session: AsyncSession) -> None:
        """Test that admin can transition to PEER_REVIEW"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        submission = Submission(
            user_id=admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.ADMIN_REVIEW,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.PEER_REVIEW,
            actor_id=admin.id,
            reason="Escalating to peer review",
        )

        assert result.workflow_state == WorkflowState.PEER_REVIEW

    @pytest.mark.asyncio
    async def test_super_admin_can_publish(self, db_session: AsyncSession) -> None:
        """Test that super_admin can transition to PUBLISHED"""
        from app.services.workflow_service import WorkflowService

        super_admin = User(
            email="superadmin@example.com", password_hash="hash", role=UserRole.SUPER_ADMIN
        )
        db_session.add(super_admin)
        await db_session.commit()
        await db_session.refresh(super_admin)

        submission = Submission(
            user_id=super_admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.FINAL_APPROVAL,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.PUBLISHED,
            actor_id=super_admin.id,
            reason="Final approval complete",
        )

        assert result.workflow_state == WorkflowState.PUBLISHED

    @pytest.mark.asyncio
    async def test_submitter_cannot_transition(self, db_session: AsyncSession) -> None:
        """Test that submitter cannot make workflow transitions"""
        from app.services.workflow_service import PermissionDeniedError, WorkflowService

        submitter = User(
            email="submitter@example.com", password_hash="hash", role=UserRole.SUBMITTER
        )
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)
        with pytest.raises(PermissionDeniedError):
            await service.transition(
                submission_id=submission.id,
                to_state=WorkflowState.QUEUED,
                actor_id=submitter.id,
            )


class TestWorkflowServiceTransitionGuards:
    """Tests for transition guards"""

    @pytest.mark.asyncio
    async def test_needs_more_research_returns_to_in_research(
        self, db_session: AsyncSession
    ) -> None:
        """Test transition from NEEDS_MORE_RESEARCH back to IN_RESEARCH"""
        from app.services.workflow_service import WorkflowService

        reviewer = User(email="reviewer@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        submission = Submission(
            user_id=reviewer.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.NEEDS_MORE_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.IN_RESEARCH,
            actor_id=reviewer.id,
            reason="Returning to research",
        )

        assert result.workflow_state == WorkflowState.IN_RESEARCH

    @pytest.mark.asyncio
    async def test_correction_workflow(self, db_session: AsyncSession) -> None:
        """Test correction workflow: PUBLISHED -> UNDER_CORRECTION -> CORRECTED -> PUBLISHED"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        submission = Submission(
            user_id=admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.PUBLISHED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)

        # Start correction
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.UNDER_CORRECTION,
            actor_id=admin.id,
            reason="Error found, needs correction",
        )
        assert result.workflow_state == WorkflowState.UNDER_CORRECTION

        # Complete correction
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.CORRECTED,
            actor_id=admin.id,
            reason="Correction applied",
        )
        assert result.workflow_state == WorkflowState.CORRECTED

        # Re-publish
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.PUBLISHED,
            actor_id=admin.id,
            reason="Republished after correction",
        )
        assert result.workflow_state == WorkflowState.PUBLISHED


class TestWorkflowServiceTransitionLogging:
    """Tests for transition logging to workflow_transitions table"""

    @pytest.mark.asyncio
    async def test_transition_creates_log_entry(self, db_session: AsyncSession) -> None:
        """Test that transition creates a log entry in workflow_transitions table"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        submission = Submission(
            user_id=admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)
        await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.QUEUED,
            actor_id=admin.id,
            reason="Adding to queue",
        )

        # Query workflow_transitions table
        result = await db_session.execute(
            select(WorkflowTransition).where(WorkflowTransition.submission_id == submission.id)
        )
        transitions = result.scalars().all()

        assert len(transitions) == 1
        assert transitions[0].from_state == WorkflowState.SUBMITTED
        assert transitions[0].to_state == WorkflowState.QUEUED
        assert transitions[0].actor_id == admin.id
        assert transitions[0].reason == "Adding to queue"

    @pytest.mark.asyncio
    async def test_multiple_transitions_create_audit_trail(self, db_session: AsyncSession) -> None:
        """Test that multiple transitions create complete audit trail"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        submission = Submission(
            user_id=admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)

        # Make multiple transitions
        transitions_to_make = [
            (WorkflowState.QUEUED, "Adding to queue"),
            (WorkflowState.ASSIGNED, "Assigned to reviewer"),
            (WorkflowState.IN_RESEARCH, "Starting research"),
        ]

        for to_state, reason in transitions_to_make:
            await service.transition(
                submission_id=submission.id,
                to_state=to_state,
                actor_id=admin.id,
                reason=reason,
            )

        # Query all transitions
        result = await db_session.execute(
            select(WorkflowTransition)
            .where(WorkflowTransition.submission_id == submission.id)
            .order_by(WorkflowTransition.created_at)
        )
        transitions = result.scalars().all()

        assert len(transitions) == 3
        assert transitions[0].to_state == WorkflowState.QUEUED
        assert transitions[1].to_state == WorkflowState.ASSIGNED
        assert transitions[2].to_state == WorkflowState.IN_RESEARCH

    @pytest.mark.asyncio
    async def test_transition_with_metadata(self, db_session: AsyncSession) -> None:
        """Test that transition can store metadata"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        submission = Submission(
            user_id=admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)
        metadata = {"ip_address": "192.168.1.1", "user_agent": "TestClient"}

        await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.QUEUED,
            actor_id=admin.id,
            reason="Adding to queue",
            metadata=metadata,
        )

        result = await db_session.execute(
            select(WorkflowTransition).where(WorkflowTransition.submission_id == submission.id)
        )
        transition = result.scalar_one()

        assert transition.transition_metadata is not None
        assert transition.transition_metadata["ip_address"] == "192.168.1.1"


class TestWorkflowServicePeerReviewAutoTrigger:
    """Tests for automatic peer review triggering"""

    @pytest.mark.asyncio
    async def test_political_claim_triggers_peer_review(self, db_session: AsyncSession) -> None:
        """Test that political claims auto-trigger peer review requirement"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Political claim content
        submission = Submission(
            user_id=admin.id,
            content="The president announced new political policy changes",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.ADMIN_REVIEW,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)

        # Check if peer review is required
        requires_peer_review = await service.check_peer_review_required(submission)

        assert requires_peer_review is True

    @pytest.mark.asyncio
    async def test_health_claim_triggers_peer_review(self, db_session: AsyncSession) -> None:
        """Test that health/safety claims auto-trigger peer review requirement"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Health claim content
        submission = Submission(
            user_id=admin.id,
            content="This vaccine causes harmful side effects",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.ADMIN_REVIEW,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)

        requires_peer_review = await service.check_peer_review_required(submission)

        assert requires_peer_review is True

    @pytest.mark.asyncio
    async def test_simple_claim_no_peer_review(self, db_session: AsyncSession) -> None:
        """Test that simple claims don't require peer review"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Simple factual claim
        submission = Submission(
            user_id=admin.id,
            content="The Eiffel Tower is 330 meters tall",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.ADMIN_REVIEW,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)

        requires_peer_review = await service.check_peer_review_required(submission)

        assert requires_peer_review is False


class TestWorkflowServiceGetValidTransitions:
    """Tests for getting valid transitions from a state"""

    @pytest.mark.asyncio
    async def test_get_valid_transitions_from_submitted(self, db_session: AsyncSession) -> None:
        """Test getting valid transitions from SUBMITTED state"""
        from app.services.workflow_service import WorkflowService

        service = WorkflowService(db_session)
        valid_transitions = service.get_valid_transitions(WorkflowState.SUBMITTED)

        assert WorkflowState.QUEUED in valid_transitions
        assert WorkflowState.DUPLICATE_DETECTED in valid_transitions
        assert WorkflowState.PUBLISHED not in valid_transitions

    @pytest.mark.asyncio
    async def test_get_valid_transitions_from_admin_review(self, db_session: AsyncSession) -> None:
        """Test getting valid transitions from ADMIN_REVIEW state"""
        from app.services.workflow_service import WorkflowService

        service = WorkflowService(db_session)
        valid_transitions = service.get_valid_transitions(WorkflowState.ADMIN_REVIEW)

        assert WorkflowState.NEEDS_MORE_RESEARCH in valid_transitions
        assert WorkflowState.PEER_REVIEW in valid_transitions
        assert WorkflowState.FINAL_APPROVAL in valid_transitions
        assert WorkflowState.REJECTED in valid_transitions


class TestWorkflowServiceGetTransitionHistory:
    """Tests for getting transition history"""

    @pytest.mark.asyncio
    async def test_get_transition_history(self, db_session: AsyncSession) -> None:
        """Test getting transition history for a submission"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        submission = Submission(
            user_id=admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)

        # Make some transitions
        await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.QUEUED,
            actor_id=admin.id,
            reason="Adding to queue",
        )
        await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.ASSIGNED,
            actor_id=admin.id,
            reason="Assigned to reviewer",
        )

        history = await service.get_transition_history(submission.id)

        assert len(history) == 2
        assert history[0].to_state == WorkflowState.QUEUED
        assert history[1].to_state == WorkflowState.ASSIGNED

    @pytest.mark.asyncio
    async def test_get_transition_history_empty(self, db_session: AsyncSession) -> None:
        """Test getting empty transition history for new submission"""
        from app.services.workflow_service import WorkflowService

        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        submission = Submission(
            user_id=admin.id,
            content="Test claim",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        service = WorkflowService(db_session)
        history = await service.get_transition_history(submission.id)

        assert len(history) == 0


class TestWorkflowServiceFactCheckAutoCreation:
    """Tests for automatic FactCheck creation on workflow transitions (Issue #178)"""

    @pytest.mark.asyncio
    async def test_fact_check_created_on_transition_to_assigned(
        self, db_session: AsyncSession
    ) -> None:
        """Test that FactCheck is auto-created when transitioning to ASSIGNED state"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.services.workflow_service import WorkflowService

        # Create admin user
        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Create submission in QUEUED state
        submission = Submission(
            user_id=admin.id,
            content="Test claim for fact-checking",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.QUEUED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Create a claim and link to submission
        claim = Claim(content="The earth is round", source="user_submission")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        # Link claim to submission via many-to-many
        submission.claims.append(claim)
        await db_session.commit()
        await db_session.refresh(submission)

        # Perform transition to ASSIGNED
        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.ASSIGNED,
            actor_id=admin.id,
            reason="Assigning to reviewer",
        )

        assert result.workflow_state == WorkflowState.ASSIGNED

        # Verify FactCheck was created for the claim
        fact_check_result = await db_session.execute(
            select(FactCheck).where(FactCheck.claim_id == claim.id)
        )
        fact_check = fact_check_result.scalar_one_or_none()

        assert fact_check is not None
        assert fact_check.verdict == "pending"
        assert fact_check.confidence == 0.0
        assert fact_check.claim_id == claim.id

    @pytest.mark.asyncio
    async def test_fact_check_created_on_transition_to_in_research(
        self, db_session: AsyncSession
    ) -> None:
        """Test that FactCheck is auto-created when transitioning to IN_RESEARCH state"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.services.workflow_service import WorkflowService

        # Create reviewer user
        reviewer = User(email="reviewer@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        # Create submission already in ASSIGNED state (skipping FactCheck creation)
        submission = Submission(
            user_id=reviewer.id,
            content="Test claim for research",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.ASSIGNED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Create a claim and link to submission
        claim = Claim(content="Water boils at 100C at sea level", source="user_submission")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        # Link claim to submission
        submission.claims.append(claim)
        await db_session.commit()
        await db_session.refresh(submission)

        # Perform transition to IN_RESEARCH
        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.IN_RESEARCH,
            actor_id=reviewer.id,
            reason="Starting research",
        )

        assert result.workflow_state == WorkflowState.IN_RESEARCH

        # Verify FactCheck was created
        fact_check_result = await db_session.execute(
            select(FactCheck).where(FactCheck.claim_id == claim.id)
        )
        fact_check = fact_check_result.scalar_one_or_none()

        assert fact_check is not None
        assert fact_check.verdict == "pending"
        assert fact_check.confidence == 0.0

    @pytest.mark.asyncio
    async def test_no_duplicate_fact_check_creation(self, db_session: AsyncSession) -> None:
        """Test that duplicate FactCheck is not created if one already exists"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.services.workflow_service import WorkflowService

        # Create reviewer user
        reviewer = User(email="reviewer@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        # Create submission in ASSIGNED state
        submission = Submission(
            user_id=reviewer.id,
            content="Test claim already checked",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.ASSIGNED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Create a claim and link to submission
        claim = Claim(content="The sky is blue", source="user_submission")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        # Create existing FactCheck for this claim
        existing_fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Verified by multiple sources",
            sources=["https://example.com/source1"],
        )
        db_session.add(existing_fact_check)
        await db_session.commit()
        await db_session.refresh(existing_fact_check)

        # Link claim to submission
        submission.claims.append(claim)
        await db_session.commit()
        await db_session.refresh(submission)

        # Perform transition to IN_RESEARCH
        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.IN_RESEARCH,
            actor_id=reviewer.id,
            reason="Starting research",
        )

        assert result.workflow_state == WorkflowState.IN_RESEARCH

        # Verify only one FactCheck exists (no duplicate created)
        fact_check_result = await db_session.execute(
            select(FactCheck).where(FactCheck.claim_id == claim.id)
        )
        fact_checks = fact_check_result.scalars().all()

        assert len(fact_checks) == 1
        # Original FactCheck should be unchanged
        assert fact_checks[0].verdict == "true"
        assert fact_checks[0].confidence == 0.9

    @pytest.mark.asyncio
    async def test_no_fact_check_created_when_no_claims(self, db_session: AsyncSession) -> None:
        """Test that no FactCheck is created and no error raised when submission has no claims"""
        from app.models.fact_check import FactCheck
        from app.services.workflow_service import WorkflowService

        # Create admin user
        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Create submission with NO claims
        submission = Submission(
            user_id=admin.id,
            content="Submission without claims",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.QUEUED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Perform transition to ASSIGNED (should NOT raise error)
        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.ASSIGNED,
            actor_id=admin.id,
            reason="Assigning reviewer",
        )

        # Transition should succeed
        assert result.workflow_state == WorkflowState.ASSIGNED

        # No FactCheck should be created
        fact_check_result = await db_session.execute(select(FactCheck))
        fact_checks = fact_check_result.scalars().all()
        assert len(fact_checks) == 0

    @pytest.mark.asyncio
    async def test_fact_check_uses_first_claim_only(self, db_session: AsyncSession) -> None:
        """Test that FactCheck is created only for the first claim when multiple exist"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.services.workflow_service import WorkflowService

        # Create admin user
        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Create submission
        submission = Submission(
            user_id=admin.id,
            content="Multiple claims submission",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.QUEUED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Create multiple claims
        claim1 = Claim(content="First claim to check", source="user_submission")
        claim2 = Claim(content="Second claim to check", source="user_submission")
        claim3 = Claim(content="Third claim to check", source="user_submission")
        db_session.add_all([claim1, claim2, claim3])
        await db_session.commit()
        await db_session.refresh(claim1)
        await db_session.refresh(claim2)
        await db_session.refresh(claim3)

        # Link all claims to submission
        submission.claims.append(claim1)
        submission.claims.append(claim2)
        submission.claims.append(claim3)
        await db_session.commit()
        await db_session.refresh(submission)

        # Perform transition to ASSIGNED
        service = WorkflowService(db_session)
        result = await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.ASSIGNED,
            actor_id=admin.id,
            reason="Assigning reviewer",
        )

        assert result.workflow_state == WorkflowState.ASSIGNED

        # Verify only ONE FactCheck was created (for one of the claims)
        fact_check_result = await db_session.execute(select(FactCheck))
        fact_checks = fact_check_result.scalars().all()

        assert len(fact_checks) == 1
        # FactCheck should be for one of the submission's claims
        assert fact_checks[0].claim_id in [claim1.id, claim2.id, claim3.id]
        # Verify it's the claim with the lowest ID (deterministic sorting)
        claim_ids_sorted = sorted([claim1.id, claim2.id, claim3.id])
        assert fact_checks[0].claim_id == claim_ids_sorted[0]

    @pytest.mark.asyncio
    async def test_fact_check_creation_logged_in_transition_metadata(
        self, db_session: AsyncSession
    ) -> None:
        """Test that FactCheck creation is logged in workflow transition metadata"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.services.workflow_service import WorkflowService

        # Create admin user
        admin = User(email="admin@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Create submission
        submission = Submission(
            user_id=admin.id,
            content="Test claim for metadata logging",
            submission_type="text",
            status="pending",
            workflow_state=WorkflowState.QUEUED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Create and link claim
        claim = Claim(content="Metadata test claim", source="user_submission")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()
        await db_session.refresh(submission)

        # Perform transition to ASSIGNED
        service = WorkflowService(db_session)
        await service.transition(
            submission_id=submission.id,
            to_state=WorkflowState.ASSIGNED,
            actor_id=admin.id,
            reason="Assigning reviewer",
        )

        # Get the transition and check metadata
        transitions = await service.get_transition_history(submission.id)
        assert len(transitions) == 1

        # Verify metadata contains fact_check creation info
        transition = transitions[0]
        assert transition.transition_metadata is not None
        assert "fact_check_created" in transition.transition_metadata
        assert transition.transition_metadata["fact_check_created"] is True

        # Get created FactCheck ID from metadata
        fact_check_id = transition.transition_metadata.get("fact_check_id")
        assert fact_check_id is not None

        # Verify the FactCheck exists with that ID
        fact_check_result = await db_session.execute(
            select(FactCheck).where(FactCheck.claim_id == claim.id)
        )
        fact_check = fact_check_result.scalar_one()
        assert str(fact_check.id) == fact_check_id
