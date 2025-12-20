"""
Tests for Reviewer Assignment API - TDD Approach (Tests written FIRST)

These tests are written BEFORE implementation and should FAIL initially (RED phase).
Once implementation is complete, these tests should pass (GREEN phase).
"""

from uuid import uuid4

from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.reviewer_assignments import (
    _format_reviewer_info,
    _get_submission_or_404,
    _get_user_or_404,
    _user_has_permission,
)
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

    token = create_access_token(data={"sub": str(user.id)})
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

    token = create_access_token(data={"sub": str(user.id)})
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

    token = create_access_token(data={"sub": str(user.id)})
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

    token = create_access_token(data={"sub": str(user.id)})
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

    token = create_access_token(data={"sub": str(user.id)})
    return user, token


@pytest.fixture
async def test_submission(db_session: AsyncSession, submitter_user: Any) -> Submission:
    """Create a test submission"""
    user, _ = submitter_user
    submission = Submission(
        user_id=user.id,
        content="Test submission for reviewer assignment",
        submission_type="text",
        status="pending",
    )
    db_session.add(submission)
    await db_session.commit()
    await db_session.refresh(submission)
    return submission


# ============================================================================
# POST /api/v1/submissions/{submission_id}/reviewers - Assign Reviewers
# ============================================================================


class TestAssignReviewers:
    """Tests for POST /api/v1/submissions/{submission_id}/reviewers"""

    @pytest.mark.asyncio
    async def test_admin_can_assign_single_reviewer(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that admin can assign a single reviewer to a submission"""
        admin, admin_token = admin_user
        reviewer, _ = reviewer_user

        payload = {"reviewer_ids": [str(reviewer.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == str(test_submission.id)
        assert "reviewers" in data
        assert len(data["reviewers"]) == 1
        assert data["reviewers"][0]["id"] == str(reviewer.id)
        assert data["reviewers"][0]["email"] == reviewer.email
        assert data["reviewers"][0]["role"] == "reviewer"

    @pytest.mark.asyncio
    async def test_admin_can_assign_multiple_reviewers(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        reviewer_user: Any,
        reviewer_user_2: Any,
        test_submission: Any,
    ) -> None:
        """Test that admin can assign multiple reviewers at once"""
        admin, admin_token = admin_user
        reviewer1, _ = reviewer_user
        reviewer2, _ = reviewer_user_2

        payload = {"reviewer_ids": [str(reviewer1.id), str(reviewer2.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["reviewers"]) == 2
        reviewer_ids = [r["id"] for r in data["reviewers"]]
        assert str(reviewer1.id) in reviewer_ids
        assert str(reviewer2.id) in reviewer_ids

    @pytest.mark.asyncio
    async def test_super_admin_can_assign_reviewers(
        self,
        client: TestClient,
        db_session: AsyncSession,
        super_admin_user: Any,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that super admin can assign reviewers"""
        super_admin, super_admin_token = super_admin_user
        reviewer, _ = reviewer_user

        payload = {"reviewer_ids": [str(reviewer.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["reviewers"]) == 1
        assert data["reviewers"][0]["id"] == str(reviewer.id)

    @pytest.mark.asyncio
    async def test_non_admin_cannot_assign_reviewers(
        self,
        client: TestClient,
        db_session: AsyncSession,
        submitter_user: Any,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that non-admin users (submitter) cannot assign reviewers"""
        submitter, submitter_token = submitter_user
        reviewer, _ = reviewer_user

        payload = {"reviewer_ids": [str(reviewer.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {submitter_token}"},
        )

        assert response.status_code == 403
        assert "detail" in response.json()
        assert "permission" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_reviewer_cannot_assign_reviewers(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        reviewer_user_2: Any,
        test_submission: Any,
    ) -> None:
        """Test that reviewer users cannot assign other reviewers"""
        reviewer1, reviewer1_token = reviewer_user
        reviewer2, _ = reviewer_user_2

        payload = {"reviewer_ids": [str(reviewer2.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {reviewer1_token}"},
        )

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cannot_assign_non_reviewer_users(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        submitter_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that non-reviewer role users cannot be assigned as reviewers"""
        admin, admin_token = admin_user
        submitter, _ = submitter_user

        payload = {"reviewer_ids": [str(submitter.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "detail" in response.json()
        assert "reviewer" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cannot_assign_same_reviewer_twice(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that the same reviewer cannot be assigned twice to same submission"""
        admin, admin_token = admin_user
        reviewer, _ = reviewer_user

        # First assignment should succeed
        payload = {"reviewer_ids": [str(reviewer.id)]}
        response1 = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response1.status_code == 200

        # Second assignment of same reviewer should fail
        response2 = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response2.status_code == 409
        assert "detail" in response2.json()
        assert "already assigned" in response2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cannot_assign_to_nonexistent_submission(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        reviewer_user: Any,
    ) -> None:
        """Test that assignment to non-existent submission returns 404"""
        admin, admin_token = admin_user
        reviewer, _ = reviewer_user

        fake_uuid = "00000000-0000-0000-0000-000000000000"
        payload = {"reviewer_ids": [str(reviewer.id)]}

        response = client.post(
            f"/api/v1/submissions/{fake_uuid}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404
        assert "submission" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cannot_assign_nonexistent_user(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that assigning non-existent user returns 404"""
        admin, admin_token = admin_user

        fake_user_uuid = "00000000-0000-0000-0000-000000000099"
        payload = {"reviewer_ids": [fake_user_uuid]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404
        assert "user" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_assignment_tracks_assigned_by(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that assignment tracks who made the assignment (assigned_by_id)"""
        admin, admin_token = admin_user
        reviewer, _ = reviewer_user

        payload = {"reviewer_ids": [str(reviewer.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

        # Verify in database that assigned_by_id is set correctly
        from sqlalchemy import select

        result = await db_session.execute(
            select(SubmissionReviewer).where(
                SubmissionReviewer.submission_id == test_submission.id,
                SubmissionReviewer.reviewer_id == reviewer.id,
            )
        )
        assignment = result.scalar_one_or_none()
        assert assignment is not None
        assert assignment.assigned_by_id == admin.id

    @pytest.mark.asyncio
    async def test_assign_reviewers_requires_auth(
        self,
        client: TestClient,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that assignment requires authentication"""
        reviewer, _ = reviewer_user

        payload = {"reviewer_ids": [str(reviewer.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_assign_reviewers_empty_list(
        self,
        client: TestClient,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that empty reviewer list returns validation error"""
        admin, admin_token = admin_user

        payload: dict[str, list[str]] = {"reviewer_ids": []}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_assign_reviewers_invalid_uuid(
        self,
        client: TestClient,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that invalid UUID format returns validation error"""
        admin, admin_token = admin_user

        payload = {"reviewer_ids": ["not-a-uuid"]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422


# ============================================================================
# DELETE /api/v1/submissions/{submission_id}/reviewers/{reviewer_id}
# ============================================================================


class TestRemoveReviewer:
    """Tests for DELETE /api/v1/submissions/{submission_id}/reviewers/{reviewer_id}"""

    @pytest.mark.asyncio
    async def test_admin_can_remove_reviewer_assignment(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that admin can remove a reviewer assignment"""
        admin, admin_token = admin_user
        reviewer, _ = reviewer_user

        # First, create an assignment
        assignment = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        # Now remove the assignment
        response = client.delete(
            f"/api/v1/submissions/{test_submission.id}/reviewers/{reviewer.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "removed" in data["message"].lower()

        # Verify assignment is removed from database
        from sqlalchemy import select

        result = await db_session.execute(
            select(SubmissionReviewer).where(
                SubmissionReviewer.submission_id == test_submission.id,
                SubmissionReviewer.reviewer_id == reviewer.id,
            )
        )
        assignment_check = result.scalar_one_or_none()
        assert assignment_check is None

    @pytest.mark.asyncio
    async def test_super_admin_can_remove_reviewer_assignment(
        self,
        client: TestClient,
        db_session: AsyncSession,
        super_admin_user: Any,
        reviewer_user: Any,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that super admin can remove reviewer assignments"""
        super_admin, super_admin_token = super_admin_user
        reviewer, _ = reviewer_user
        admin, _ = admin_user

        # Create an assignment
        assignment = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        # Super admin removes it
        response = client.delete(
            f"/api/v1/submissions/{test_submission.id}/reviewers/{reviewer.id}",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_non_admin_cannot_remove_assignment(
        self,
        client: TestClient,
        db_session: AsyncSession,
        submitter_user: Any,
        reviewer_user: Any,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that non-admin users cannot remove reviewer assignments"""
        submitter, submitter_token = submitter_user
        reviewer, _ = reviewer_user
        admin, _ = admin_user

        # Create an assignment
        assignment = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        # Submitter tries to remove it
        response = client.delete(
            f"/api/v1/submissions/{test_submission.id}/reviewers/{reviewer.id}",
            headers={"Authorization": f"Bearer {submitter_token}"},
        )

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_reviewer_cannot_remove_assignment(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        reviewer_user_2: Any,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that reviewers cannot remove reviewer assignments"""
        reviewer1, reviewer1_token = reviewer_user
        reviewer2, _ = reviewer_user_2
        admin, _ = admin_user

        # Create an assignment for reviewer2
        assignment = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer2.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        # Reviewer1 tries to remove reviewer2's assignment
        response = client.delete(
            f"/api/v1/submissions/{test_submission.id}/reviewers/{reviewer2.id}",
            headers={"Authorization": f"Bearer {reviewer1_token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_removing_nonexistent_assignment_returns_404(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that removing non-existent assignment returns 404"""
        admin, admin_token = admin_user
        reviewer, _ = reviewer_user

        # Try to remove assignment that doesn't exist
        response = client.delete(
            f"/api/v1/submissions/{test_submission.id}/reviewers/{reviewer.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404
        assert "assignment" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_removing_from_nonexistent_submission_returns_404(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        reviewer_user: Any,
    ) -> None:
        """Test that removing from non-existent submission returns 404"""
        admin, admin_token = admin_user
        reviewer, _ = reviewer_user

        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.delete(
            f"/api/v1/submissions/{fake_uuid}/reviewers/{reviewer.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_remove_reviewer_requires_auth(
        self,
        client: TestClient,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that removing reviewer requires authentication"""
        reviewer, _ = reviewer_user

        response = client.delete(
            f"/api/v1/submissions/{test_submission.id}/reviewers/{reviewer.id}",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_remove_reviewer_invalid_uuid(
        self,
        client: TestClient,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that invalid UUID format returns validation error"""
        admin, admin_token = admin_user

        response = client.delete(
            f"/api/v1/submissions/{test_submission.id}/reviewers/not-a-uuid",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422


# ============================================================================
# GET /api/v1/submissions/{submission_id}/reviewers
# ============================================================================


class TestGetAssignedReviewers:
    """Tests for GET /api/v1/submissions/{submission_id}/reviewers"""

    @pytest.mark.asyncio
    async def test_owner_can_view_assigned_reviewers(
        self,
        client: TestClient,
        db_session: AsyncSession,
        submitter_user: Any,
        reviewer_user: Any,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that submission owner can view assigned reviewers"""
        submitter, submitter_token = submitter_user
        reviewer, _ = reviewer_user
        admin, _ = admin_user

        # Create assignment
        assignment = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        # Owner views reviewers
        response = client.get(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            headers={"Authorization": f"Bearer {submitter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == str(reviewer.id)
        assert data[0]["email"] == reviewer.email
        assert data[0]["role"] == "reviewer"

    @pytest.mark.asyncio
    async def test_assigned_reviewer_can_view_list(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        reviewer_user_2: Any,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that assigned reviewer can view list of all reviewers"""
        reviewer1, reviewer1_token = reviewer_user
        reviewer2, _ = reviewer_user_2
        admin, _ = admin_user

        # Create assignments for both reviewers
        assignment1 = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer1.id,
            assigned_by_id=admin.id,
        )
        assignment2 = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer2.id,
            assigned_by_id=admin.id,
        )
        db_session.add_all([assignment1, assignment2])
        await db_session.commit()

        # Reviewer1 views all reviewers
        response = client.get(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            headers={"Authorization": f"Bearer {reviewer1_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        reviewer_ids = [r["id"] for r in data]
        assert str(reviewer1.id) in reviewer_ids
        assert str(reviewer2.id) in reviewer_ids

    @pytest.mark.asyncio
    async def test_admin_can_view_list(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        reviewer_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that admin can view list of assigned reviewers"""
        admin, admin_token = admin_user
        reviewer, _ = reviewer_user

        # Create assignment
        assignment = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        # Admin views reviewers
        response = client.get(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(reviewer.id)

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_no_assignments(
        self,
        client: TestClient,
        db_session: AsyncSession,
        submitter_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that endpoint returns empty list when no reviewers assigned"""
        submitter, submitter_token = submitter_user

        response = client.get(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            headers={"Authorization": f"Bearer {submitter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_returns_full_user_objects(
        self,
        client: TestClient,
        db_session: AsyncSession,
        submitter_user: Any,
        reviewer_user: Any,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that endpoint returns full user objects with id, email, role"""
        submitter, submitter_token = submitter_user
        reviewer, _ = reviewer_user
        admin, _ = admin_user

        # Create assignment
        assignment = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        response = client.get(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            headers={"Authorization": f"Bearer {submitter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        reviewer_data = data[0]
        assert "id" in reviewer_data
        assert "email" in reviewer_data
        assert "role" in reviewer_data
        assert reviewer_data["id"] == str(reviewer.id)
        assert reviewer_data["email"] == reviewer.email
        assert reviewer_data["role"] == "reviewer"

    @pytest.mark.asyncio
    async def test_non_owner_non_reviewer_cannot_view(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that users who are not owner or assigned reviewer cannot view"""
        reviewer, _ = reviewer_user
        admin, _ = admin_user

        # Create a different submitter who owns this submission
        other_submitter = User(
            email="othersubmitter@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(other_submitter)
        await db_session.commit()
        await db_session.refresh(other_submitter)

        other_submitter_token = create_access_token(data={"sub": str(other_submitter.id)})

        # Create assignment for reviewer
        assignment = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        # Other submitter (not owner) tries to view
        response = client.get(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            headers={"Authorization": f"Bearer {other_submitter_token}"},
        )

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_unassigned_reviewer_cannot_view(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        reviewer_user_2: Any,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that unassigned reviewer cannot view reviewer list"""
        reviewer1, _ = reviewer_user
        reviewer2, reviewer2_token = reviewer_user_2
        admin, _ = admin_user

        # Assign only reviewer1
        assignment = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer1.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        # Reviewer2 (not assigned) tries to view
        response = client.get(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            headers={"Authorization": f"Bearer {reviewer2_token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_reviewers_requires_auth(
        self,
        client: TestClient,
        test_submission: Any,
    ) -> None:
        """Test that viewing reviewers requires authentication"""
        response = client.get(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_reviewers_nonexistent_submission(
        self,
        client: TestClient,
        admin_user: Any,
    ) -> None:
        """Test that viewing reviewers for non-existent submission returns 404"""
        admin, admin_token = admin_user

        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/api/v1/submissions/{fake_uuid}/reviewers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_reviewers_invalid_uuid(
        self,
        client: TestClient,
        admin_user: Any,
    ) -> None:
        """Test that invalid submission UUID returns validation error"""
        admin, admin_token = admin_user

        response = client.get(
            "/api/v1/submissions/not-a-uuid/reviewers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422


# ============================================================================
# Additional Edge Cases and Integration Tests
# ============================================================================


class TestReviewerAssignmentEdgeCases:
    """Additional edge case tests for reviewer assignment functionality"""

    @pytest.mark.asyncio
    async def test_super_admin_can_be_assigned_as_reviewer_role(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that super_admin role user cannot be assigned as reviewer"""
        admin, admin_token = admin_user

        # Create a super admin
        super_admin = User(
            email="superadmin2@example.com",
            password_hash="hashed_password",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        db_session.add(super_admin)
        await db_session.commit()
        await db_session.refresh(super_admin)

        payload = {"reviewer_ids": [str(super_admin.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Super admins should not be assignable as reviewers
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_admin_role_cannot_be_assigned_as_reviewer(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that admin role user cannot be assigned as reviewer"""
        admin1, admin1_token = admin_user

        # Create another admin
        admin2 = User(
            email="admin2@example.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin2)
        await db_session.commit()
        await db_session.refresh(admin2)

        payload = {"reviewer_ids": [str(admin2.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin1_token}"},
        )

        # Admins should not be assignable as reviewers
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_assign_inactive_reviewer(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that inactive reviewer users cannot be assigned"""
        admin, admin_token = admin_user

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

        payload = {"reviewer_ids": [str(inactive_reviewer.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "inactive" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_assignment_to_completed_submission_still_allowed(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        reviewer_user: Any,
        submitter_user: Any,
    ) -> None:
        """Test that reviewers can be assigned even to completed submissions"""
        admin, admin_token = admin_user
        reviewer, _ = reviewer_user
        submitter, _ = submitter_user

        # Create a completed submission
        completed_submission = Submission(
            user_id=submitter.id,
            content="Completed submission",
            submission_type="text",
            status="completed",
        )
        db_session.add(completed_submission)
        await db_session.commit()
        await db_session.refresh(completed_submission)

        payload = {"reviewer_ids": [str(reviewer.id)]}

        response = client.post(
            f"/api/v1/submissions/{completed_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Should still allow assignment
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_multiple_assignments_with_partial_duplicates(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        reviewer_user: Any,
        reviewer_user_2: Any,
        test_submission: Any,
    ) -> None:
        """Test assigning multiple reviewers when one is already assigned"""
        admin, admin_token = admin_user
        reviewer1, _ = reviewer_user
        reviewer2, _ = reviewer_user_2

        # First assign reviewer1
        assignment = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer1.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        # Try to assign both reviewer1 (duplicate) and reviewer2 (new)
        payload = {"reviewer_ids": [str(reviewer1.id), str(reviewer2.id)]}

        response = client.post(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Should fail with conflict
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_reviewer_list_shows_multiple_reviewers_correctly(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        submitter_user: Any,
        test_submission: Any,
    ) -> None:
        """Test that list endpoint correctly shows multiple assigned reviewers"""
        admin, _ = admin_user
        submitter, submitter_token = submitter_user

        # Create 3 reviewers
        reviewers = []
        for i in range(3):
            reviewer = User(
                email=f"reviewer{i}@example.com",
                password_hash="hashed_password",
                role=UserRole.REVIEWER,
                is_active=True,
            )
            db_session.add(reviewer)
            reviewers.append(reviewer)

        await db_session.commit()
        for reviewer in reviewers:
            await db_session.refresh(reviewer)

        # Assign all 3 reviewers
        for reviewer in reviewers:
            assignment = SubmissionReviewer(
                submission_id=test_submission.id,
                reviewer_id=reviewer.id,
                assigned_by_id=admin.id,
            )
            db_session.add(assignment)
        await db_session.commit()

        # Get reviewer list
        response = client.get(
            f"/api/v1/submissions/{test_submission.id}/reviewers",
            headers={"Authorization": f"Bearer {submitter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        returned_emails = [r["email"] for r in data]
        for reviewer in reviewers:
            assert reviewer.email in returned_emails


# ============================================================================
# Unit Tests for Helper Functions (for coverage)
# ============================================================================


class TestHelperFunctions:
    """Unit tests for internal helper functions"""

    def test_user_has_permission_assign_action(self) -> None:
        """Test permission check for assign action"""
        # Admin can assign
        admin = User(email="admin@example.com", role=UserRole.ADMIN, is_active=True)
        assert _user_has_permission(admin, "assign") is True

        # Super admin can assign
        super_admin = User(
            email="superadmin@example.com", role=UserRole.SUPER_ADMIN, is_active=True
        )
        assert _user_has_permission(super_admin, "assign") is True

        # Reviewer cannot assign
        reviewer = User(email="reviewer@example.com", role=UserRole.REVIEWER, is_active=True)
        assert _user_has_permission(reviewer, "assign") is False

        # Submitter cannot assign
        submitter = User(email="submitter@example.com", role=UserRole.SUBMITTER, is_active=True)
        assert _user_has_permission(submitter, "assign") is False

    def test_user_has_permission_remove_action(self) -> None:
        """Test permission check for remove action"""
        # Admin can remove
        admin = User(email="admin@example.com", role=UserRole.ADMIN, is_active=True)
        assert _user_has_permission(admin, "remove") is True

        # Super admin can remove
        super_admin = User(
            email="superadmin@example.com", role=UserRole.SUPER_ADMIN, is_active=True
        )
        assert _user_has_permission(super_admin, "remove") is True

        # Reviewer cannot remove
        reviewer = User(email="reviewer@example.com", role=UserRole.REVIEWER, is_active=True)
        assert _user_has_permission(reviewer, "remove") is False

    def test_user_has_permission_view_action(self) -> None:
        """Test permission check for view action"""
        # Admin can view
        admin = User(email="admin@example.com", role=UserRole.ADMIN, is_active=True)
        assert _user_has_permission(admin, "view") is True

        # Super admin can view
        super_admin = User(
            email="superadmin@example.com", role=UserRole.SUPER_ADMIN, is_active=True
        )
        assert _user_has_permission(super_admin, "view") is True

        # Reviewer can view
        reviewer = User(email="reviewer@example.com", role=UserRole.REVIEWER, is_active=True)
        assert _user_has_permission(reviewer, "view") is True

        # Submitter can view
        submitter = User(email="submitter@example.com", role=UserRole.SUBMITTER, is_active=True)
        assert _user_has_permission(submitter, "view") is True

    def test_user_has_permission_unknown_action(self) -> None:
        """Test permission check for unknown action returns False"""
        admin = User(email="admin@example.com", role=UserRole.ADMIN, is_active=True)
        assert _user_has_permission(admin, "unknown_action") is False

    @pytest.mark.asyncio
    async def test_get_submission_or_404_found(
        self, db_session: AsyncSession, submitter_user: Any, test_submission: Any
    ) -> None:
        """Test _get_submission_or_404 when submission exists"""
        submission = await _get_submission_or_404(db_session, test_submission.id)
        assert submission.id == test_submission.id

    @pytest.mark.asyncio
    async def test_get_submission_or_404_not_found(self, db_session: AsyncSession) -> None:
        """Test _get_submission_or_404 raises 404 when submission not found"""
        fake_uuid = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await _get_submission_or_404(db_session, fake_uuid)
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_get_user_or_404_found(self, db_session: AsyncSession, reviewer_user: Any) -> None:
        """Test _get_user_or_404 when user exists"""
        reviewer, _ = reviewer_user
        user = await _get_user_or_404(db_session, reviewer.id)
        assert user.id == reviewer.id

    @pytest.mark.asyncio
    async def test_get_user_or_404_not_found(self, db_session: AsyncSession) -> None:
        """Test _get_user_or_404 raises 404 when user not found"""
        fake_uuid = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await _get_user_or_404(db_session, fake_uuid)
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_format_reviewer_info(
        self, db_session: AsyncSession, reviewer_user: Any, admin_user: Any, test_submission: Any
    ) -> None:
        """Test _format_reviewer_info formats data correctly"""
        reviewer, _ = reviewer_user
        admin, _ = admin_user

        # Create a real assignment
        assignment = SubmissionReviewer(
            submission_id=test_submission.id,
            reviewer_id=reviewer.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)

        # Load the reviewer relationship
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await db_session.execute(
            select(SubmissionReviewer)
            .where(SubmissionReviewer.id == assignment.id)
            .options(selectinload(SubmissionReviewer.reviewer))
        )
        loaded_assignment = result.scalar_one()

        info = _format_reviewer_info(loaded_assignment)

        assert info.id == reviewer.id
        assert info.email == reviewer.email
        assert info.role == "reviewer"
        assert info.full_name is None
        assert info.assigned_at == loaded_assignment.created_at
