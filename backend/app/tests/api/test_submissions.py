"""
Tests for Submissions API - TDD Approach (Tests written FIRST)
"""

from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.submission import Submission
from app.models.user import User, UserRole


class TestCreateSubmission:
    """Tests for POST /api/v1/submissions"""

    @pytest.mark.asyncio
    async def test_create_submission_success(
        self, client: TestClient, db_session: AsyncSession, auth_user: Any
    ) -> None:
        """Test creating a submission successfully"""
        user, token = auth_user
        payload = {"content": "Is climate change real?", "type": "text"}

        response = client.post(
            "/api/v1/submissions", json=payload, headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert UUID(data["id"])  # Valid UUID
        assert data["content"] == "Is climate change real?"
        assert data["submission_type"] == "text"
        assert data["status"] == "processing"  # Should be processing after claim extraction
        assert "created_at" in data
        assert "updated_at" in data
        assert "claims" in data
        assert "extracted_claims_count" in data

    @pytest.mark.asyncio
    async def test_create_submission_content_too_short(
        self, client: TestClient, auth_user: Any
    ) -> None:
        """Test creating submission with content too short"""
        user, token = auth_user
        payload = {"content": "Short", "type": "text"}  # Less than 10 chars

        response = client.post(
            "/api/v1/submissions", json=payload, headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_create_submission_content_empty(
        self, client: TestClient, auth_user: Any
    ) -> None:
        """Test creating submission with empty content"""
        user, token = auth_user
        payload = {"content": "          ", "type": "text"}  # Only whitespace

        response = client.post(
            "/api/v1/submissions", json=payload, headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_submission_invalid_type(self, client: TestClient, auth_user: Any) -> None:
        """Test creating submission with invalid type"""
        user, token = auth_user
        payload = {"content": "Valid content here", "type": "invalid"}

        response = client.post(
            "/api/v1/submissions", json=payload, headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_submission_missing_fields(
        self, client: TestClient, auth_user: Any
    ) -> None:
        """Test creating submission with missing required fields"""
        user, token = auth_user
        payload = {"content": "Missing type field"}

        response = client.post(
            "/api/v1/submissions", json=payload, headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422


class TestGetSubmission:
    """Tests for GET /api/v1/submissions/{id}"""

    @pytest.mark.asyncio
    async def test_get_submission_success(
        self, client: TestClient, db_session: AsyncSession, auth_user: Any
    ) -> None:
        """Test getting a submission by ID"""
        # Use authenticated user
        user, token = auth_user

        # Create a submission
        submission = Submission(
            user_id=user.id,
            content="Test claim content",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Get the submission
        response = client.get(
            f"/api/v1/submissions/{submission.id}", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(submission.id)
        assert data["content"] == "Test claim content"
        assert data["submission_type"] == "text"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_submission_not_found(self, client: TestClient, auth_user: Any) -> None:
        """Test getting non-existent submission"""
        user, token = auth_user
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/api/v1/submissions/{fake_uuid}", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_get_submission_invalid_uuid(self, client: TestClient, auth_user: Any) -> None:
        """Test getting submission with invalid UUID"""
        user, token = auth_user
        response = client.get(
            "/api/v1/submissions/not-a-uuid", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422


class TestListSubmissions:
    """Tests for GET /api/v1/submissions (list with pagination)"""

    @pytest.mark.asyncio
    async def test_list_submissions_empty(
        self, client: TestClient, db_session: AsyncSession, auth_user: Any
    ) -> None:
        """Test listing submissions when none exist"""
        user, token = auth_user
        response = client.get("/api/v1/submissions", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 50
        assert data["total_pages"] == 0

    @pytest.mark.asyncio
    async def test_list_submissions_with_data(
        self, client: TestClient, db_session: AsyncSession, auth_user: Any
    ) -> None:
        """Test listing submissions with data (submitter sees only their own)"""
        user, token = auth_user

        # Create multiple submissions for authenticated user
        for i in range(3):
            submission = Submission(
                user_id=user.id,
                content=f"Test submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)
        await db_session.commit()

        response = client.get("/api/v1/submissions", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["total_pages"] == 1

    @pytest.mark.asyncio
    async def test_list_submissions_pagination(
        self, client: TestClient, db_session: AsyncSession, auth_user: Any
    ) -> None:
        """Test pagination of submissions list"""
        user, token = auth_user

        # Create 25 submissions for authenticated user
        for i in range(25):
            submission = Submission(
                user_id=user.id,
                content=f"Test submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)
        await db_session.commit()

        # Get first page (10 items)
        response = client.get(
            "/api/v1/submissions?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total_pages"] == 3

        # Get second page
        response = client.get(
            "/api/v1/submissions?page=2&page_size=10", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2

    def test_list_submissions_invalid_page(self, client: TestClient, auth_user: Any) -> None:
        """Test listing with invalid page parameter"""
        user, token = auth_user
        response = client.get(
            "/api/v1/submissions?page=0", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422

    def test_list_submissions_invalid_page_size(self, client: TestClient, auth_user: Any) -> None:
        """Test listing with invalid page_size parameter"""
        user, token = auth_user
        response = client.get(
            "/api/v1/submissions?page_size=101",  # Max is 100
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422


class TestSubmissionWithAuthentication:
    """Tests for authenticated submission endpoints (Phase 3)"""

    @pytest.mark.asyncio
    async def test_create_submission_requires_auth(self, client: TestClient) -> None:
        """Test that creating submission requires authentication"""
        payload = {"content": "Is climate change real?", "type": "text"}

        # Try without auth token
        response = client.post("/api/v1/submissions", json=payload)

        assert response.status_code == 401  # Unauthorized without auth

    @pytest.mark.asyncio
    async def test_create_submission_with_authenticated_user(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test creating submission with authenticated user"""
        # Create a user
        user = User(
            email="testuser@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create access token
        token = create_access_token(data={"sub": str(user.id)})

        # Create submission with auth
        payload = {"content": "Is climate change real?", "type": "text"}
        response = client.post(
            "/api/v1/submissions",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["user_id"] == str(user.id)
        assert data["content"] == "Is climate change real?"
        assert data["status"] == "processing"  # Should be processing after claim extraction

    @pytest.mark.asyncio
    async def test_create_submission_extracts_claims(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that submission extracts claims automatically"""
        # Create a user
        user = User(
            email="testuser@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create access token
        token = create_access_token(data={"sub": str(user.id)})

        # Create submission with multiple claims
        payload = {
            "content": "The earth is flat. Vaccines cause autism. Climate change is a hoax.",
            "type": "text",
        }
        response = client.post(
            "/api/v1/submissions",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert "claims" in data
        assert "extracted_claims_count" in data
        assert data["extracted_claims_count"] > 0
        assert len(data["claims"]) == data["extracted_claims_count"]

        # Verify claim structure
        if data["claims"]:
            claim = data["claims"][0]
            assert "id" in claim
            assert "content" in claim
            assert "created_at" in claim

    @pytest.mark.asyncio
    async def test_create_submission_with_invalid_token(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that invalid token is rejected"""
        payload = {"content": "Is climate change real?", "type": "text"}
        response = client.post(
            "/api/v1/submissions",
            json=payload,
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == 401  # Unauthorized

    @pytest.mark.asyncio
    async def test_get_submission_only_owner_or_admin(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that only owner or admin can view submission"""
        # Create two users
        owner = User(
            email="owner@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        other_user = User(
            email="other@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        admin_user = User(
            email="admin@example.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(owner)
        db_session.add(other_user)
        db_session.add(admin_user)
        await db_session.commit()
        await db_session.refresh(owner)
        await db_session.refresh(other_user)
        await db_session.refresh(admin_user)

        # Create submission as owner
        submission = Submission(
            user_id=owner.id,
            content="Test claim content",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Owner can view their own submission
        owner_token = create_access_token(data={"sub": str(owner.id)})
        response = client.get(
            f"/api/v1/submissions/{submission.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200

        # Other user cannot view
        other_token = create_access_token(data={"sub": str(other_user.id)})
        response = client.get(
            f"/api/v1/submissions/{submission.id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert response.status_code == 403  # Forbidden

        # Admin can view any submission
        admin_token = create_access_token(data={"sub": str(admin_user.id)})
        response = client.get(
            f"/api/v1/submissions/{submission.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_submissions_role_based_filtering(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that submitters only see their own submissions, admins see all"""
        # Create two submitters and one admin
        submitter1 = User(
            email="submitter1@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        submitter2 = User(
            email="submitter2@example.com",
            password_hash="hashed_password",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        admin = User(
            email="admin@example.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add_all([submitter1, submitter2, admin])
        await db_session.commit()
        await db_session.refresh(submitter1)
        await db_session.refresh(submitter2)
        await db_session.refresh(admin)

        # Create submissions for both submitters
        for i in range(3):
            submission1 = Submission(
                user_id=submitter1.id,
                content=f"Submitter 1 submission {i}",
                submission_type="text",
                status="pending",
            )
            submission2 = Submission(
                user_id=submitter2.id,
                content=f"Submitter 2 submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission1)
            db_session.add(submission2)
        await db_session.commit()

        # Submitter 1 sees only their own 3 submissions
        token1 = create_access_token(data={"sub": str(submitter1.id)})
        response1 = client.get("/api/v1/submissions", headers={"Authorization": f"Bearer {token1}"})
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["total"] == 3
        assert len(data1["items"]) == 3

        # Submitter 2 sees only their own 3 submissions
        token2 = create_access_token(data={"sub": str(submitter2.id)})
        response2 = client.get("/api/v1/submissions", headers={"Authorization": f"Bearer {token2}"})
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["total"] == 3
        assert len(data2["items"]) == 3

        # Admin sees all 6 submissions
        admin_token = create_access_token(data={"sub": str(admin.id)})
        admin_response = client.get(
            "/api/v1/submissions", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_response.status_code == 200
        admin_data = admin_response.json()
        assert admin_data["total"] == 6
        assert len(admin_data["items"]) == 6
