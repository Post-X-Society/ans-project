"""
Tests for Submissions List API with role-based filtering - TDD Approach (Tests written FIRST)

These tests are written BEFORE implementation and should FAIL initially (RED phase).
Once implementation is complete, these tests should pass (GREEN phase).
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.submission import Submission
from app.models.submission_reviewer import SubmissionReviewer
from app.models.user import User, UserRole

# ============================================================================
# Fixtures for test users and submissions
# ============================================================================


@pytest.fixture
async def submitter_user(db_session: AsyncSession) -> tuple[User, str]:
    """Create a submitter user and return user and token"""
    user = User(
        email="submitter1@example.com",
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
async def submitter_user_2(db_session: AsyncSession) -> tuple[User, str]:
    """Create a second submitter user and return user and token"""
    user = User(
        email="submitter2@example.com",
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
        email="reviewer1@example.com",
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
        email="admin1@example.com",
        password_hash="hashed_password",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return user, token


# ============================================================================
# GET /api/v1/submissions - Basic Role-Based Filtering
# ============================================================================


class TestSubmissionsListRoleBasedFiltering:
    """Tests for GET /api/v1/submissions with role-based filtering"""

    @pytest.mark.asyncio
    async def test_submitter_sees_only_own_submissions(
        self,
        client: TestClient,
        db_session: AsyncSession,
        submitter_user: Any,
        submitter_user_2: Any,
    ) -> None:
        """Test that submitters only see their own submissions"""
        user1, token1 = submitter_user
        user2, _ = submitter_user_2

        # Create 3 submissions for user1
        for i in range(3):
            submission = Submission(
                user_id=user1.id,
                content=f"User1 submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)

        # Create 2 submissions for user2
        for i in range(2):
            submission = Submission(
                user_id=user2.id,
                content=f"User2 submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)

        await db_session.commit()

        # User1 should only see their 3 submissions
        response = client.get(
            "/api/v1/submissions",
            headers={"Authorization": f"Bearer {token1}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        # Verify all items belong to user1
        for item in data["items"]:
            assert item["user_id"] == str(user1.id)

    @pytest.mark.asyncio
    async def test_reviewer_sees_all_submissions(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        submitter_user: Any,
        submitter_user_2: Any,
    ) -> None:
        """Test that reviewers see all submissions"""
        reviewer, reviewer_token = reviewer_user
        user1, _ = submitter_user
        user2, _ = submitter_user_2

        # Create submissions from different users
        for i in range(2):
            submission = Submission(
                user_id=user1.id,
                content=f"User1 submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)

        for i in range(3):
            submission = Submission(
                user_id=user2.id,
                content=f"User2 submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)

        await db_session.commit()

        # Reviewer should see all 5 submissions
        response = client.get(
            "/api/v1/submissions",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    @pytest.mark.asyncio
    async def test_admin_sees_all_submissions(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        submitter_user: Any,
        submitter_user_2: Any,
    ) -> None:
        """Test that admins see all submissions"""
        admin, admin_token = admin_user
        user1, _ = submitter_user
        user2, _ = submitter_user_2

        # Create submissions from different users
        for i in range(4):
            submission = Submission(
                user_id=user1.id,
                content=f"Submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)

        for i in range(3):
            submission = Submission(
                user_id=user2.id,
                content=f"Submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)

        await db_session.commit()

        # Admin should see all 7 submissions
        response = client.get(
            "/api/v1/submissions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 7
        assert len(data["items"]) == 7


# ============================================================================
# GET /api/v1/submissions?assigned_to_me=true - Reviewer Assignment Filtering
# ============================================================================


class TestSubmissionsListAssignedFilter:
    """Tests for assigned_to_me filter parameter"""

    @pytest.mark.asyncio
    async def test_reviewer_with_assigned_to_me_filter(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        submitter_user: Any,
        admin_user: Any,
    ) -> None:
        """Test reviewer using assigned_to_me=true filter"""
        reviewer, reviewer_token = reviewer_user
        submitter, _ = submitter_user
        admin, _ = admin_user

        # Create 5 submissions
        submissions = []
        for i in range(5):
            submission = Submission(
                user_id=submitter.id,
                content=f"Submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)
            await db_session.flush()
            submissions.append(submission)

        # Assign reviewer to 2 of them
        for i in [1, 3]:
            assignment = SubmissionReviewer(
                submission_id=submissions[i].id,
                reviewer_id=reviewer.id,
                assigned_by_id=admin.id,
            )
            db_session.add(assignment)

        await db_session.commit()

        # Without filter: should see all 5
        response = client.get(
            "/api/v1/submissions",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 200
        assert response.json()["total"] == 5

        # With assigned_to_me=true: should see only 2
        response = client.get(
            "/api/v1/submissions?assigned_to_me=true",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        # Verify these are the correct submissions
        returned_ids = {item["id"] for item in data["items"]}
        expected_ids = {str(submissions[1].id), str(submissions[3].id)}
        assert returned_ids == expected_ids

    @pytest.mark.asyncio
    async def test_reviewer_with_no_assignments(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        submitter_user: Any,
    ) -> None:
        """Test reviewer with assigned_to_me=true but no assignments"""
        reviewer, reviewer_token = reviewer_user
        submitter, _ = submitter_user

        # Create 3 submissions but don't assign any to reviewer
        for i in range(3):
            submission = Submission(
                user_id=submitter.id,
                content=f"Submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)

        await db_session.commit()

        # With assigned_to_me=true: should see 0
        response = client.get(
            "/api/v1/submissions?assigned_to_me=true",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_assigned_to_me_filter_ignored_for_admin(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        submitter_user: Any,
    ) -> None:
        """Test that assigned_to_me filter is ignored for admins (they see all)"""
        admin, admin_token = admin_user
        submitter, _ = submitter_user

        # Create 4 submissions
        for i in range(4):
            submission = Submission(
                user_id=submitter.id,
                content=f"Submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)

        await db_session.commit()

        # Admin with assigned_to_me=true should still see all
        response = client.get(
            "/api/v1/submissions?assigned_to_me=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4


# ============================================================================
# GET /api/v1/submissions?status=X - Status Filtering
# ============================================================================


class TestSubmissionsListStatusFilter:
    """Tests for status filter parameter"""

    @pytest.mark.asyncio
    async def test_filter_by_status_pending(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        submitter_user: Any,
    ) -> None:
        """Test filtering by status=pending"""
        reviewer, reviewer_token = reviewer_user
        submitter, _ = submitter_user

        # Create submissions with different statuses
        statuses = ["pending", "pending", "completed", "rejected", "pending"]
        for i, status in enumerate(statuses):
            submission = Submission(
                user_id=submitter.id,
                content=f"Submission {i}",
                submission_type="text",
                status=status,
            )
            db_session.add(submission)

        await db_session.commit()

        # Filter for pending: should get 3
        response = client.get(
            "/api/v1/submissions?status=pending",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        # Verify all returned items have status=pending
        for item in data["items"]:
            assert item["status"] == "pending"

    @pytest.mark.asyncio
    async def test_filter_by_status_completed(
        self,
        client: TestClient,
        db_session: AsyncSession,
        admin_user: Any,
        submitter_user: Any,
    ) -> None:
        """Test filtering by status=completed"""
        admin, admin_token = admin_user
        submitter, _ = submitter_user

        # Create submissions with different statuses
        statuses = ["pending", "completed", "completed", "rejected"]
        for i, status in enumerate(statuses):
            submission = Submission(
                user_id=submitter.id,
                content=f"Submission {i}",
                submission_type="text",
                status=status,
            )
            db_session.add(submission)

        await db_session.commit()

        # Filter for completed: should get 2
        response = client.get(
            "/api/v1/submissions?status=completed",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["status"] == "completed"


# ============================================================================
# Pagination Tests
# ============================================================================


class TestSubmissionsListPagination:
    """Tests for pagination"""

    @pytest.mark.asyncio
    async def test_pagination_page_size(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        submitter_user: Any,
    ) -> None:
        """Test pagination with different page sizes"""
        reviewer, reviewer_token = reviewer_user
        submitter, _ = submitter_user

        # Create 10 submissions
        for i in range(10):
            submission = Submission(
                user_id=submitter.id,
                content=f"Submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)

        await db_session.commit()

        # Get page 1 with page_size=3
        response = client.get(
            "/api/v1/submissions?page=1&page_size=3",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert len(data["items"]) == 3
        assert data["total_pages"] == 4

        # Get page 2
        response = client.get(
            "/api/v1/submissions?page=2&page_size=3",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["items"]) == 3

        # Get page 4 (last page with 1 item)
        response = client.get(
            "/api/v1/submissions?page=4&page_size=3",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 4
        assert len(data["items"]) == 1


# ============================================================================
# Response Format Tests
# ============================================================================


class TestSubmissionsListResponseFormat:
    """Tests for response format including reviewer assignments"""

    @pytest.mark.asyncio
    async def test_response_includes_reviewer_assignments(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        reviewer_user_2: Any,
        submitter_user: Any,
        admin_user: Any,
    ) -> None:
        """Test that response includes reviewer assignment information"""
        reviewer1, _ = reviewer_user
        reviewer2, _ = reviewer_user_2
        submitter, submitter_token = submitter_user
        admin, _ = admin_user

        # Create a submission
        submission = Submission(
            user_id=submitter.id,
            content="Test submission",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.flush()

        # Assign 2 reviewers
        assignment1 = SubmissionReviewer(
            submission_id=submission.id,
            reviewer_id=reviewer1.id,
            assigned_by_id=admin.id,
        )
        assignment2 = SubmissionReviewer(
            submission_id=submission.id,
            reviewer_id=reviewer2.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment1)
        db_session.add(assignment2)
        await db_session.commit()

        # Get submissions
        response = client.get(
            "/api/v1/submissions",
            headers={"Authorization": f"Bearer {submitter_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

        item = data["items"][0]
        # Verify reviewers array exists and contains both reviewers
        assert "reviewers" in item
        assert len(item["reviewers"]) == 2

        # Verify reviewer info structure
        reviewer_ids = {r["id"] for r in item["reviewers"]}
        expected_ids = {str(reviewer1.id), str(reviewer2.id)}
        assert reviewer_ids == expected_ids

        # Each reviewer should have id, email, role
        for reviewer_info in item["reviewers"]:
            assert "id" in reviewer_info
            assert "email" in reviewer_info
            assert "role" in reviewer_info

    @pytest.mark.asyncio
    async def test_response_shows_is_assigned_for_reviewer(
        self,
        client: TestClient,
        db_session: AsyncSession,
        reviewer_user: Any,
        submitter_user: Any,
        admin_user: Any,
    ) -> None:
        """Test that response shows is_assigned_to_me for reviewers"""
        reviewer, reviewer_token = reviewer_user
        submitter, _ = submitter_user
        admin, _ = admin_user

        # Create 2 submissions
        submission1 = Submission(
            user_id=submitter.id,
            content="Submission 1",
            submission_type="text",
            status="pending",
        )
        submission2 = Submission(
            user_id=submitter.id,
            content="Submission 2",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission1)
        db_session.add(submission2)
        await db_session.flush()

        # Assign reviewer to only submission1
        assignment = SubmissionReviewer(
            submission_id=submission1.id,
            reviewer_id=reviewer.id,
            assigned_by_id=admin.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        # Get submissions as reviewer
        response = client.get(
            "/api/v1/submissions",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

        # Find which item is submission1
        for item in data["items"]:
            if item["id"] == str(submission1.id):
                assert item["is_assigned_to_me"] is True
            elif item["id"] == str(submission2.id):
                assert item["is_assigned_to_me"] is False
