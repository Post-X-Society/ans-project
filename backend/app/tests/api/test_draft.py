"""
Tests for Fact-Check Draft Storage API - TDD Approach (Tests written FIRST)

Issue #123: Backend: Fact-Check Draft Storage API (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- PATCH /api/v1/fact-checks/{id}/draft - Save/update draft content
- GET /api/v1/fact-checks/{id}/draft - Retrieve draft data

Authorization Rules:
- Assigned reviewers can save/view their own drafts
- Admins have override permissions
- Others receive 403 Forbidden

Editable States: assigned, in_research, draft_ready, needs_more_research
Locked States: published, rejected, archived
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.claim import Claim
from app.models.fact_check import FactCheck
from app.models.submission import Submission
from app.models.submission_reviewer import SubmissionReviewer
from app.models.user import User, UserRole
from app.models.workflow_transition import WorkflowState
from app.tests.helpers import normalize_dt


class TestSaveDraft:
    """Tests for PATCH /api/v1/fact-checks/{id}/draft - Save/update draft."""

    @pytest.mark.asyncio
    async def test_save_draft_as_assigned_reviewer_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test assigned reviewer can save draft on their assigned fact-check."""
        # Arrange: Create submitter, reviewer, submission, claim, fact-check
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        reviewer = User(
            email="reviewer@example.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(submitter)
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(submitter)
        await db_session.refresh(reviewer)

        # Create submission in editable state
        submission = Submission(
            user_id=submitter.id,
            content="Test content for fact-checking",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Create claim linked to submission
        claim = Claim(
            content="Test claim content",
            source="https://example.com",
        )
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        # Link claim to submission
        submission.claims.append(claim)
        await db_session.commit()

        # Create fact-check
        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending review",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Assign reviewer to submission
        assignment = SubmissionReviewer(
            submission_id=submission.id,
            reviewer_id=reviewer.id,
            assigned_by_id=submitter.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        token = create_access_token(data={"sub": str(reviewer.id)})

        # Act
        payload = {
            "claim_summary": "Summary of the claim being reviewed",
            "analysis": "<p>Initial analysis of the claim...</p>",
            "verdict": "partly_false",
            "justification": "This is a detailed justification that explains the verdict with enough characters.",
            "sources_cited": ["https://source1.com", "https://source2.com"],
            "internal_notes": "Note to self: check more sources",
        }
        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["fact_check_id"] == str(fact_check.id)
        assert data["has_draft"] is True
        assert data["draft_content"]["claim_summary"] == payload["claim_summary"]
        assert data["draft_content"]["verdict"] == payload["verdict"]
        assert data["draft_content"]["version"] == 1
        assert data["draft_content"]["last_edited_by"] == str(reviewer.id)
        assert data["draft_updated_at"] is not None

    @pytest.mark.asyncio
    async def test_save_draft_as_admin_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can save draft on any fact-check."""
        # Arrange: Create admin, submission, claim, fact-check
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(admin)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.ASSIGNED,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(
            content="Test claim for admin",
            source="https://example.com",
        )
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending review",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        payload = {
            "claim_summary": "Admin's draft summary",
            "analysis": "<p>Admin analysis</p>",
        }
        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["has_draft"] is True
        assert data["draft_content"]["claim_summary"] == "Admin's draft summary"

    @pytest.mark.asyncio
    async def test_save_draft_increments_version(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test saving draft multiple times increments version."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(admin)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Test claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act: Save draft first time
        response1 = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "First save"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response1.status_code == 200
        assert response1.json()["draft_content"]["version"] == 1

        # Save draft second time
        response2 = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Second save"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response2.status_code == 200
        assert response2.json()["draft_content"]["version"] == 2

    @pytest.mark.asyncio
    async def test_save_draft_unassigned_reviewer_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test unassigned reviewer cannot save draft (403)."""
        # Arrange: Create reviewer NOT assigned to submission
        reviewer = User(
            email="unassigned@example.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(reviewer)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(reviewer)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Test claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Note: reviewer is NOT assigned to submission

        token = create_access_token(data={"sub": str(reviewer.id)})

        # Act
        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Trying to save"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_save_draft_submitter_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test submitter cannot save draft (403)."""
        # Arrange
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Test claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(submitter.id)})

        # Act
        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Submitter trying to save"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_save_draft_published_state_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test cannot save draft when workflow is in published state (locked)."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(admin)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="completed",
            workflow_state=WorkflowState.PUBLISHED,  # Locked state
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Published claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Verified as true",
            sources=["https://source.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Trying to modify published"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403
        assert (
            "locked" in response.json()["detail"].lower()
            or "published" in response.json()["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_save_draft_rejected_state_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test cannot save draft when workflow is in rejected state (locked)."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(admin)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="rejected",
            workflow_state=WorkflowState.REJECTED,  # Locked state
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Rejected claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Rejected",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Trying to modify rejected"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_save_draft_archived_state_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test cannot save draft when workflow is in archived state (locked)."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(admin)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="archived",
            workflow_state=WorkflowState.ARCHIVED,  # Locked state
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Archived claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Archived",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Trying to modify archived"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_save_draft_fact_check_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test saving draft for non-existent fact-check returns 404."""
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
        response = client.patch(
            f"/api/v1/fact-checks/{fake_id}/draft",
            json={"claim_summary": "Draft for non-existent"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_save_draft_requires_auth(self, client: TestClient) -> None:
        """Test saving draft requires authentication."""
        fake_id = uuid4()
        response = client.patch(
            f"/api/v1/fact-checks/{fake_id}/draft",
            json={"claim_summary": "Unauthenticated save"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_save_draft_short_justification_validation(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test saving draft with short justification is allowed (work-in-progress)."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(admin)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Test claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act: Short justification (less than 50 chars)
        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"justification": "Too short"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert: Drafts allow short text (work-in-progress), validation happens at submit
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_save_draft_updates_timestamp(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test saving draft updates draft_updated_at timestamp."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(admin)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Test claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        before_save = datetime.now(timezone.utc)
        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Testing timestamp"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        draft_updated_at = datetime.fromisoformat(data["draft_updated_at"].replace("Z", "+00:00"))
        # Use normalize_dt for cross-database compatibility
        assert normalize_dt(draft_updated_at) >= normalize_dt(before_save)


class TestGetDraft:
    """Tests for GET /api/v1/fact-checks/{id}/draft - Retrieve draft."""

    @pytest.mark.asyncio
    async def test_get_draft_as_assigned_reviewer_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test assigned reviewer can get draft."""
        # Arrange
        reviewer = User(
            email="reviewer@example.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(reviewer)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(reviewer)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Test claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Assign reviewer
        assignment = SubmissionReviewer(
            submission_id=submission.id,
            reviewer_id=reviewer.id,
            assigned_by_id=submitter.id,
        )
        db_session.add(assignment)
        await db_session.commit()

        token = create_access_token(data={"sub": str(reviewer.id)})

        # First save a draft
        client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Saved draft content"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Act: Get the draft
        response = client.get(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["fact_check_id"] == str(fact_check.id)
        assert data["has_draft"] is True
        assert data["draft_content"]["claim_summary"] == "Saved draft content"

    @pytest.mark.asyncio
    async def test_get_draft_as_admin_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can get draft on any fact-check."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(admin)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Test claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        response = client.get(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["has_draft"] is False  # No draft saved yet
        assert data["draft_content"] is None

    @pytest.mark.asyncio
    async def test_get_draft_no_draft_exists(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting draft when none exists returns has_draft=False."""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(admin)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Test claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        response = client.get(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["has_draft"] is False
        assert data["draft_content"] is None
        assert data["draft_updated_at"] is None

    @pytest.mark.asyncio
    async def test_get_draft_unassigned_reviewer_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test unassigned reviewer cannot get draft (403)."""
        # Arrange
        reviewer = User(
            email="unassigned@example.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(reviewer)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(reviewer)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Test claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(reviewer.id)})

        # Act
        response = client.get(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_draft_submitter_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test submitter cannot get draft (403)."""
        # Arrange
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=WorkflowState.IN_RESEARCH,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Test claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        token = create_access_token(data={"sub": str(submitter.id)})

        # Act
        response = client.get(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_draft_fact_check_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting draft for non-existent fact-check returns 404."""
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
            f"/api/v1/fact-checks/{fake_id}/draft",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_draft_requires_auth(self, client: TestClient) -> None:
        """Test getting draft requires authentication."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/fact-checks/{fake_id}/draft")
        assert response.status_code == 401


class TestDraftEditableStates:
    """Tests for editable workflow states: assigned, in_research, draft_ready, needs_more_research."""

    @pytest.mark.asyncio
    async def test_save_draft_assigned_state_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test can save draft in ASSIGNED state."""
        admin, submitter, submission, fact_check = await self._create_test_data(
            db_session, WorkflowState.ASSIGNED
        )
        token = create_access_token(data={"sub": str(admin.id)})

        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Draft in assigned state"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_save_draft_in_research_state_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test can save draft in IN_RESEARCH state."""
        admin, submitter, submission, fact_check = await self._create_test_data(
            db_session, WorkflowState.IN_RESEARCH
        )
        token = create_access_token(data={"sub": str(admin.id)})

        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Draft in research state"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_save_draft_draft_ready_state_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test can save draft in DRAFT_READY state."""
        admin, submitter, submission, fact_check = await self._create_test_data(
            db_session, WorkflowState.DRAFT_READY
        )
        token = create_access_token(data={"sub": str(admin.id)})

        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Draft in draft_ready state"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_save_draft_needs_more_research_state_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test can save draft in NEEDS_MORE_RESEARCH state."""
        admin, submitter, submission, fact_check = await self._create_test_data(
            db_session, WorkflowState.NEEDS_MORE_RESEARCH
        )
        token = create_access_token(data={"sub": str(admin.id)})

        response = client.patch(
            f"/api/v1/fact-checks/{fact_check.id}/draft",
            json={"claim_summary": "Draft in needs_more_research state"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    async def _create_test_data(
        self, db_session: AsyncSession, workflow_state: WorkflowState
    ) -> tuple[User, User, Submission, FactCheck]:
        """Helper to create test data with specific workflow state."""
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(admin)
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(submitter)

        submission = Submission(
            user_id=submitter.id,
            content="Test content",
            submission_type="text",
            status="processing",
            workflow_state=workflow_state,
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        claim = Claim(content="Test claim", source="https://example.com")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        submission.claims.append(claim)
        await db_session.commit()

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.0,
            reasoning="Pending",
            sources=[],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        return admin, submitter, submission, fact_check
