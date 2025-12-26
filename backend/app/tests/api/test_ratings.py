"""
Tests for Rating API Endpoints - TDD Approach (Tests written FIRST)

Issue #60: Backend: Rating & Workflow API Endpoints (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- POST /api/v1/ratings/seed - Seed rating definitions (admin-only)
- GET /api/v1/ratings/definitions - Get all rating definitions (public)
- POST /api/v1/fact-checks/{id}/rating - Assign rating (admin-only, versioned)
- GET /api/v1/fact-checks/{id}/ratings - Get rating history (public)
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.fact_check import FactCheck
from app.models.fact_check_rating import FactCheckRating
from app.models.rating_definition import RatingDefinition
from app.models.submission import Submission
from app.models.user import User, UserRole


class TestSeedRatingDefinitions:
    """Tests for POST /api/v1/ratings/seed - Admin only."""

    @pytest.mark.asyncio
    async def test_seed_definitions_as_admin_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test seeding rating definitions as admin succeeds."""
        # Arrange: Create admin user
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

        # Act
        response = client.post(
            "/api/v1/ratings/seed",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "seeded" in data["message"].lower() or "created" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_seed_definitions_as_super_admin_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test seeding rating definitions as super admin succeeds."""
        # Arrange
        super_admin = User(
            email="superadmin@example.com",
            password_hash="hashed",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        db_session.add(super_admin)
        await db_session.commit()
        await db_session.refresh(super_admin)

        token = create_access_token(data={"sub": str(super_admin.id)})

        # Act
        response = client.post(
            "/api/v1/ratings/seed",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_seed_definitions_as_reviewer_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test reviewer cannot seed rating definitions (403)."""
        # Arrange
        reviewer = User(
            email="reviewer@example.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        token = create_access_token(data={"sub": str(reviewer.id)})

        # Act
        response = client.post(
            "/api/v1/ratings/seed",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_seed_definitions_requires_auth(self, client: TestClient) -> None:
        """Test seeding rating definitions requires authentication."""
        # Act: No auth header
        response = client.post("/api/v1/ratings/seed")

        # Assert
        assert response.status_code == 401


class TestGetRatingDefinitions:
    """Tests for GET /api/v1/ratings/definitions - Public endpoint."""

    @pytest.mark.asyncio
    async def test_get_definitions_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test retrieving rating definitions (public access)."""
        # Arrange: Create rating definitions
        definitions = [
            RatingDefinition(
                rating_key="TRUE",
                title={"en": "True", "nl": "Waar"},
                description={"en": "Completely accurate", "nl": "Volledig juist"},
                visual_color="#00AA00",
                icon_name="check-circle",
                display_order=1,
            ),
            RatingDefinition(
                rating_key="FALSE",
                title={"en": "False", "nl": "Onwaar"},
                description={"en": "Completely inaccurate", "nl": "Volledig onjuist"},
                visual_color="#FF0000",
                icon_name="x-circle",
                display_order=2,
            ),
        ]
        for defn in definitions:
            db_session.add(defn)
        await db_session.commit()

        # Act: No auth required
        response = client.get("/api/v1/ratings/definitions")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["rating_key"] == "TRUE"
        assert data[0]["title"]["en"] == "True"
        assert data[1]["rating_key"] == "FALSE"

    @pytest.mark.asyncio
    async def test_get_definitions_empty(self, client: TestClient) -> None:
        """Test retrieving rating definitions when none exist."""
        # Act
        response = client.get("/api/v1/ratings/definitions")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestAssignRating:
    """Tests for POST /api/v1/fact-checks/{id}/rating - Admin only."""

    @pytest.mark.asyncio
    async def test_assign_rating_as_admin_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test assigning rating as admin creates versioned rating."""
        # Arrange: Create admin user
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        # Create submission and fact-check
        submission = Submission(
            content="Test claim content",
            source_url="https://example.com",
            workflow_state="in_research",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        fact_check = FactCheck(
            submission_id=submission.id,
            title="Test Fact Check",
            summary="Test summary content here",
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        payload = {
            "rating": "false",
            "justification": "This claim is completely false based on evidence from multiple sources.",
        }
        response = client.post(
            f"/api/v1/fact-checks/{fact_check.id}/rating",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == "false"
        assert data["version"] == 1
        assert data["is_current"] is True
        assert "id" in data
        assert "assigned_at" in data

    @pytest.mark.asyncio
    async def test_assign_rating_creates_new_version(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test assigning a second rating increments version."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)

        submission = Submission(
            content="Test claim for versioning",
            source_url="https://example.com",
            workflow_state="in_research",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        fact_check = FactCheck(
            submission_id=submission.id,
            title="Test Versioning",
            summary="Test summary",
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(fact_check)

        # Create first rating directly
        first_rating = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=admin.id,
            rating="partly_false",
            justification="Initial rating justification that is long enough to pass validation.",
            version=1,
            is_current=True,
        )
        db_session.add(first_rating)
        await db_session.commit()

        token = create_access_token(data={"sub": str(admin.id)})

        # Act: Assign second rating
        payload = {
            "rating": "false",
            "justification": "Updated rating after more evidence was found and reviewed carefully.",
        }
        response = client.post(
            f"/api/v1/fact-checks/{fact_check.id}/rating",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["version"] == 2
        assert data["is_current"] is True
        assert data["rating"] == "false"

    @pytest.mark.asyncio
    async def test_assign_rating_as_reviewer_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test reviewer cannot assign ratings (403)."""
        # Arrange
        reviewer = User(
            email="reviewer@example.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(reviewer)

        submission = Submission(
            content="Test claim",
            source_url="https://example.com",
            workflow_state="in_research",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        fact_check = FactCheck(
            submission_id=submission.id,
            title="Test",
            summary="Test summary",
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(reviewer)
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(reviewer.id)})

        # Act
        payload = {
            "rating": "true",
            "justification": "This is a valid justification that is long enough for the test.",
        }
        response = client.post(
            f"/api/v1/fact-checks/{fact_check.id}/rating",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_assign_rating_fact_check_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test assigning rating to non-existent fact-check returns 404."""
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

        # Act
        fake_id = uuid4()
        payload = {
            "rating": "true",
            "justification": "This justification is long enough for the validation requirements.",
        }
        response = client.post(
            f"/api/v1/fact-checks/{fake_id}/rating",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_rating_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test assigning rating requires authentication."""
        fake_id = uuid4()
        payload = {
            "rating": "true",
            "justification": "This justification is long enough for the validation requirements.",
        }
        response = client.post(
            f"/api/v1/fact-checks/{fake_id}/rating",
            json=payload,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_assign_rating_invalid_justification(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test assigning rating with short justification returns 422."""
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
            workflow_state="in_research",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        fact_check = FactCheck(
            submission_id=submission.id,
            title="Test",
            summary="Test summary",
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act: Short justification (less than 50 chars)
        payload = {
            "rating": "true",
            "justification": "Too short",
        }
        response = client.post(
            f"/api/v1/fact-checks/{fact_check.id}/rating",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 422


class TestGetRatingHistory:
    """Tests for GET /api/v1/fact-checks/{id}/ratings - Public endpoint."""

    @pytest.mark.asyncio
    async def test_get_rating_history_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test retrieving rating history for a fact-check."""
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
            workflow_state="published",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        fact_check = FactCheck(
            submission_id=submission.id,
            title="Test History",
            summary="Test summary",
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(fact_check)

        # Create ratings
        rating1 = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=admin.id,
            rating="partly_false",
            justification="Initial rating with adequate justification length for the test.",
            version=1,
            is_current=False,
        )
        rating2 = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=admin.id,
            rating="false",
            justification="Updated rating after more evidence was found and analyzed.",
            version=2,
            is_current=True,
        )
        db_session.add(rating1)
        db_session.add(rating2)
        await db_session.commit()

        # Act: No auth required for reading
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/ratings")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["fact_check_id"] == str(fact_check.id)
        assert data["total_versions"] == 2
        assert len(data["ratings"]) == 2
        assert data["ratings"][0]["version"] == 1
        assert data["ratings"][1]["version"] == 2

    @pytest.mark.asyncio
    async def test_get_rating_history_empty(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test retrieving rating history when no ratings exist."""
        # Arrange
        submission = Submission(
            content="Test claim",
            source_url="https://example.com",
            workflow_state="in_research",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        fact_check = FactCheck(
            submission_id=submission.id,
            title="Unrated",
            summary="Test summary",
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Act
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/ratings")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_versions"] == 0
        assert data["ratings"] == []

    @pytest.mark.asyncio
    async def test_get_rating_history_not_found(self, client: TestClient) -> None:
        """Test retrieving rating history for non-existent fact-check."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/fact-checks/{fake_id}/ratings")
        assert response.status_code == 404
