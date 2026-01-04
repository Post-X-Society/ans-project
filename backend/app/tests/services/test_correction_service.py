"""
Tests for CorrectionService - TDD approach: Write tests FIRST.

Issue #76: Backend: Correction Request Service (TDD)
EPIC #50: Corrections & Complaints System
ADR 0005: EFCSN Compliance Architecture

Tests cover:
- CorrectionService.submit_request() - public endpoint (no auth)
- SLA deadline calculation (7-day deadline)
- Acknowledgment email functionality
- Correction routing/triage logic
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.correction import Correction, CorrectionStatus, CorrectionType
from app.models.fact_check import FactCheck
from app.models.user import User, UserRole
from app.tests.helpers import normalize_dt


class TestCorrectionServiceSubmitRequest:
    """Tests for CorrectionService.submit_request() - public submission endpoint."""

    @pytest.mark.asyncio
    async def test_submit_request_creates_correction_with_required_fields(
        self, db_session: AsyncSession
    ) -> None:
        """Test that submit_request creates a correction with all required fields."""
        from app.services.correction_service import CorrectionService

        # Create prerequisite entities
        claim: Claim = Claim(content="Test claim for correction", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.95,
            reasoning="This is false",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Submit correction request
        service: CorrectionService = CorrectionService(db_session)
        result: Correction = await service.submit_request(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="The rating should be TRUE, not FALSE. New evidence shows the claim is accurate.",
            requester_email="user@example.com",
        )

        # Assert
        assert result is not None
        assert isinstance(result.id, UUID)
        assert result.fact_check_id == fact_check.id
        assert result.correction_type == CorrectionType.SUBSTANTIAL
        assert (
            result.request_details
            == "The rating should be TRUE, not FALSE. New evidence shows the claim is accurate."
        )
        assert result.requester_email == "user@example.com"
        assert result.status == CorrectionStatus.PENDING
        assert result.reviewed_by_id is None
        assert result.reviewed_at is None
        assert result.resolution_notes is None

    @pytest.mark.asyncio
    async def test_submit_request_allows_anonymous_submission(
        self, db_session: AsyncSession
    ) -> None:
        """Test that submit_request works without requester_email (anonymous)."""
        from app.services.correction_service import CorrectionService

        # Create prerequisite entities
        claim: Claim = Claim(content="Anonymous correction test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Verified",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Submit anonymous correction request
        service: CorrectionService = CorrectionService(db_session)
        result: Correction = await service.submit_request(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Please add more context to this fact-check.",
            requester_email=None,  # Anonymous
        )

        # Assert
        assert result is not None
        assert result.requester_email is None
        assert result.status == CorrectionStatus.PENDING

    @pytest.mark.asyncio
    async def test_submit_request_supports_all_correction_types(
        self, db_session: AsyncSession
    ) -> None:
        """Test that all correction types are supported."""
        from app.services.correction_service import CorrectionService

        # Create prerequisite entities
        claim: Claim = Claim(content="Correction types test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.8,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        service: CorrectionService = CorrectionService(db_session)

        # Test each correction type
        correction_types: list[CorrectionType] = [
            CorrectionType.MINOR,
            CorrectionType.UPDATE,
            CorrectionType.SUBSTANTIAL,
        ]

        for i, correction_type in enumerate(correction_types):
            result: Correction = await service.submit_request(
                fact_check_id=fact_check.id,
                correction_type=correction_type,
                request_details=f"Test correction type: {correction_type.value}",
                requester_email=f"user{i}@example.com",
            )
            assert result.correction_type == correction_type

    @pytest.mark.asyncio
    async def test_submit_request_raises_error_for_nonexistent_fact_check(
        self, db_session: AsyncSession
    ) -> None:
        """Test that submit_request raises error for non-existent fact_check_id."""
        from uuid import uuid4

        from app.services.correction_service import (
            CorrectionService,
            FactCheckNotFoundError,
        )

        service: CorrectionService = CorrectionService(db_session)
        fake_id: UUID = uuid4()

        with pytest.raises(FactCheckNotFoundError) as exc_info:
            await service.submit_request(
                fact_check_id=fake_id,
                correction_type=CorrectionType.MINOR,
                request_details="This should fail.",
                requester_email="user@example.com",
            )

        assert str(fake_id) in str(exc_info.value)


class TestCorrectionServiceSLADeadline:
    """Tests for SLA deadline calculation (7-day SLA per EFCSN requirements)."""

    @pytest.mark.asyncio
    async def test_submit_request_sets_7_day_sla_deadline(self, db_session: AsyncSession) -> None:
        """Test that submit_request sets a 7-day SLA deadline."""
        from app.services.correction_service import CorrectionService

        # Create prerequisite entities
        claim: Claim = Claim(content="SLA deadline test", source="test")
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

        # Submit request and capture time
        before_submit: datetime = datetime.now(timezone.utc)

        service: CorrectionService = CorrectionService(db_session)
        result: Correction = await service.submit_request(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Test SLA deadline.",
            requester_email="user@example.com",
        )

        after_submit: datetime = datetime.now(timezone.utc)

        # Assert SLA deadline is set and is approximately 7 days from now
        assert result.sla_deadline is not None

        expected_deadline_min: datetime = before_submit + timedelta(days=7)
        expected_deadline_max: datetime = after_submit + timedelta(days=7)

        # Normalize datetimes for comparison (SQLite may return naive datetimes)
        normalized_deadline: datetime = normalize_dt(result.sla_deadline)
        normalized_min: datetime = normalize_dt(expected_deadline_min)
        normalized_max: datetime = normalize_dt(expected_deadline_max)

        assert normalized_min <= normalized_deadline <= normalized_max

    @pytest.mark.asyncio
    async def test_calculate_sla_deadline_returns_7_days_from_now(
        self, db_session: AsyncSession
    ) -> None:
        """Test the calculate_sla_deadline helper method."""
        from app.services.correction_service import CorrectionService

        service: CorrectionService = CorrectionService(db_session)

        before: datetime = datetime.now(timezone.utc)
        deadline: datetime = service.calculate_sla_deadline()
        after: datetime = datetime.now(timezone.utc)

        expected_min: datetime = before + timedelta(days=7)
        expected_max: datetime = after + timedelta(days=7)

        assert expected_min <= deadline <= expected_max

    @pytest.mark.asyncio
    async def test_get_overdue_corrections_returns_corrections_past_sla(
        self, db_session: AsyncSession
    ) -> None:
        """Test getting corrections that have passed their SLA deadline."""
        from app.services.correction_service import CorrectionService

        # Create prerequisite entities
        claim: Claim = Claim(content="Overdue test", source="test")
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

        # Create a correction with an overdue SLA deadline
        overdue_deadline: datetime = datetime.now(timezone.utc) - timedelta(days=1)
        overdue_correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="This is overdue.",
            status=CorrectionStatus.PENDING,
            sla_deadline=overdue_deadline,
        )
        db_session.add(overdue_correction)

        # Create a correction with a future SLA deadline
        future_deadline: datetime = datetime.now(timezone.utc) + timedelta(days=5)
        future_correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="This is not overdue.",
            status=CorrectionStatus.PENDING,
            sla_deadline=future_deadline,
        )
        db_session.add(future_correction)
        await db_session.commit()

        # Get overdue corrections
        service: CorrectionService = CorrectionService(db_session)
        overdue_list: list[Correction] = await service.get_overdue_corrections()

        # Assert only the overdue one is returned
        assert len(overdue_list) == 1
        assert overdue_list[0].id == overdue_correction.id


class TestCorrectionServiceAcknowledgmentEmail:
    """Tests for acknowledgment email functionality."""

    @pytest.mark.asyncio
    async def test_submit_request_sends_acknowledgment_email_when_email_provided(
        self, db_session: AsyncSession
    ) -> None:
        """Test that acknowledgment email is sent when requester provides email."""
        from app.services.correction_service import CorrectionService

        # Create prerequisite entities
        claim: Claim = Claim(content="Email test", source="test")
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

        # Mock the email service
        with patch(
            "app.services.correction_service.send_correction_acknowledgment_email"
        ) as mock_send:
            mock_send.return_value = True

            service: CorrectionService = CorrectionService(db_session)
            result: Correction = await service.submit_request(
                fact_check_id=fact_check.id,
                correction_type=CorrectionType.UPDATE,
                request_details="Please update this fact-check.",
                requester_email="user@example.com",
            )

            # Assert email was sent
            mock_send.assert_called_once()
            call_kwargs: dict[str, Any] = mock_send.call_args[1]
            assert call_kwargs["to_email"] == "user@example.com"
            assert call_kwargs["correction_id"] == result.id

    @pytest.mark.asyncio
    async def test_submit_request_does_not_send_email_for_anonymous(
        self, db_session: AsyncSession
    ) -> None:
        """Test that no email is sent for anonymous submissions."""
        from app.services.correction_service import CorrectionService

        # Create prerequisite entities
        claim: Claim = Claim(content="Anonymous email test", source="test")
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

        # Mock the email service
        with patch(
            "app.services.correction_service.send_correction_acknowledgment_email"
        ) as mock_send:
            service: CorrectionService = CorrectionService(db_session)
            await service.submit_request(
                fact_check_id=fact_check.id,
                correction_type=CorrectionType.MINOR,
                request_details="Anonymous correction.",
                requester_email=None,  # Anonymous
            )

            # Assert email was NOT sent
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_submit_request_continues_if_email_fails(self, db_session: AsyncSession) -> None:
        """Test that correction is still created even if email fails."""
        from app.services.correction_service import CorrectionService

        # Create prerequisite entities
        claim: Claim = Claim(content="Email failure test", source="test")
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

        # Mock the email service to fail
        with patch(
            "app.services.correction_service.send_correction_acknowledgment_email"
        ) as mock_send:
            mock_send.return_value = False  # Email fails

            service: CorrectionService = CorrectionService(db_session)
            result: Correction = await service.submit_request(
                fact_check_id=fact_check.id,
                correction_type=CorrectionType.SUBSTANTIAL,
                request_details="Correction despite email failure.",
                requester_email="user@example.com",
            )

            # Assert correction was still created
            assert result is not None
            assert result.id is not None
            assert result.status == CorrectionStatus.PENDING


class TestCorrectionServiceTriageRouting:
    """Tests for correction routing/triage logic."""

    @pytest.mark.asyncio
    async def test_get_pending_corrections_returns_pending_only(
        self, db_session: AsyncSession
    ) -> None:
        """Test getting only pending corrections for triage."""
        from app.services.correction_service import CorrectionService

        # Create prerequisite entities
        claim: Claim = Claim(content="Triage test", source="test")
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

        # Create reviewer
        reviewer: User = User(
            email="reviewer@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        # Create corrections with different statuses
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
            reviewed_by_id=reviewer.id,
            reviewed_at=datetime.now(timezone.utc),
        )
        rejected_correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Rejected correction.",
            status=CorrectionStatus.REJECTED,
            reviewed_by_id=reviewer.id,
            reviewed_at=datetime.now(timezone.utc),
        )
        db_session.add_all([pending_correction, accepted_correction, rejected_correction])
        await db_session.commit()

        # Get pending corrections
        service: CorrectionService = CorrectionService(db_session)
        pending_list: list[Correction] = await service.get_pending_corrections()

        # Assert only pending correction is returned
        assert len(pending_list) == 1
        assert pending_list[0].status == CorrectionStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_corrections_by_type_filters_correctly(
        self, db_session: AsyncSession
    ) -> None:
        """Test filtering corrections by type for triage routing."""
        from app.services.correction_service import CorrectionService

        # Create prerequisite entities
        claim: Claim = Claim(content="Type filter test", source="test")
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
        minor_correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Minor fix.",
            status=CorrectionStatus.PENDING,
        )
        substantial_correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Major change.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add_all([minor_correction, substantial_correction])
        await db_session.commit()

        # Get corrections by type
        service: CorrectionService = CorrectionService(db_session)
        substantial_list: list[Correction] = await service.get_corrections_by_type(
            CorrectionType.SUBSTANTIAL
        )

        # Assert only substantial correction is returned
        assert len(substantial_list) == 1
        assert substantial_list[0].correction_type == CorrectionType.SUBSTANTIAL

    @pytest.mark.asyncio
    async def test_get_corrections_for_fact_check(self, db_session: AsyncSession) -> None:
        """Test getting all corrections for a specific fact-check."""
        from app.services.correction_service import CorrectionService

        # Create two claims with fact-checks
        claim1: Claim = Claim(content="Claim 1", source="test")
        claim2: Claim = Claim(content="Claim 2", source="test")
        db_session.add_all([claim1, claim2])
        await db_session.commit()
        await db_session.refresh(claim1)
        await db_session.refresh(claim2)

        fact_check1: FactCheck = FactCheck(
            claim_id=claim1.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        fact_check2: FactCheck = FactCheck(
            claim_id=claim2.id,
            verdict="true",
            confidence=0.8,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add_all([fact_check1, fact_check2])
        await db_session.commit()
        await db_session.refresh(fact_check1)
        await db_session.refresh(fact_check2)

        # Create corrections for fact_check1 only
        correction1: Correction = Correction(
            fact_check_id=fact_check1.id,
            correction_type=CorrectionType.MINOR,
            request_details="Correction for fact_check1.",
            status=CorrectionStatus.PENDING,
        )
        correction2: Correction = Correction(
            fact_check_id=fact_check1.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Another for fact_check1.",
            status=CorrectionStatus.PENDING,
        )
        correction3: Correction = Correction(
            fact_check_id=fact_check2.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Correction for fact_check2.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add_all([correction1, correction2, correction3])
        await db_session.commit()

        # Get corrections for fact_check1
        service: CorrectionService = CorrectionService(db_session)
        corrections: list[Correction] = await service.get_corrections_for_fact_check(fact_check1.id)

        # Assert only fact_check1 corrections are returned
        assert len(corrections) == 2
        for correction in corrections:
            assert correction.fact_check_id == fact_check1.id

    @pytest.mark.asyncio
    async def test_prioritize_corrections_orders_by_type_and_age(
        self, db_session: AsyncSession
    ) -> None:
        """Test that corrections are prioritized by type (substantial first) and age."""
        from app.services.correction_service import CorrectionService

        # Create prerequisite entities
        claim: Claim = Claim(content="Priority test", source="test")
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

        # Create corrections with different priorities
        # Note: Substantial should come before Minor, and older before newer
        minor_old: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Minor old.",
            status=CorrectionStatus.PENDING,
        )
        substantial_new: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Substantial new.",
            status=CorrectionStatus.PENDING,
        )
        update_new: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Update new.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add_all([minor_old, substantial_new, update_new])
        await db_session.commit()

        # Get prioritized corrections
        service: CorrectionService = CorrectionService(db_session)
        prioritized: list[Correction] = await service.get_prioritized_pending_corrections()

        # Assert substantial comes first
        assert len(prioritized) >= 1
        assert prioritized[0].correction_type == CorrectionType.SUBSTANTIAL


class TestCorrectionServiceGetById:
    """Tests for getting a correction by ID."""

    @pytest.mark.asyncio
    async def test_get_correction_by_id_returns_correction(self, db_session: AsyncSession) -> None:
        """Test getting a correction by its ID."""
        from app.services.correction_service import CorrectionService

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
            correction_type=CorrectionType.MINOR,
            request_details="Test correction.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Get by ID
        service: CorrectionService = CorrectionService(db_session)
        result: Correction | None = await service.get_correction_by_id(correction.id)

        # Assert
        assert result is not None
        assert result.id == correction.id

    @pytest.mark.asyncio
    async def test_get_correction_by_id_returns_none_for_nonexistent(
        self, db_session: AsyncSession
    ) -> None:
        """Test getting a non-existent correction returns None."""
        from uuid import uuid4

        from app.services.correction_service import CorrectionService

        service: CorrectionService = CorrectionService(db_session)
        result: Correction | None = await service.get_correction_by_id(uuid4())

        assert result is None
