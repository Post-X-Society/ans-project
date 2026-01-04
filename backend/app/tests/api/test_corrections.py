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
