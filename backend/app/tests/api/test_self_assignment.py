"""
Tests for Reviewer Self-Assignment API - TDD Approach (Tests written FIRST)

Issue #140: POST /api/v1/submissions/{submission_id}/reviewers/me

These tests verify the self-assignment functionality where reviewers can
assign themselves to submissions without admin intervention.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.submission import Submission
from app.models.submission_reviewer import SubmissionReviewer
from app.models.user import User, UserRole

# ============================================================================
# Fixtures for test users with different roles
# ============================================================================


@pytest.fixture
async def submitter_user(db_session: AsyncSession) -> tuple[User, str]:
    """Create a submitter user and return user and token"""
    user = User(
        email="submitter@example.com",
        password_hash="hashed_password",
        role=UserRole.SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token: str = create_access_token(data={"sub": str(user.id)})
    return user, token


@pytest.fixture
async def reviewer_user(db_session: AsyncSession) -> tuple[User, str]:
    """Create a reviewer user and return user and token"""
    user = User(
        email="reviewer@example.com",
        password_hash="hashed_password",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token: str = create_access_token(data={"sub": str(user.id)})
    return user, token


@pytest.fixture
async def reviewer_user_2(db_session: AsyncSession) -> tuple[User, str]:
    """Create a second reviewer user and return user and token"""
    user = User(
        email="reviewer2@example.com",
        password_hash="hashed_password",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token: str = create_access_token(data={"sub": str(user.id)})
    return user, token


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> tuple[User, str]:
    """Create an admin user and return user and token"""
    user = User(
        email="admin@example.com",
        password_hash="hashed_password",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token: str = create_access_token(data={"sub": str(user.id)})
    return user, token


@pytest.fixture
async def super_admin_user(db_session: AsyncSession) -> tuple[User, str]:
    """Create a super admin user and return user and token"""
    user = User(
        email="superadmin@example.com",
        password_hash="hashed_password",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token: str = create_access_token(data={"sub": str(user.id)})
    return user, token


@pytest.fixture
async def test_submission(db_session: AsyncSession, submitter_user: Any) -> Submission:
    """Create a test submission"""
    user, _ = submitter_user
    submission = Submission(
        user_id=user.id,
        content="Test submission for self-assignment",
        submission_type="text",
        status="pending",
    )
    db_session.add(submission)
    await db_session.commit()
    await db_session.refresh(submission)
    return submission


# ============================================================================
# POST /api/v1/submissions/{submission_id}/reviewers/me - Self-Assignment
# ============================================================================


class TestSelfAssignment:
    """Tests for POST /api/v1/submissions/{submission_id}/reviewers/me"""

    @pytest.mark.asyncio
    async def test_reviewer_can_self_assign_returns_201(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that a reviewer can self-assign to a submission (returns 201 Created)"""
        reviewer, reviewer_token = reviewer_user

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        assert response.status_code == 201
        data: dict[str, Any] = response.json()
        assert "message" in data
        assert "submission_id" in data
        assert "reviewer_id" in data
        assert data["submission_id"] == str(test_submission.id)
        assert data["reviewer_id"] == str(reviewer.id)

    @pytest.mark.asyncio
    async def test_self_assignment_creates_db_record(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that self-assignment creates a SubmissionReviewer record in database"""
        reviewer, reviewer_token = reviewer_user

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        assert response.status_code == 201

        # Verify in database
        result = await db_session.execute(
            select(SubmissionReviewer).where(
                SubmissionReviewer.submission_id == test_submission.id,
                SubmissionReviewer.reviewer_id == reviewer.id,
            )
        )
        assignment = result.scalar_one_or_none()
        assert assignment is not None
        # For self-assignment, assigned_by_id should be the same as reviewer_id
        assert assignment.assigned_by_id == reviewer.id

    @pytest.mark.asyncio
    async def test_idempotent_self_assignment_returns_200(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that repeated self-assignment returns 200 OK (idempotent)"""
        reviewer, reviewer_token = reviewer_user

        # First self-assignment should return 201
        response1 = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response1.status_code == 201

        # Second self-assignment should return 200 (already assigned)
        response2 = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response2.status_code == 200
        data: dict[str, Any] = response2.json()
        assert "already" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_admin_can_self_assign(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that an admin can self-assign to a submission"""
        admin, admin_token = admin_user

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 201
        data: dict[str, Any] = response.json()
        assert data["reviewer_id"] == str(admin.id)

    @pytest.mark.asyncio
    async def test_super_admin_can_self_assign(
        self,
        client: TestClient,
        db_session: AsyncSession,
        super_admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that a super admin can self-assign to a submission"""
        super_admin, super_admin_token = super_admin_user

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )

        assert response.status_code == 201
        data: dict[str, Any] = response.json()
        assert data["reviewer_id"] == str(super_admin.id)

    @pytest.mark.asyncio
    async def test_submitter_cannot_self_assign(
        self,
        client: TestClient,
        db_session: AsyncSession,
        submitter_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that a submitter (non-reviewer) cannot self-assign"""
        submitter, submitter_token = submitter_user

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {submitter_token}"},
        )

        assert response.status_code == 403
        data: dict[str, Any] = response.json()
        assert "detail" in data
        assert "permission" in data["detail"].lower() or "role" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_self_assignment_requires_auth(
        self,
        client: TestClient,
        test_submission: Any,
    ) -> None:
        """Test that self-assignment requires authentication"""
        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_self_assignment_to_nonexistent_submission_returns_404(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
    ) -> None:
        """Test that self-assignment to non-existent submission returns 404"""
        reviewer, reviewer_token = reviewer_user
        fake_uuid: str = "00000000-0000-0000-0000-000000000000"

        response = client.post(
            f"/api/v1/submissions/{fake_uuid}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        assert response.status_code == 404
        data: dict[str, Any] = response.json()
        assert "submission" in data["detail"].lower() or "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_self_assignment_with_invalid_uuid_returns_422(
        self,
        client: TestClient,
        reviewer_user: Any,
    ) -> None:
        """Test that self-assignment with invalid UUID format returns 422"""
        reviewer, reviewer_token = reviewer_user

        response = client.post(
            "/api/v1/submissions/not-a-valid-uuid/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_multiple_reviewers_can_self_assign_to_same_submission(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        reviewer_user_2: Any,
        test_submission: Any,
    ) -> None:
        """Test that multiple reviewers can self-assign to the same submission"""
        reviewer1, reviewer1_token = reviewer_user
        reviewer2, reviewer2_token = reviewer_user_2

        # First reviewer self-assigns
        response1 = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer1_token}"},
        )
        assert response1.status_code == 201

        # Second reviewer self-assigns
        response2 = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer2_token}"},
        )
        assert response2.status_code == 201

        # Verify both are in database
        result = await db_session.execute(
            select(SubmissionReviewer).where(SubmissionReviewer.submission_id == test_submission.id)
        )
        assignments = result.scalars().all()
        assert len(assignments) == 2
        reviewer_ids = [a.reviewer_id for a in assignments]
        assert reviewer1.id in reviewer_ids
        assert reviewer2.id in reviewer_ids

    @pytest.mark.asyncio
    async def test_self_assignment_does_not_require_request_body(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that self-assignment does not require a request body (user from JWT)"""
        reviewer, reviewer_token = reviewer_user

        # No JSON body provided
        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_inactive_reviewer_cannot_self_assign(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_submission: Any,
    ) -> None:
        """Test that an inactive reviewer cannot self-assign"""
        # Create inactive reviewer
        inactive_reviewer = User(
            email="inactive.reviewer@example.com",
            password_hash="hashed_password",
            role=UserRole.REVIEWER,
            is_active=False,
        )
        db_session.add(inactive_reviewer)
        await db_session.commit()
        await db_session.refresh(inactive_reviewer)

        token: str = create_access_token(data={"sub": str(inactive_reviewer.id)})

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should return 403 because the user is inactive
        assert response.status_code == 403


# ============================================================================
# Integration Tests - Self-Assignment with existing workflows
# ============================================================================


class TestSelfAssignmentIntegration:
    """Integration tests for self-assignment with other endpoints"""

    @pytest.mark.asyncio
    async def test_self_assigned_reviewer_appears_in_reviewer_list(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that self-assigned reviewer appears in GET /submissions/{id}/reviewers"""
        reviewer, reviewer_token = reviewer_user
        admin, admin_token = admin_user

        # Self-assign
        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 201

        # Verify via GET endpoint (admin can view)
        list_response = client.get(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_response.status_code == 200
        data: list[dict[str, Any]] = list_response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(reviewer.id)

    @pytest.mark.asyncio
    async def test_self_assigned_reviewer_can_view_submission(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that a self-assigned reviewer can view the submission"""
        reviewer, reviewer_token = reviewer_user

        # Self-assign
        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 201

        # Verify can view submission
        get_response = client.get(
            f"/api/v1/submissions/{test_submission.id}",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert get_response.status_code == 200
        data: dict[str, Any] = get_response.json()
        assert data["id"] == str(test_submission.id)

    @pytest.mark.asyncio
    async def test_admin_can_remove_self_assigned_reviewer(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that admin can remove a self-assigned reviewer"""
        reviewer, reviewer_token = reviewer_user
        admin, admin_token = admin_user

        # Self-assign
        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 201

        # Admin removes the assignment
        delete_response = client.delete(
            f"/api/v1/submissions/{test_submission.id}/reviewers/{reviewer.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert delete_response.status_code == 200

        # Verify assignment removed
        result = await db_session.execute(
            select(SubmissionReviewer).where(
                SubmissionReviewer.submission_id == test_submission.id,
                SubmissionReviewer.reviewer_id == reviewer.id,
            )
        )
        assignment = result.scalar_one_or_none()
        assert assignment is None

    @pytest.mark.asyncio
    async def test_self_assignment_with_assigned_to_me_filter(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that self-assigned submissions appear with assigned_to_me filter"""
        reviewer, reviewer_token = reviewer_user

        # Self-assign
        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers/me",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 201

        # List submissions with assigned_to_me=true
        list_response = client.get(
            "/api/v1/submissions?assigned_to_me=true",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert list_response.status_code == 200
        data: dict[str, Any] = list_response.json()
        assert "items" in data
        # Should contain the self-assigned submission
        submission_ids = [item["id"] for item in data["items"]]
        assert str(test_submission.id) in submission_ids
