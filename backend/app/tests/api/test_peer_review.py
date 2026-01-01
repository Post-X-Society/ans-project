"""
Tests for Peer Review API Endpoints - TDD Approach (Tests written FIRST)

Issue #66: Backend: Peer Review API Endpoints (TDD)
EPIC #48: Multi-Tier Approval & Peer Review
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- POST /api/v1/peer-review/{fact_check_id}/initiate - Start peer review process
- POST /api/v1/peer-review/{fact_check_id}/submit - Submit review decision
- GET /api/v1/peer-review/{fact_check_id}/status - Get review status/consensus
- GET /api/v1/peer-review/pending - Get current user's pending reviews
- PATCH /api/v1/peer-review/triggers - Update trigger configuration (admin only)
"""

from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.claim import Claim
from app.models.fact_check import FactCheck
from app.models.peer_review import ApprovalStatus, PeerReview
from app.models.peer_review_trigger import PeerReviewTrigger, TriggerType
from app.models.user import User, UserRole

# =============================================================================
# Helper functions
# =============================================================================


async def create_test_fact_check(db_session: AsyncSession) -> FactCheck:
    """Create a claim and fact_check for testing."""
    claim = Claim(
        content="Test claim for peer review API testing",
        source="user_submission",
    )
    db_session.add(claim)
    await db_session.flush()

    fact_check = FactCheck(
        claim_id=claim.id,
        verdict="true",
        confidence=0.9,
        reasoning="Test reasoning for peer review",
        sources=["https://example.com"],
    )
    db_session.add(fact_check)
    await db_session.commit()
    await db_session.refresh(fact_check)

    return fact_check


async def create_test_user(
    db_session: AsyncSession,
    role: UserRole = UserRole.ADMIN,
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
# Test: Initiate Peer Review
# POST /api/v1/peer-review/{fact_check_id}/initiate
# =============================================================================


class TestInitiatePeerReview:
    """Tests for POST /api/v1/peer-review/{fact_check_id}/initiate"""

    @pytest.mark.asyncio
    async def test_initiate_peer_review_as_admin_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test initiating peer review as admin succeeds."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        admin, admin_token = await create_test_user(
            db_session, role=UserRole.ADMIN, email="admin@test.com"
        )
        reviewer1, _ = await create_test_user(
            db_session, role=UserRole.ADMIN, email="reviewer1@test.com"
        )
        reviewer2, _ = await create_test_user(
            db_session, role=UserRole.ADMIN, email="reviewer2@test.com"
        )

        payload: dict[str, Any] = {"reviewer_ids": [str(reviewer1.id), str(reviewer2.id)]}

        # Act
        response = client.post(
            f"/api/v1/peer-review/{fact_check.id}/initiate",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["fact_check_id"] == str(fact_check.id)
        assert data["reviews_created"] == 2
        assert len(data["reviews"]) == 2

    @pytest.mark.asyncio
    async def test_initiate_peer_review_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that initiating peer review requires authentication."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        payload: dict[str, Any] = {"reviewer_ids": [str(uuid4())]}

        # Act - no auth header
        response = client.post(
            f"/api/v1/peer-review/{fact_check.id}/initiate",
            json=payload,
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_initiate_peer_review_as_submitter_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that submitter cannot initiate peer review."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, submitter_token = await create_test_user(db_session, role=UserRole.SUBMITTER)

        payload: dict[str, Any] = {"reviewer_ids": [str(uuid4())]}

        # Act
        response = client.post(
            f"/api/v1/peer-review/{fact_check.id}/initiate",
            json=payload,
            headers={"Authorization": f"Bearer {submitter_token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_initiate_peer_review_as_reviewer_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that reviewer cannot initiate peer review (admin+ required)."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, reviewer_token = await create_test_user(db_session, role=UserRole.REVIEWER)

        payload: dict[str, Any] = {"reviewer_ids": [str(uuid4())]}

        # Act
        response = client.post(
            f"/api/v1/peer-review/{fact_check.id}/initiate",
            json=payload,
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_initiate_peer_review_fact_check_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test initiating peer review for non-existent fact-check returns 404."""
        # Arrange
        _, admin_token = await create_test_user(db_session, role=UserRole.ADMIN)
        fake_id = uuid4()

        payload: dict[str, Any] = {"reviewer_ids": [str(uuid4())]}

        # Act
        response = client.post(
            f"/api/v1/peer-review/{fake_id}/initiate",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_initiate_peer_review_empty_reviewer_list(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test initiating peer review with empty reviewer list returns 422."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, admin_token = await create_test_user(db_session, role=UserRole.ADMIN)

        payload: dict[str, Any] = {"reviewer_ids": []}

        # Act
        response = client.post(
            f"/api/v1/peer-review/{fact_check.id}/initiate",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert - FastAPI/Pydantic returns 422 for validation errors
        assert response.status_code == 422


# =============================================================================
# Test: Submit Peer Review
# POST /api/v1/peer-review/{fact_check_id}/submit
# =============================================================================


class TestSubmitPeerReview:
    """Tests for POST /api/v1/peer-review/{fact_check_id}/submit"""

    @pytest.mark.asyncio
    async def test_submit_peer_review_approve_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test submitting an approval decision succeeds."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        reviewer, reviewer_token = await create_test_user(db_session, role=UserRole.ADMIN)

        # Create pending review assignment
        review = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer.id,
            approval_status=ApprovalStatus.PENDING,
        )
        db_session.add(review)
        await db_session.commit()

        payload: dict[str, Any] = {"approved": True, "comments": "LGTM - well researched"}

        # Act
        response = client.post(
            f"/api/v1/peer-review/{fact_check.id}/submit",
            json=payload,
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"
        assert data["comments"] == "LGTM - well researched"

    @pytest.mark.asyncio
    async def test_submit_peer_review_reject_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test submitting a rejection decision succeeds."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        reviewer, reviewer_token = await create_test_user(db_session, role=UserRole.ADMIN)

        # Create pending review assignment
        review = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer.id,
            approval_status=ApprovalStatus.PENDING,
        )
        db_session.add(review)
        await db_session.commit()

        payload: dict[str, Any] = {"approved": False, "comments": "Needs more sources"}

        # Act
        response = client.post(
            f"/api/v1/peer-review/{fact_check.id}/submit",
            json=payload,
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "rejected"
        assert data["comments"] == "Needs more sources"

    @pytest.mark.asyncio
    async def test_submit_peer_review_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that submitting peer review requires authentication."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        payload: dict[str, Any] = {"approved": True}

        # Act - no auth header
        response = client.post(
            f"/api/v1/peer-review/{fact_check.id}/submit",
            json=payload,
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_submit_peer_review_as_submitter_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that submitter cannot submit peer review."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, submitter_token = await create_test_user(db_session, role=UserRole.SUBMITTER)

        payload: dict[str, Any] = {"approved": True}

        # Act
        response = client.post(
            f"/api/v1/peer-review/{fact_check.id}/submit",
            json=payload,
            headers={"Authorization": f"Bearer {submitter_token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_submit_peer_review_fact_check_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test submitting review for non-existent fact-check returns 404."""
        # Arrange
        _, admin_token = await create_test_user(db_session, role=UserRole.ADMIN)
        fake_id = uuid4()

        payload: dict[str, Any] = {"approved": True}

        # Act
        response = client.post(
            f"/api/v1/peer-review/{fake_id}/submit",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 404


# =============================================================================
# Test: Get Peer Review Status
# GET /api/v1/peer-review/{fact_check_id}/status
# =============================================================================


class TestGetPeerReviewStatus:
    """Tests for GET /api/v1/peer-review/{fact_check_id}/status"""

    @pytest.mark.asyncio
    async def test_get_status_with_pending_reviews(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting status when reviews are still pending."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        reviewer1, _ = await create_test_user(db_session, role=UserRole.ADMIN, email="r1@test.com")
        reviewer2, _ = await create_test_user(db_session, role=UserRole.ADMIN, email="r2@test.com")
        _, admin_token = await create_test_user(
            db_session, role=UserRole.ADMIN, email="admin@test.com"
        )

        # Create pending reviews
        for reviewer_id in [reviewer1.id, reviewer2.id]:
            review = PeerReview(
                fact_check_id=fact_check.id,
                reviewer_id=reviewer_id,
                approval_status=ApprovalStatus.PENDING,
            )
            db_session.add(review)
        await db_session.commit()

        # Act
        response = client.get(
            f"/api/v1/peer-review/{fact_check.id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["fact_check_id"] == str(fact_check.id)
        assert data["consensus_reached"] is False
        assert data["total_reviews"] == 2
        assert data["pending_count"] == 2
        assert data["approved_count"] == 0
        assert data["rejected_count"] == 0

    @pytest.mark.asyncio
    async def test_get_status_with_consensus_approved(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting status when all reviews are approved."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        reviewer1, _ = await create_test_user(db_session, role=UserRole.ADMIN, email="r1@test.com")
        reviewer2, _ = await create_test_user(db_session, role=UserRole.ADMIN, email="r2@test.com")
        _, admin_token = await create_test_user(
            db_session, role=UserRole.ADMIN, email="admin@test.com"
        )

        # Create approved reviews
        for reviewer_id in [reviewer1.id, reviewer2.id]:
            review = PeerReview(
                fact_check_id=fact_check.id,
                reviewer_id=reviewer_id,
                approval_status=ApprovalStatus.APPROVED,
            )
            db_session.add(review)
        await db_session.commit()

        # Act
        response = client.get(
            f"/api/v1/peer-review/{fact_check.id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["consensus_reached"] is True
        assert data["approved"] is True
        assert data["approved_count"] == 2
        assert data["rejected_count"] == 0
        assert data["pending_count"] == 0

    @pytest.mark.asyncio
    async def test_get_status_with_rejection(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting status when at least one review is rejected."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        reviewer1, _ = await create_test_user(db_session, role=UserRole.ADMIN, email="r1@test.com")
        reviewer2, _ = await create_test_user(db_session, role=UserRole.ADMIN, email="r2@test.com")
        _, admin_token = await create_test_user(
            db_session, role=UserRole.ADMIN, email="admin@test.com"
        )

        # Create mixed reviews (1 approved, 1 rejected)
        review1 = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer1.id,
            approval_status=ApprovalStatus.APPROVED,
        )
        review2 = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer2.id,
            approval_status=ApprovalStatus.REJECTED,
            comments="Needs improvement",
        )
        db_session.add_all([review1, review2])
        await db_session.commit()

        # Act
        response = client.get(
            f"/api/v1/peer-review/{fact_check.id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["consensus_reached"] is True  # All have decided
        assert data["approved"] is False  # Not unanimous approval
        assert data["approved_count"] == 1
        assert data["rejected_count"] == 1

    @pytest.mark.asyncio
    async def test_get_status_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that getting status requires authentication."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)

        # Act - no auth header
        response = client.get(
            f"/api/v1/peer-review/{fact_check.id}/status",
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_status_as_reviewer_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that reviewer can get review status."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        _, reviewer_token = await create_test_user(db_session, role=UserRole.REVIEWER)

        # Act
        response = client.get(
            f"/api/v1/peer-review/{fact_check.id}/status",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        # Assert
        assert response.status_code == 200


# =============================================================================
# Test: Get Pending Reviews
# GET /api/v1/peer-review/pending
# =============================================================================


class TestGetPendingReviews:
    """Tests for GET /api/v1/peer-review/pending"""

    @pytest.mark.asyncio
    async def test_get_pending_reviews_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting current user's pending reviews."""
        # Arrange
        fact_check1 = await create_test_fact_check(db_session)
        fact_check2 = await create_test_fact_check(db_session)
        reviewer, reviewer_token = await create_test_user(db_session, role=UserRole.ADMIN)

        # Create pending reviews for this reviewer
        for fc in [fact_check1, fact_check2]:
            review = PeerReview(
                fact_check_id=fc.id,
                reviewer_id=reviewer.id,
                approval_status=ApprovalStatus.PENDING,
            )
            db_session.add(review)
        await db_session.commit()

        # Act
        response = client.get(
            "/api/v1/peer-review/pending",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["reviews"]) == 2

    @pytest.mark.asyncio
    async def test_get_pending_reviews_empty(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting pending reviews when none exist."""
        # Arrange
        _, reviewer_token = await create_test_user(db_session, role=UserRole.ADMIN)

        # Act
        response = client.get(
            "/api/v1/peer-review/pending",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["reviews"] == []

    @pytest.mark.asyncio
    async def test_get_pending_reviews_excludes_completed(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that completed reviews are not included in pending list."""
        # Arrange
        fact_check = await create_test_fact_check(db_session)
        reviewer, reviewer_token = await create_test_user(db_session, role=UserRole.ADMIN)

        # Create an approved (not pending) review
        review = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer.id,
            approval_status=ApprovalStatus.APPROVED,
        )
        db_session.add(review)
        await db_session.commit()

        # Act
        response = client.get(
            "/api/v1/peer-review/pending",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0

    @pytest.mark.asyncio
    async def test_get_pending_reviews_requires_auth(self, client: TestClient) -> None:
        """Test that getting pending reviews requires authentication."""
        # Act - no auth header
        response = client.get("/api/v1/peer-review/pending")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_pending_reviews_as_submitter_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that submitter cannot access pending reviews."""
        # Arrange
        _, submitter_token = await create_test_user(db_session, role=UserRole.SUBMITTER)

        # Act
        response = client.get(
            "/api/v1/peer-review/pending",
            headers={"Authorization": f"Bearer {submitter_token}"},
        )

        # Assert
        assert response.status_code == 403


# =============================================================================
# Test: Update Peer Review Triggers
# PATCH /api/v1/peer-review/triggers
# =============================================================================


class TestUpdatePeerReviewTriggers:
    """Tests for PATCH /api/v1/peer-review/triggers"""

    @pytest.mark.asyncio
    async def test_update_trigger_as_admin_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test updating trigger configuration as admin succeeds."""
        # Arrange
        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.ENGAGEMENT_THRESHOLD,
            enabled=True,
            threshold_value={"min_views": 10000},
            description="Engagement trigger",
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)

        _, admin_token = await create_test_user(db_session, role=UserRole.ADMIN)

        payload: dict[str, Any] = {
            "trigger_id": str(trigger.id),
            "enabled": False,
            "threshold_value": {"min_views": 20000},
        }

        # Act
        response = client.patch(
            "/api/v1/peer-review/triggers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert data["threshold_value"]["min_views"] == 20000

    @pytest.mark.asyncio
    async def test_update_trigger_requires_admin(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that updating triggers requires admin role."""
        # Arrange
        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["election"]},
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)

        _, reviewer_token = await create_test_user(db_session, role=UserRole.REVIEWER)

        payload: dict[str, Any] = {"trigger_id": str(trigger.id), "enabled": False}

        # Act
        response = client.patch(
            "/api/v1/peer-review/triggers",
            json=payload,
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_trigger_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test updating non-existent trigger returns 404."""
        # Arrange
        _, admin_token = await create_test_user(db_session, role=UserRole.ADMIN)
        fake_id = uuid4()

        payload: dict[str, Any] = {"trigger_id": str(fake_id), "enabled": False}

        # Act
        response = client.patch(
            "/api/v1/peer-review/triggers",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_trigger_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that updating triggers requires authentication."""
        # Arrange
        trigger = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["election"]},
        )
        db_session.add(trigger)
        await db_session.commit()
        await db_session.refresh(trigger)

        payload: dict[str, Any] = {"trigger_id": str(trigger.id), "enabled": False}

        # Act - no auth header
        response = client.patch(
            "/api/v1/peer-review/triggers",
            json=payload,
        )

        # Assert
        assert response.status_code == 401


# =============================================================================
# Test: Get Peer Review Triggers
# GET /api/v1/peer-review/triggers
# =============================================================================


class TestGetPeerReviewTriggers:
    """Tests for GET /api/v1/peer-review/triggers"""

    @pytest.mark.asyncio
    async def test_get_triggers_as_admin_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting triggers as admin succeeds."""
        # Arrange
        trigger1 = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["election"]},
        )
        trigger2 = PeerReviewTrigger(
            trigger_type=TriggerType.ENGAGEMENT_THRESHOLD,
            enabled=False,
            threshold_value={"min_views": 10000},
        )
        db_session.add_all([trigger1, trigger2])
        await db_session.commit()

        _, admin_token = await create_test_user(db_session, role=UserRole.ADMIN)

        # Act
        response = client.get(
            "/api/v1/peer-review/triggers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["triggers"]) == 2

    @pytest.mark.asyncio
    async def test_get_triggers_filter_enabled(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test filtering triggers by enabled status."""
        # Arrange
        trigger1 = PeerReviewTrigger(
            trigger_type=TriggerType.POLITICAL_KEYWORD,
            enabled=True,
            threshold_value={"keywords": ["election"]},
        )
        trigger2 = PeerReviewTrigger(
            trigger_type=TriggerType.ENGAGEMENT_THRESHOLD,
            enabled=False,
            threshold_value={"min_views": 10000},
        )
        db_session.add_all([trigger1, trigger2])
        await db_session.commit()

        _, admin_token = await create_test_user(db_session, role=UserRole.ADMIN)

        # Act
        response = client.get(
            "/api/v1/peer-review/triggers",
            params={"enabled_only": True},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["triggers"][0]["enabled"] is True

    @pytest.mark.asyncio
    async def test_get_triggers_requires_admin(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that getting triggers requires admin role."""
        # Arrange
        _, reviewer_token = await create_test_user(db_session, role=UserRole.REVIEWER)

        # Act
        response = client.get(
            "/api/v1/peer-review/triggers",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )

        # Assert
        assert response.status_code == 403
