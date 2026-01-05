"""
Tests for Correction API endpoints - TDD approach: Write tests FIRST.

Issue #76: Backend: Correction Request Service (TDD)
EPIC #50: Corrections & Complaints System
ADR 0005: EFCSN Compliance Architecture

Tests cover:
- POST /api/v1/corrections - public submission (no auth required)
- GET /api/v1/corrections - list corrections (admin only)
- GET /api/v1/corrections/{id} - get correction by ID
- GET /api/v1/corrections/fact-check/{fact_check_id} - get corrections for fact-check
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.correction import Correction, CorrectionStatus, CorrectionType
from app.models.fact_check import FactCheck
from app.models.user import User, UserRole


class TestPublicCorrectionSubmission:
    """Tests for public correction submission endpoint (no auth required)."""

    @pytest.mark.asyncio
    async def test_submit_correction_request_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test successful public correction submission."""
        # Create prerequisite entities
        claim: Claim = Claim(content="Public submission test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Submit correction request (no auth required)
        payload: dict[str, Any] = {
            "fact_check_id": str(fact_check.id),
            "correction_type": "substantial",
            "request_details": "The verdict should be TRUE. New evidence shows the claim is accurate.",
            "requester_email": "user@example.com",
        }

        response = client.post("/api/v1/corrections", json=payload)

        # Assert
        assert response.status_code == 201
        data: dict[str, Any] = response.json()
        assert "id" in data
        assert data["fact_check_id"] == str(fact_check.id)
        assert data["correction_type"] == "substantial"
        assert data["status"] == "pending"
        assert data["requester_email"] == "user@example.com"
        assert "sla_deadline" in data
        assert data["sla_deadline"] is not None

    @pytest.mark.asyncio
    async def test_submit_correction_request_anonymous(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test anonymous correction submission (no email)."""
        # Create prerequisite entities
        claim: Claim = Claim(content="Anonymous test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.8,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Submit anonymous correction request
        payload: dict[str, Any] = {
            "fact_check_id": str(fact_check.id),
            "correction_type": "update",
            "request_details": "Please add more context.",
        }

        response = client.post("/api/v1/corrections", json=payload)

        # Assert
        assert response.status_code == 201
        data: dict[str, Any] = response.json()
        assert data["requester_email"] is None

    @pytest.mark.asyncio
    async def test_submit_correction_request_invalid_fact_check_id(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test correction submission with non-existent fact_check_id."""
        fake_id: str = str(uuid4())

        payload: dict[str, Any] = {
            "fact_check_id": fake_id,
            "correction_type": "minor",
            "request_details": "This should fail.",
            "requester_email": "user@example.com",
        }

        response = client.post("/api/v1/corrections", json=payload)

        # Assert 404 Not Found
        assert response.status_code == 404
        data: dict[str, Any] = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_submit_correction_request_invalid_correction_type(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test correction submission with invalid correction_type."""
        # Create prerequisite entities
        claim: Claim = Claim(content="Invalid type test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        payload: dict[str, Any] = {
            "fact_check_id": str(fact_check.id),
            "correction_type": "invalid_type",  # Invalid
            "request_details": "This should fail.",
        }

        response = client.post("/api/v1/corrections", json=payload)

        # Assert 422 Validation Error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_correction_request_missing_details(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test correction submission without request_details."""
        # Create prerequisite entities
        claim: Claim = Claim(content="Missing details test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        payload: dict[str, Any] = {
            "fact_check_id": str(fact_check.id),
            "correction_type": "minor",
            # Missing request_details
        }

        response = client.post("/api/v1/corrections", json=payload)

        # Assert 422 Validation Error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_correction_request_empty_details(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test correction submission with empty request_details."""
        # Create prerequisite entities
        claim: Claim = Claim(content="Empty details test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        payload: dict[str, Any] = {
            "fact_check_id": str(fact_check.id),
            "correction_type": "minor",
            "request_details": "",  # Empty
        }

        response = client.post("/api/v1/corrections", json=payload)

        # Assert 422 Validation Error
        assert response.status_code == 422


class TestGetCorrectionById:
    """Tests for getting a correction by ID."""

    @pytest.mark.asyncio
    async def test_get_correction_by_id_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting a correction by ID."""
        # Create prerequisite entities
        claim: Claim = Claim(content="Get by ID test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Test correction.",
            status=CorrectionStatus.PENDING,
            requester_email="user@example.com",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Get correction by ID
        response = client.get(f"/api/v1/corrections/{correction.id}")

        # Assert
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["id"] == str(correction.id)
        assert data["correction_type"] == "substantial"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_correction_by_id_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting a non-existent correction returns 404."""
        fake_id: str = str(uuid4())

        response = client.get(f"/api/v1/corrections/{fake_id}")

        # Assert 404 Not Found
        assert response.status_code == 404


class TestGetCorrectionsForFactCheck:
    """Tests for getting corrections for a specific fact-check."""

    @pytest.mark.asyncio
    async def test_get_corrections_for_fact_check(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting all corrections for a fact-check."""
        # Create prerequisite entities
        claim: Claim = Claim(content="Corrections list test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create multiple corrections
        correction1: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="First correction.",
            status=CorrectionStatus.PENDING,
        )
        correction2: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Second correction.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add_all([correction1, correction2])
        await db_session.commit()

        # Get corrections for fact-check
        response = client.get(f"/api/v1/corrections/fact-check/{fact_check.id}")

        # Assert
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["fact_check_id"] == str(fact_check.id)
        assert len(data["corrections"]) == 2
        assert data["total_count"] == 2

    @pytest.mark.asyncio
    async def test_get_corrections_for_fact_check_empty(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting corrections for fact-check with no corrections."""
        # Create prerequisite entities
        claim: Claim = Claim(content="Empty corrections test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Get corrections for fact-check (no corrections exist)
        response = client.get(f"/api/v1/corrections/fact-check/{fact_check.id}")

        # Assert
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert len(data["corrections"]) == 0
        assert data["total_count"] == 0


class TestListCorrections:
    """Tests for listing corrections (admin endpoint)."""

    @pytest.mark.asyncio
    async def test_list_pending_corrections_admin_only(
        self,
        client: TestClient,
        db_session: AsyncSession,
        auth_user: tuple[User, str],
    ) -> None:
        """Test that listing pending corrections requires admin auth."""
        user, token = auth_user

        # Regular user should get 403
        response = client.get(
            "/api/v1/corrections/pending",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert 403 Forbidden (user is SUBMITTER, not ADMIN)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_pending_corrections_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can list pending corrections."""
        # Create admin user
        admin: User = User(
            email="admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Create token for admin
        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        # Create prerequisite entities
        claim: Claim = Claim(content="Admin list test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create corrections
        pending_correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Pending correction.",
            status=CorrectionStatus.PENDING,
        )
        accepted_correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Accepted correction.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
        )
        db_session.add_all([pending_correction, accepted_correction])
        await db_session.commit()

        # Get pending corrections as admin
        response = client.get(
            "/api/v1/corrections/pending",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert len(data["corrections"]) == 1
        assert data["corrections"][0]["status"] == "pending"


class TestCorrectionTypeFiltering:
    """Tests for filtering corrections by type."""

    @pytest.mark.asyncio
    async def test_filter_by_correction_type(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test filtering corrections by correction_type."""
        # Create prerequisite entities
        claim: Claim = Claim(content="Filter test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create corrections of different types
        minor: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Minor fix.",
            status=CorrectionStatus.PENDING,
        )
        substantial: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Major change.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add_all([minor, substantial])
        await db_session.commit()

        # Filter by type
        response = client.get(
            f"/api/v1/corrections/fact-check/{fact_check.id}",
            params={"correction_type": "substantial"},
        )

        # Assert
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert len(data["corrections"]) == 1
        assert data["corrections"][0]["correction_type"] == "substantial"


# =============================================================================
# Issue #78: GET /api/v1/corrections (Admin - List All Corrections)
# =============================================================================


class TestListAllCorrections:
    """Tests for listing all corrections (admin endpoint) - Issue #78."""

    @pytest.mark.asyncio
    async def test_list_all_corrections_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that listing all corrections requires authentication."""
        response = client.get("/api/v1/corrections")

        # Assert 401 Unauthorized (no auth header)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_all_corrections_requires_admin(
        self,
        client: TestClient,
        db_session: AsyncSession,
        auth_user: tuple[User, str],
    ) -> None:
        """Test that listing all corrections requires admin role."""
        user, token = auth_user

        response = client.get(
            "/api/v1/corrections",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert 403 Forbidden (user is SUBMITTER, not ADMIN)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_all_corrections_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can list all corrections."""
        # Create admin user
        admin: User = User(
            email="admin_list_all@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Create token for admin
        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        # Create prerequisite entities
        claim: Claim = Claim(content="List all corrections test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create corrections with different statuses
        pending: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Pending correction.",
            status=CorrectionStatus.PENDING,
        )
        accepted: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Accepted correction.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
        )
        rejected: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Rejected correction.",
            status=CorrectionStatus.REJECTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
        )
        db_session.add_all([pending, accepted, rejected])
        await db_session.commit()

        # Get all corrections as admin
        response = client.get(
            "/api/v1/corrections",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["total_count"] == 3
        assert len(data["corrections"]) == 3

    @pytest.mark.asyncio
    async def test_list_all_corrections_filter_by_status(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test filtering corrections by status."""
        # Create admin user
        admin: User = User(
            email="admin_filter_status@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        # Create prerequisite entities
        claim: Claim = Claim(content="Filter by status test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.8,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create corrections with different statuses
        pending1: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Pending one.",
            status=CorrectionStatus.PENDING,
        )
        pending2: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Pending two.",
            status=CorrectionStatus.PENDING,
        )
        accepted: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Accepted one.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
        )
        db_session.add_all([pending1, pending2, accepted])
        await db_session.commit()

        # Filter by accepted status
        response = client.get(
            "/api/v1/corrections",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"status": "accepted"},
        )

        # Assert
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["total_count"] == 1
        assert len(data["corrections"]) == 1
        assert data["corrections"][0]["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_list_all_corrections_filter_by_type(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test filtering corrections by type."""
        # Create admin user
        admin: User = User(
            email="admin_filter_type@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        # Create prerequisite entities
        claim: Claim = Claim(content="Filter by type test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.7,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create corrections with different types
        minor: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Minor fix.",
            status=CorrectionStatus.PENDING,
        )
        substantial: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Major change.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add_all([minor, substantial])
        await db_session.commit()

        # Filter by substantial type
        response = client.get(
            "/api/v1/corrections",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"correction_type": "substantial"},
        )

        # Assert
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["total_count"] == 1
        assert len(data["corrections"]) == 1
        assert data["corrections"][0]["correction_type"] == "substantial"

    @pytest.mark.asyncio
    async def test_list_all_corrections_pagination(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test pagination for listing corrections."""
        # Create admin user
        admin: User = User(
            email="admin_pagination@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        from app.core.security import create_access_token

        admin_token: str = create_access_token(data={"sub": str(admin.id)})

        # Create prerequisite entities
        claim: Claim = Claim(content="Pagination test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create 5 corrections
        corrections: list[Correction] = []
        for i in range(5):
            correction: Correction = Correction(
                fact_check_id=fact_check.id,
                correction_type=CorrectionType.MINOR,
                request_details=f"Correction {i}.",
                status=CorrectionStatus.PENDING,
            )
            corrections.append(correction)
        db_session.add_all(corrections)
        await db_session.commit()

        # Get first page (limit 2)
        response = client.get(
            "/api/v1/corrections",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 2, "offset": 0},
        )

        # Assert
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["total_count"] == 5
        assert len(data["corrections"]) == 2

        # Get second page
        response = client.get(
            "/api/v1/corrections",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 2, "offset": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 5
        assert len(data["corrections"]) == 2


# =============================================================================
# Issue #78: GET /api/v1/corrections/public-log (Public Corrections Log)
# =============================================================================


class TestPublicCorrectionsLog:
    """Tests for public corrections log endpoint (EFCSN requirement) - Issue #78."""

    @pytest.mark.asyncio
    async def test_public_log_no_auth_required(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that public corrections log does not require authentication."""
        response = client.get("/api/v1/corrections/public-log")

        # Assert 200 OK (no auth required)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_public_log_returns_only_applied_corrections(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that public log only returns applied (substantial/update) corrections."""
        # Create admin user for reviewed_by
        admin: User = User(
            email="admin_public_log@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Create prerequisite entities
        claim: Claim = Claim(content="Public log test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create corrections of different types and statuses
        # Pending - should NOT appear
        pending: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Pending substantial.",
            status=CorrectionStatus.PENDING,
        )
        # Accepted minor - should NOT appear (minor corrections not public)
        accepted_minor: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Accepted minor.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
        )
        # Accepted substantial - SHOULD appear
        accepted_substantial: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Accepted substantial for public log.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="This was a valid correction.",
        )
        # Accepted update - SHOULD appear
        accepted_update: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Accepted update for public log.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Added new information.",
        )
        # Rejected - should NOT appear
        rejected: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Rejected substantial.",
            status=CorrectionStatus.REJECTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
        )
        db_session.add_all(
            [pending, accepted_minor, accepted_substantial, accepted_update, rejected]
        )
        await db_session.commit()

        # Get public log
        response = client.get("/api/v1/corrections/public-log")

        # Assert
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        # Should only have substantial and update accepted corrections
        assert data["total_count"] == 2
        assert len(data["corrections"]) == 2

        # Verify only substantial and update types are returned
        types_returned: list[str] = [c["correction_type"] for c in data["corrections"]]
        assert "substantial" in types_returned
        assert "update" in types_returned
        assert "minor" not in types_returned

    @pytest.mark.asyncio
    async def test_public_log_hides_requester_email(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that public log does not expose requester email for privacy."""
        # Create admin user
        admin: User = User(
            email="admin_privacy@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Create prerequisite entities
        claim: Claim = Claim(content="Privacy test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.85,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create accepted substantial correction with email
        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Correction with email.",
            status=CorrectionStatus.ACCEPTED,
            requester_email="private_email@example.com",
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Approved.",
        )
        db_session.add(correction)
        await db_session.commit()

        # Get public log
        response = client.get("/api/v1/corrections/public-log")

        # Assert email is not exposed
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert len(data["corrections"]) == 1
        # Email should be completely omitted from public log for privacy
        assert "requester_email" not in data["corrections"][0]

    @pytest.mark.asyncio
    async def test_public_log_ordered_by_reviewed_date(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that public log is ordered by reviewed_at date (newest first)."""
        from datetime import timedelta

        # Create admin user
        admin: User = User(
            email="admin_order@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Create prerequisite entities
        claim: Claim = Claim(content="Order test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.75,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        now: datetime = datetime.now(timezone.utc)

        # Create corrections reviewed at different times
        older_correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Older correction.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=now - timedelta(days=10),
            resolution_notes="Old correction.",
        )
        newer_correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Newer correction.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=now - timedelta(days=1),
            resolution_notes="New correction.",
        )
        db_session.add_all([older_correction, newer_correction])
        await db_session.commit()

        # Get public log
        response = client.get("/api/v1/corrections/public-log")

        # Assert ordered by reviewed_at (newest first)
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert len(data["corrections"]) == 2
        # First should be newer (update type)
        assert data["corrections"][0]["correction_type"] == "update"
        # Second should be older (substantial type)
        assert data["corrections"][1]["correction_type"] == "substantial"

    @pytest.mark.asyncio
    async def test_public_log_empty_when_no_applied_corrections(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test that public log returns empty list when no corrections applied."""
        # Create prerequisite entities
        claim: Claim = Claim(content="Empty log test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create only pending correction
        pending: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Still pending.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add(pending)
        await db_session.commit()

        # Get public log
        response = client.get("/api/v1/corrections/public-log")

        # Assert empty list
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["total_count"] == 0
        assert len(data["corrections"]) == 0
