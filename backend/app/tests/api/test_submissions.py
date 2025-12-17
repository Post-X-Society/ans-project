"""
Tests for Submissions API - TDD Approach (Tests written FIRST)
"""

import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.submission import Submission


class TestCreateSubmission:
    """Tests for POST /api/v1/submissions"""

    def test_create_submission_success(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test creating a submission successfully"""
        payload = {"content": "Is climate change real?", "type": "text"}

        response = client.post("/api/v1/submissions", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert UUID(data["id"])  # Valid UUID
        assert data["content"] == "Is climate change real?"
        assert data["submission_type"] == "text"
        assert data["status"] == "pending"
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_submission_content_too_short(self, client: TestClient) -> None:
        """Test creating submission with content too short"""
        payload = {"content": "Short", "type": "text"}  # Less than 10 chars

        response = client.post("/api/v1/submissions", json=payload)

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_create_submission_content_empty(self, client: TestClient) -> None:
        """Test creating submission with empty content"""
        payload = {"content": "          ", "type": "text"}  # Only whitespace

        response = client.post("/api/v1/submissions", json=payload)

        assert response.status_code == 422

    def test_create_submission_invalid_type(self, client: TestClient) -> None:
        """Test creating submission with invalid type"""
        payload = {"content": "Valid content here", "type": "invalid"}

        response = client.post("/api/v1/submissions", json=payload)

        assert response.status_code == 422

    def test_create_submission_missing_fields(self, client: TestClient) -> None:
        """Test creating submission with missing required fields"""
        payload = {"content": "Missing type field"}

        response = client.post("/api/v1/submissions", json=payload)

        assert response.status_code == 422


class TestGetSubmission:
    """Tests for GET /api/v1/submissions/{id}"""

    @pytest.mark.asyncio
    async def test_get_submission_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting a submission by ID"""
        # Create a user first
        user = User(email="test@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

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
        response = client.get(f"/api/v1/submissions/{submission.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(submission.id)
        assert data["content"] == "Test claim content"
        assert data["submission_type"] == "text"
        assert data["status"] == "pending"

    def test_get_submission_not_found(self, client: TestClient) -> None:
        """Test getting non-existent submission"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.get(f"/api/v1/submissions/{fake_uuid}")

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_get_submission_invalid_uuid(self, client: TestClient) -> None:
        """Test getting submission with invalid UUID"""
        response = client.get("/api/v1/submissions/not-a-uuid")

        assert response.status_code == 422


class TestListSubmissions:
    """Tests for GET /api/v1/submissions (list with pagination)"""

    @pytest.mark.asyncio
    async def test_list_submissions_empty(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test listing submissions when none exist"""
        response = client.get("/api/v1/submissions")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 50
        assert data["total_pages"] == 0

    @pytest.mark.asyncio
    async def test_list_submissions_with_data(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test listing submissions with data"""
        # Create a user
        user = User(email="test@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create multiple submissions
        for i in range(3):
            submission = Submission(
                user_id=user.id,
                content=f"Test submission {i}",
                submission_type="text",
                status="pending",
            )
            db_session.add(submission)
        await db_session.commit()

        response = client.get("/api/v1/submissions")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["total_pages"] == 1

    @pytest.mark.asyncio
    async def test_list_submissions_pagination(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test pagination of submissions list"""
        # Create a user
        user = User(email="test@example.com", password_hash="hash", role=UserRole.SUBMITTER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create 25 submissions
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
        response = client.get("/api/v1/submissions?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total_pages"] == 3

        # Get second page
        response = client.get("/api/v1/submissions?page=2&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2

    def test_list_submissions_invalid_page(self, client: TestClient) -> None:
        """Test listing with invalid page parameter"""
        response = client.get("/api/v1/submissions?page=0")

        assert response.status_code == 422

    def test_list_submissions_invalid_page_size(self, client: TestClient) -> None:
        """Test listing with invalid page_size parameter"""
        response = client.get("/api/v1/submissions?page_size=101")  # Max is 100

        assert response.status_code == 422
