"""
Tests for Source API Endpoints - TDD Approach (Tests written FIRST)

Issue #70: Backend: Source Management Service (TDD)
EPIC #49: Evidence & Source Management
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- POST /api/v1/fact-checks/{id}/sources - Add source to fact-check
- GET /api/v1/fact-checks/{id}/sources - List sources for fact-check
- GET /api/v1/fact-checks/{id}/sources/citations - List sources with citations
- GET /api/v1/sources/{id} - Get single source
- PATCH /api/v1/sources/{id} - Update source
- DELETE /api/v1/sources/{id} - Delete source
- GET /api/v1/fact-checks/{id}/sources/validate - Validate minimum sources
- GET /api/v1/fact-checks/{id}/sources/credibility - Get credibility summary
"""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.claim import Claim
from app.models.fact_check import FactCheck
from app.models.source import Source, SourceType
from app.models.user import User, UserRole

# =============================================================================
# Helper functions
# =============================================================================


async def create_test_fact_check(db_session: AsyncSession) -> FactCheck:
    """Create a claim and fact_check for testing."""
    claim = Claim(
        content="Test claim content for API testing",
        source="user_submission",
    )
    db_session.add(claim)
    await db_session.flush()

    fact_check = FactCheck(
        claim_id=claim.id,
        verdict="true",
        confidence=0.9,
        reasoning="Test reasoning",
        sources=["https://example.com"],
    )
    db_session.add(fact_check)
    await db_session.commit()
    await db_session.refresh(fact_check)

    return fact_check


async def create_test_user(
    db_session: AsyncSession,
    role: UserRole = UserRole.REVIEWER,
    email: str | None = None,
) -> tuple[User, str]:
    """Create a test user and return user and JWT token."""
    user = User(
        email=email or f"testuser-{uuid4()}@example.com",
        password_hash="hashed_password",
        role=role,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return user, token


# =============================================================================
# Test: Add Source to Fact-Check
# =============================================================================


class TestAddSource:
    """Tests for POST /api/v1/fact-checks/{id}/sources"""

    @pytest.mark.asyncio
    async def test_add_source_as_reviewer_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test adding a source as reviewer succeeds."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, token = await create_test_user(db_session, role=UserRole.REVIEWER)

        payload = {
            "fact_check_id": str(fact_check.id),
            "source_type": "primary",
            "title": "Primary Evidence Source",
            "access_date": "2025-12-28",
        }

        # Act
        response = client.post(
            f"/api/v1/fact-checks/{fact_check.id}/sources",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Primary Evidence Source"
        assert data["source_type"] == "primary"
        assert "id" in data
        assert data["fact_check_id"] == str(fact_check.id)

    @pytest.mark.asyncio
    async def test_add_source_with_all_fields(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test adding a source with all optional fields."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, token = await create_test_user(db_session, role=UserRole.ADMIN)

        payload = {
            "fact_check_id": str(fact_check.id),
            "source_type": "academic",
            "title": "Academic Research Paper",
            "url": "https://academic.example.com/paper/123",
            "publication_date": "2025-06-15",
            "access_date": "2025-12-28",
            "credibility_score": 5,
            "relevance": "supports",
            "archived_url": "https://web.archive.org/example",
            "notes": "Peer-reviewed journal article.",
        }

        # Act
        response = client.post(
            f"/api/v1/fact-checks/{fact_check.id}/sources",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["source_type"] == "academic"
        assert data["credibility_score"] == 5
        assert data["relevance"] == "supports"
        assert data["url"] == "https://academic.example.com/paper/123"

    @pytest.mark.asyncio
    async def test_add_source_as_submitter_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that submitter cannot add sources (403)."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, token = await create_test_user(db_session, role=UserRole.SUBMITTER)

        payload = {
            "fact_check_id": str(fact_check.id),
            "source_type": "primary",
            "title": "Source",
            "access_date": "2025-12-28",
        }

        # Act
        response = client.post(
            f"/api/v1/fact-checks/{fact_check.id}/sources",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_add_source_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that adding a source requires authentication."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        payload = {
            "fact_check_id": str(fact_check.id),
            "source_type": "primary",
            "title": "Source",
            "access_date": "2025-12-28",
        }

        # Act - no auth header
        response = client.post(
            f"/api/v1/fact-checks/{fact_check.id}/sources",
            json=payload,
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_add_source_fact_check_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test adding source to non-existent fact-check returns 404."""
        # Arrange
        _, token = await create_test_user(db_session, role=UserRole.REVIEWER)
        fake_id = uuid4()

        payload = {
            "fact_check_id": str(fake_id),
            "source_type": "primary",
            "title": "Source",
            "access_date": "2025-12-28",
        }

        # Act
        response = client.post(
            f"/api/v1/fact-checks/{fake_id}/sources",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_source_path_body_mismatch(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that path fact_check_id must match body fact_check_id."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, token = await create_test_user(db_session, role=UserRole.REVIEWER)

        # Different fact_check_id in path vs body
        payload = {
            "fact_check_id": str(uuid4()),  # Different ID
            "source_type": "primary",
            "title": "Source",
            "access_date": "2025-12-28",
        }

        # Act
        response = client.post(
            f"/api/v1/fact-checks/{fact_check.id}/sources",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 400


# =============================================================================
# Test: List Sources
# =============================================================================


class TestListSources:
    """Tests for GET /api/v1/fact-checks/{id}/sources"""

    @pytest.mark.asyncio
    async def test_list_sources_success(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test listing sources for a fact-check (public access)."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        # Add sources directly
        for i, source_type in enumerate([SourceType.PRIMARY, SourceType.SECONDARY]):
            source = Source(
                fact_check_id=fact_check.id,
                source_type=source_type,
                title=f"Source {i + 1}",
                access_date=date(2025, 12, 28),
            )
            db_session.add(source)
        await db_session.commit()

        # Act - no auth required
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/sources")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["fact_check_id"] == str(fact_check.id)
        assert data["total_count"] == 2
        assert len(data["sources"]) == 2

    @pytest.mark.asyncio
    async def test_list_sources_empty(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test listing sources when none exist."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        # Act
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/sources")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["sources"] == []


# =============================================================================
# Test: List Sources with Citations
# =============================================================================


class TestListSourcesWithCitations:
    """Tests for GET /api/v1/fact-checks/{id}/sources/citations"""

    @pytest.mark.asyncio
    async def test_list_sources_with_citations(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test listing sources with citation numbers."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        for i in range(3):
            source = Source(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source {i + 1}",
                access_date=date(2025, 12, 28),
            )
            db_session.add(source)
        await db_session.commit()

        # Act
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/sources/citations")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3

        # Check citation numbers
        assert data["sources"][0]["citation_number"] == 1
        assert data["sources"][0]["citation_string"] == "[1]"
        assert data["sources"][1]["citation_number"] == 2
        assert data["sources"][1]["citation_string"] == "[2]"
        assert data["sources"][2]["citation_number"] == 3
        assert data["sources"][2]["citation_string"] == "[3]"


# =============================================================================
# Test: Get Single Source
# =============================================================================


class TestGetSingleSource:
    """Tests for GET /api/v1/sources/{id}"""

    @pytest.mark.asyncio
    async def test_get_source_success(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test getting a single source by ID."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        source = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.EXPERT,
            title="Expert Quote",
            access_date=date(2025, 12, 28),
            credibility_score=4,
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)

        # Act
        response = client.get(f"/api/v1/sources/{source.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(source.id)
        assert data["title"] == "Expert Quote"
        assert data["credibility_score"] == 4

    @pytest.mark.asyncio
    async def test_get_source_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent source returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/sources/{fake_id}")
        assert response.status_code == 404


# =============================================================================
# Test: Update Source
# =============================================================================


class TestUpdateSource:
    """Tests for PATCH /api/v1/sources/{id}"""

    @pytest.mark.asyncio
    async def test_update_source_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test updating a source as reviewer."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, token = await create_test_user(db_session, role=UserRole.REVIEWER)

        source = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.MEDIA,
            title="Original Title",
            access_date=date(2025, 12, 28),
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)

        # Act
        response = client.patch(
            f"/api/v1/sources/{source.id}",
            json={"title": "Updated Title", "credibility_score": 5},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["credibility_score"] == 5
        assert data["source_type"] == "media"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_source_as_submitter_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that submitter cannot update sources."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, token = await create_test_user(db_session, role=UserRole.SUBMITTER)

        source = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.MEDIA,
            title="Source",
            access_date=date(2025, 12, 28),
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)

        # Act
        response = client.patch(
            f"/api/v1/sources/{source.id}",
            json={"title": "Updated"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_source_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test updating a non-existent source returns 404."""
        # Arrange
        _, token = await create_test_user(db_session, role=UserRole.REVIEWER)

        # Act
        response = client.patch(
            f"/api/v1/sources/{uuid4()}",
            json={"title": "Updated"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 404


# =============================================================================
# Test: Delete Source
# =============================================================================


class TestDeleteSource:
    """Tests for DELETE /api/v1/sources/{id}"""

    @pytest.mark.asyncio
    async def test_delete_source_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test deleting a source as reviewer."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, token = await create_test_user(db_session, role=UserRole.REVIEWER)

        source = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Source to Delete",
            access_date=date(2025, 12, 28),
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)
        source_id = source.id

        # Act
        response = client.delete(
            f"/api/v1/sources/{source_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/v1/sources/{source_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_source_as_submitter_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that submitter cannot delete sources."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, token = await create_test_user(db_session, role=UserRole.SUBMITTER)

        source = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Source",
            access_date=date(2025, 12, 28),
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)

        # Act
        response = client.delete(
            f"/api/v1/sources/{source.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403


# =============================================================================
# Test: Validate Source Count
# =============================================================================


class TestValidateSources:
    """Tests for GET /api/v1/fact-checks/{id}/sources/validate"""

    @pytest.mark.asyncio
    async def test_validate_passes_with_two_sources(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test validation passes with 2+ sources."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        for i in range(2):
            source = Source(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source {i + 1}",
                access_date=date(2025, 12, 28),
            )
            db_session.add(source)
        await db_session.commit()

        # Act
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/sources/validate")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["source_count"] == 2
        assert data["minimum_required"] == 2

    @pytest.mark.asyncio
    async def test_validate_fails_with_one_source(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test validation fails with only 1 source."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        source = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Only Source",
            access_date=date(2025, 12, 28),
        )
        db_session.add(source)
        await db_session.commit()

        # Act
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/sources/validate")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["source_count"] == 1
        assert data["minimum_required"] == 2

    @pytest.mark.asyncio
    async def test_validate_fails_with_no_sources(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test validation fails with no sources."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        # Act
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/sources/validate")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["source_count"] == 0


# =============================================================================
# Test: Credibility Summary
# =============================================================================


class TestCredibilitySummary:
    """Tests for GET /api/v1/fact-checks/{id}/sources/credibility"""

    @pytest.mark.asyncio
    async def test_get_credibility_summary(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting credibility summary."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        # Sources with scores: 3, 4, 5 -> average = 4.0
        for score in [3, 4, 5]:
            source = Source(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source score {score}",
                access_date=date(2025, 12, 28),
                credibility_score=score,
            )
            db_session.add(source)
        await db_session.commit()

        # Act
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/sources/credibility")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_sources"] == 3
        assert data["sources_with_scores"] == 3
        assert data["average_credibility"] == 4.0

    @pytest.mark.asyncio
    async def test_get_credibility_summary_mixed_scores(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test credibility summary with some sources missing scores."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        # Source with score 5
        source1 = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Source with score",
            access_date=date(2025, 12, 28),
            credibility_score=5,
        )
        db_session.add(source1)

        # Source without score
        source2 = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.SECONDARY,
            title="Source without score",
            access_date=date(2025, 12, 28),
        )
        db_session.add(source2)
        await db_session.commit()

        # Act
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/sources/credibility")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_sources"] == 2
        assert data["sources_with_scores"] == 1
        assert data["average_credibility"] == 5.0

    @pytest.mark.asyncio
    async def test_get_credibility_summary_no_scores(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test credibility summary when no sources have scores."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        source = Source(
            fact_check_id=fact_check.id,
            source_type=SourceType.PRIMARY,
            title="Source without score",
            access_date=date(2025, 12, 28),
        )
        db_session.add(source)
        await db_session.commit()

        # Act
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/sources/credibility")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_sources"] == 1
        assert data["sources_with_scores"] == 0
        assert data["average_credibility"] is None


# =============================================================================
# Test: High Credibility Sources
# =============================================================================


class TestHighCredibilitySources:
    """Tests for GET /api/v1/fact-checks/{id}/sources/high-credibility"""

    @pytest.mark.asyncio
    async def test_get_high_credibility_sources(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting sources with high credibility scores."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        for score in [1, 2, 3, 4, 5]:
            source = Source(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source score {score}",
                access_date=date(2025, 12, 28),
                credibility_score=score,
            )
            db_session.add(source)
        await db_session.commit()

        # Act - default min_score is 4
        response = client.get(f"/api/v1/fact-checks/{fact_check.id}/sources/high-credibility")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2  # Scores 4 and 5

    @pytest.mark.asyncio
    async def test_get_high_credibility_sources_custom_threshold(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting sources with custom credibility threshold."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        for score in [1, 2, 3, 4, 5]:
            source = Source(
                fact_check_id=fact_check.id,
                source_type=SourceType.PRIMARY,
                title=f"Source score {score}",
                access_date=date(2025, 12, 28),
                credibility_score=score,
            )
            db_session.add(source)
        await db_session.commit()

        # Act - min_score = 3
        response = client.get(
            f"/api/v1/fact-checks/{fact_check.id}/sources/high-credibility",
            params={"min_score": 3},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3  # Scores 3, 4, and 5
