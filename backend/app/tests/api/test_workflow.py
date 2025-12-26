"""
Tests for Workflow API Endpoints - TDD Approach (Tests written FIRST)

Issue #60: Backend: Rating & Workflow API Endpoints (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- POST /api/v1/workflow/{submission_id}/transition - State transition (role-based)
- GET /api/v1/workflow/{submission_id}/history - Full timeline (authenticated)
- GET /api/v1/workflow/{submission_id}/current - Current state (authenticated)
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.models.workflow_transition import WorkflowState, WorkflowTransition


class TestWorkflowTransition:
    """Tests for POST /api/v1/workflow/{submission_id}/transition."""

    @pytest.mark.asyncio
    async def test_admin_can_transition_submitted_to_queued(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can transition submission from SUBMITTED to QUEUED."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        submission = Submission(
            content="Test claim content",
            source_url="https://example.com",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submission)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        payload = {
            "to_state": "queued",
            "reason": "Submission validated for processing",
        }
        response = client.post(
            f"/api/v1/workflow/{submission.id}/transition",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_state"] == "queued"

    @pytest.mark.asyncio
    async def test_reviewer_can_transition_assigned_to_in_research(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test reviewer can transition from ASSIGNED to IN_RESEARCH."""
        # Arrange
        reviewer = User(
            email="reviewer@example.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(reviewer)

        submission = Submission(
            content="Test claim for research",
            source_url="https://example.com",
            workflow_state=WorkflowState.ASSIGNED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(reviewer)
        await db_session.refresh(submission)

        token = create_access_token(data={"sub": str(reviewer.id)})

        # Act
        payload = {
            "to_state": "in_research",
            "reason": "Starting research on this claim",
        }
        response = client.post(
            f"/api/v1/workflow/{submission.id}/transition",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_state"] == "in_research"

    @pytest.mark.asyncio
    async def test_super_admin_can_transition_final_approval_to_published(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test only super admin can transition FINAL_APPROVAL to PUBLISHED."""
        # Arrange
        super_admin = User(
            email="superadmin@example.com",
            password_hash="hashed",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        db_session.add(super_admin)

        submission = Submission(
            content="Test claim ready for publication",
            source_url="https://example.com",
            workflow_state=WorkflowState.FINAL_APPROVAL,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(super_admin)
        await db_session.refresh(submission)

        token = create_access_token(data={"sub": str(super_admin.id)})

        # Act
        payload = {
            "to_state": "published",
            "reason": "Approved for publication",
        }
        response = client.post(
            f"/api/v1/workflow/{submission.id}/transition",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_state"] == "published"

    @pytest.mark.asyncio
    async def test_admin_cannot_transition_final_approval_to_published(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test regular admin cannot transition FINAL_APPROVAL to PUBLISHED (super admin only)."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        submission = Submission(
            content="Test claim",
            source_url="https://example.com",
            workflow_state=WorkflowState.FINAL_APPROVAL,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submission)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        payload = {
            "to_state": "published",
            "reason": "Attempting to publish",
        }
        response = client.post(
            f"/api/v1/workflow/{submission.id}/transition",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_submitter_cannot_transition(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test submitter cannot perform any workflow transitions."""
        # Arrange
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(submitter)

        submission = Submission(
            content="Test claim",
            source_url="https://example.com",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submitter)
        await db_session.refresh(submission)

        token = create_access_token(data={"sub": str(submitter.id)})

        # Act
        payload = {
            "to_state": "queued",
            "reason": "Attempting transition",
        }
        response = client.post(
            f"/api/v1/workflow/{submission.id}/transition",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_transition_returns_400(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test invalid state transition returns 400."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        submission = Submission(
            content="Test claim",
            source_url="https://example.com",
            workflow_state=WorkflowState.SUBMITTED,  # Can't go directly to PUBLISHED
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submission)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        payload = {
            "to_state": "published",  # Invalid - can't skip intermediate states
            "reason": "Trying to skip states",
        }
        response = client.post(
            f"/api/v1/workflow/{submission.id}/transition",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_transition_submission_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test transition on non-existent submission returns 404."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        token = create_access_token(data={"sub": str(admin.id)})
        fake_id = uuid4()

        # Act
        payload = {
            "to_state": "queued",
            "reason": "Test",
        }
        response = client.post(
            f"/api/v1/workflow/{fake_id}/transition",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_transition_requires_auth(self, client: TestClient) -> None:
        """Test transition requires authentication."""
        fake_id = uuid4()
        payload = {"to_state": "queued", "reason": "Test"}
        response = client.post(
            f"/api/v1/workflow/{fake_id}/transition",
            json=payload,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_transition_with_metadata(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test transition with optional metadata."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        submission = Submission(
            content="Test claim with metadata",
            source_url="https://example.com",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submission)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        payload = {
            "to_state": "queued",
            "reason": "Processing submission",
            "metadata": {"priority": "high", "notes": "Urgent review needed"},
        }
        response = client.post(
            f"/api/v1/workflow/{submission.id}/transition",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200


class TestGetWorkflowHistory:
    """Tests for GET /api/v1/workflow/{submission_id}/history."""

    @pytest.mark.asyncio
    async def test_get_history_success(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test retrieving workflow transition history."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        submission = Submission(
            content="Test claim with history",
            source_url="https://example.com",
            workflow_state=WorkflowState.QUEUED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submission)

        # Create transition history
        transition1 = WorkflowTransition(
            submission_id=submission.id,
            from_state=None,
            to_state=WorkflowState.SUBMITTED,
            actor_id=admin.id,
            reason="Initial submission",
        )
        transition2 = WorkflowTransition(
            submission_id=submission.id,
            from_state=WorkflowState.SUBMITTED,
            to_state=WorkflowState.QUEUED,
            actor_id=admin.id,
            reason="Moved to queue",
        )
        db_session.add(transition1)
        db_session.add(transition2)
        await db_session.commit()

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        response = client.get(
            f"/api/v1/workflow/{submission.id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["to_state"] == "submitted"
        assert data[1]["to_state"] == "queued"

    @pytest.mark.asyncio
    async def test_get_history_empty(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test retrieving history when no transitions exist."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        submission = Submission(
            content="New submission",
            source_url="https://example.com",
            workflow_state=WorkflowState.SUBMITTED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submission)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        response = client.get(
            f"/api/v1/workflow/{submission.id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_get_history_requires_auth(self, client: TestClient) -> None:
        """Test history endpoint requires authentication."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/workflow/{fake_id}/history")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_history_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test history for non-existent submission returns 404."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        token = create_access_token(data={"sub": str(admin.id)})
        fake_id = uuid4()

        # Act
        response = client.get(
            f"/api/v1/workflow/{fake_id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 404


class TestGetCurrentState:
    """Tests for GET /api/v1/workflow/{submission_id}/current."""

    @pytest.mark.asyncio
    async def test_get_current_state_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test retrieving current workflow state."""
        # Arrange
        user = User(
            email="user@example.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(user)

        submission = Submission(
            content="Test claim",
            source_url="https://example.com",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(submission)

        token = create_access_token(data={"sub": str(user.id)})

        # Act
        response = client.get(
            f"/api/v1/workflow/{submission.id}/current",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["current_state"] == "in_research"
        assert data["submission_id"] == str(submission.id)

    @pytest.mark.asyncio
    async def test_get_current_state_includes_valid_transitions(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test current state response includes valid next transitions."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        submission = Submission(
            content="Test claim",
            source_url="https://example.com",
            workflow_state=WorkflowState.DRAFT_READY,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submission)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        response = client.get(
            f"/api/v1/workflow/{submission.id}/current",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["current_state"] == "draft_ready"
        assert "valid_transitions" in data
        # DRAFT_READY can go to ADMIN_REVIEW or NEEDS_MORE_RESEARCH
        assert "admin_review" in data["valid_transitions"]
        assert "needs_more_research" in data["valid_transitions"]

    @pytest.mark.asyncio
    async def test_get_current_state_requires_auth(self, client: TestClient) -> None:
        """Test current state endpoint requires authentication."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/workflow/{fake_id}/current")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_state_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test current state for non-existent submission returns 404."""
        # Arrange
        user = User(
            email="user@example.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token(data={"sub": str(user.id)})
        fake_id = uuid4()

        # Act
        response = client.get(
            f"/api/v1/workflow/{fake_id}/current",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 404
