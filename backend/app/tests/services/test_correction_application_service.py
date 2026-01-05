"""
Tests for Correction Application Service - TDD approach: Write tests FIRST.

Issue #77: Backend: Correction Application Logic (TDD)
EPIC #50: Corrections & Complaints System
ADR 0005: EFCSN Compliance Architecture

Tests cover:
- Review corrections (accept/reject)
- Apply corrections based on type (MINOR, UPDATE, SUBSTANTIAL)
- Fact-check versioning when corrections applied
- Resolution email sending

EFCSN Correction Categories:
- MINOR: Typos, grammar, formatting (no public notice)
- UPDATE: New information, additional sources (appended note)
- SUBSTANTIAL: Rating change, major error (prominent notice)
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.correction import (
    Correction,
    CorrectionApplication,
    CorrectionStatus,
    CorrectionType,
)
from app.models.fact_check import FactCheck
from app.models.user import User, UserRole

# =============================================================================
# TEST CLASS: Review Corrections (Accept/Reject)
# =============================================================================


class TestCorrectionApplicationServiceReview:
    """Tests for reviewing corrections (accept/reject decisions)."""

    @pytest.mark.asyncio
    async def test_accept_correction_updates_status_to_accepted(
        self, db_session: AsyncSession
    ) -> None:
        """Test accepting a correction updates its status to ACCEPTED."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Test claim for accept", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.95,
            reasoning="Original reasoning",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        reviewer: User = User(
            email="reviewer@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Please fix the typo in reasoning.",
            status=CorrectionStatus.PENDING,
            requester_email="user@example.com",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Accept the correction
        service: CorrectionApplicationService = CorrectionApplicationService(db_session)
        result: Correction = await service.accept_correction(
            correction_id=correction.id,
            reviewer_id=reviewer.id,
            resolution_notes="Approved - will fix the typo.",
        )

        # Assert
        assert result.status == CorrectionStatus.ACCEPTED
        assert result.reviewed_by_id == reviewer.id
        assert result.reviewed_at is not None
        assert result.resolution_notes == "Approved - will fix the typo."

    @pytest.mark.asyncio
    async def test_reject_correction_updates_status_to_rejected(
        self, db_session: AsyncSession
    ) -> None:
        """Test rejecting a correction updates its status to REJECTED."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Test claim for reject", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Verified reasoning",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        reviewer: User = User(
            email="reviewer2@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="The rating should be FALSE.",
            status=CorrectionStatus.PENDING,
            requester_email="user@example.com",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Reject the correction
        service: CorrectionApplicationService = CorrectionApplicationService(db_session)
        result: Correction = await service.reject_correction(
            correction_id=correction.id,
            reviewer_id=reviewer.id,
            resolution_notes="Rejected - our evidence supports the TRUE rating.",
        )

        # Assert
        assert result.status == CorrectionStatus.REJECTED
        assert result.reviewed_by_id == reviewer.id
        assert result.reviewed_at is not None
        assert result.resolution_notes == "Rejected - our evidence supports the TRUE rating."

    @pytest.mark.asyncio
    async def test_accept_correction_requires_resolution_notes(
        self, db_session: AsyncSession
    ) -> None:
        """Test that accepting a correction requires resolution notes."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
            ValidationError,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Notes required test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.85,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        reviewer: User = User(
            email="reviewer3@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Please add more context.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Attempt to accept without resolution notes
        service: CorrectionApplicationService = CorrectionApplicationService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.accept_correction(
                correction_id=correction.id,
                reviewer_id=reviewer.id,
                resolution_notes="",  # Empty notes
            )

        assert "Resolution notes are required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cannot_review_already_reviewed_correction(
        self, db_session: AsyncSession
    ) -> None:
        """Test that already reviewed corrections cannot be reviewed again."""
        from app.services.correction_application_service import (
            CorrectionAlreadyReviewedError,
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Already reviewed test", source="test")
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

        reviewer: User = User(
            email="reviewer4@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        # Create already accepted correction
        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Already reviewed.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=reviewer.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Already processed.",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Attempt to review again
        service: CorrectionApplicationService = CorrectionApplicationService(db_session)

        with pytest.raises(CorrectionAlreadyReviewedError):
            await service.accept_correction(
                correction_id=correction.id,
                reviewer_id=reviewer.id,
                resolution_notes="Trying to accept again.",
            )

    @pytest.mark.asyncio
    async def test_review_correction_raises_error_for_nonexistent(
        self, db_session: AsyncSession
    ) -> None:
        """Test reviewing a non-existent correction raises an error."""
        from uuid import uuid4

        from app.services.correction_application_service import (
            CorrectionApplicationService,
            CorrectionNotFoundError,
        )

        reviewer: User = User(
            email="reviewer5@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        service: CorrectionApplicationService = CorrectionApplicationService(db_session)

        with pytest.raises(CorrectionNotFoundError):
            await service.accept_correction(
                correction_id=uuid4(),
                reviewer_id=reviewer.id,
                resolution_notes="This should fail.",
            )


# =============================================================================
# TEST CLASS: Apply MINOR Corrections
# =============================================================================


class TestCorrectionApplicationServiceMinor:
    """Tests for applying MINOR corrections (no public notice)."""

    @pytest.mark.asyncio
    async def test_apply_minor_correction_updates_fact_check_without_notice(
        self, db_session: AsyncSession
    ) -> None:
        """Test MINOR correction updates fact-check without adding a public notice."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Minor correction test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.95,
            reasoning="Original reasnoing with typo",  # Intentional typo
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        admin: User = User(
            email="admin_minor@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Fix typo: reasnoing -> reasoning",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Approved typo fix.",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Apply the minor correction
        service: CorrectionApplicationService = CorrectionApplicationService(db_session)
        changes: dict[str, Any] = {"reasoning": "Original reasoning with typo fixed"}

        application: CorrectionApplication = await service.apply_correction(
            correction_id=correction.id,
            applied_by_id=admin.id,
            changes=changes,
            changes_summary="Fixed typo in reasoning",
        )

        # Assert CorrectionApplication record created
        assert application is not None
        assert application.correction_id == correction.id
        assert application.applied_by_id == admin.id
        assert application.version == 1
        assert application.is_current is True
        assert application.changes_summary == "Fixed typo in reasoning"
        assert "reasoning" in application.previous_content
        assert "reasoning" in application.new_content

        # Assert fact-check updated WITHOUT correction_notice
        await db_session.refresh(fact_check)
        assert fact_check.reasoning == "Original reasoning with typo fixed"
        # MINOR corrections should NOT have a correction_notice field populated
        assert not hasattr(fact_check, "correction_notice") or fact_check.correction_notice is None  # type: ignore[union-attr]

    @pytest.mark.asyncio
    async def test_minor_correction_creates_version_record(self, db_session: AsyncSession) -> None:
        """Test MINOR correction creates a versioned CorrectionApplication record."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Version test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.8,
            reasoning="Test reasoning",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        admin: User = User(
            email="admin_version@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Fix grammar.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Grammar fix approved.",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Apply correction
        service: CorrectionApplicationService = CorrectionApplicationService(db_session)
        changes: dict[str, Any] = {"reasoning": "Fixed grammar in reasoning"}

        application: CorrectionApplication = await service.apply_correction(
            correction_id=correction.id,
            applied_by_id=admin.id,
            changes=changes,
            changes_summary="Grammar correction",
        )

        # Assert version tracking
        assert application.version == 1
        assert application.previous_content["reasoning"] == "Test reasoning"
        assert application.new_content["reasoning"] == "Fixed grammar in reasoning"


# =============================================================================
# TEST CLASS: Apply UPDATE Corrections
# =============================================================================


class TestCorrectionApplicationServiceUpdate:
    """Tests for applying UPDATE corrections (append explanatory note)."""

    @pytest.mark.asyncio
    async def test_apply_update_correction_appends_note_to_fact_check(
        self, db_session: AsyncSession
    ) -> None:
        """Test UPDATE correction appends an explanatory note to the fact-check."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Update correction test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="partly_false",
            confidence=0.85,
            reasoning="Original analysis based on initial sources.",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        admin: User = User(
            email="admin_update@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Please add the new study from Nature as a source.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Will add the new source.",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Apply the update correction
        service: CorrectionApplicationService = CorrectionApplicationService(db_session)
        changes: dict[str, Any] = {
            "sources": ["https://example.com", "https://nature.com/new-study"],
            "reasoning": "Original analysis based on initial sources. [Updated with additional source]",
        }

        application: CorrectionApplication = await service.apply_correction(
            correction_id=correction.id,
            applied_by_id=admin.id,
            changes=changes,
            changes_summary="Added Nature study as additional source",
        )

        # Assert CorrectionApplication record created
        assert application is not None
        assert application.correction_id == correction.id

        # Assert fact-check has update note appended
        await db_session.refresh(fact_check)
        assert "https://nature.com/new-study" in fact_check.sources
        assert "[Updated" in fact_check.reasoning or "Update" in application.changes_summary

    @pytest.mark.asyncio
    async def test_update_correction_includes_date_in_note(self, db_session: AsyncSession) -> None:
        """Test UPDATE correction includes date in the appended note."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Date in note test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Original fact-check.",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        admin: User = User(
            email="admin_date@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Add clarification about context.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Will add context.",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Apply the update correction with date
        service: CorrectionApplicationService = CorrectionApplicationService(db_session)
        today: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        update_note: str = (
            f"\n\n[Update ({today}): Added clarification about the original context of the claim.]"
        )

        changes: dict[str, Any] = {
            "reasoning": f"Original fact-check.{update_note}",
        }

        application: CorrectionApplication = await service.apply_correction(
            correction_id=correction.id,
            applied_by_id=admin.id,
            changes=changes,
            changes_summary=f"Update ({today}): Added context clarification",
        )

        # Assert date is in the changes summary and application created
        assert application is not None
        await db_session.refresh(fact_check)
        assert today in fact_check.reasoning
        assert "[Update" in fact_check.reasoning


# =============================================================================
# TEST CLASS: Apply SUBSTANTIAL Corrections
# =============================================================================


class TestCorrectionApplicationServiceSubstantial:
    """Tests for applying SUBSTANTIAL corrections (prominent notice)."""

    @pytest.mark.asyncio
    async def test_apply_substantial_correction_adds_prominent_notice(
        self, db_session: AsyncSession
    ) -> None:
        """Test SUBSTANTIAL correction adds a prominent correction notice."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Substantial correction test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.95,
            reasoning="This claim is false based on our analysis.",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        admin: User = User(
            email="admin_substantial@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="New evidence proves the claim is TRUE, not FALSE.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="New authoritative source confirms claim is accurate.",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Apply the substantial correction
        service: CorrectionApplicationService = CorrectionApplicationService(db_session)
        changes: dict[str, Any] = {
            "verdict": "true",
            "reasoning": "CORRECTION: Our original rating was incorrect. New evidence confirms this claim is TRUE.",
            "correction_notice": "This fact-check was corrected on {date}. The original rating was FALSE. "
            "After reviewing new evidence, we have updated the rating to TRUE.",
        }

        application: CorrectionApplication = await service.apply_correction(
            correction_id=correction.id,
            applied_by_id=admin.id,
            changes=changes,
            changes_summary="SUBSTANTIAL CORRECTION: Changed rating from FALSE to TRUE",
        )

        # Assert CorrectionApplication record created with correction details
        assert application is not None
        assert "SUBSTANTIAL" in application.changes_summary

        # Assert fact-check updated with new verdict
        await db_session.refresh(fact_check)
        assert fact_check.verdict == "true"
        assert "CORRECTION" in fact_check.reasoning

        # Verify previous content preserved for audit
        assert application.previous_content["verdict"] == "false"
        assert application.new_content["verdict"] == "true"

    @pytest.mark.asyncio
    async def test_substantial_correction_preserves_full_history(
        self, db_session: AsyncSession
    ) -> None:
        """Test SUBSTANTIAL correction preserves the full change history."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="History preservation test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        original_reasoning: str = "Original analysis showing claim is false."
        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning=original_reasoning,
            sources=["https://original-source.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        admin: User = User(
            email="admin_history@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Major factual error discovered.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Confirmed major error. Updating verdict.",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Apply the correction
        service: CorrectionApplicationService = CorrectionApplicationService(db_session)
        new_reasoning: str = "CORRECTED: Updated analysis shows claim is actually true."
        changes: dict[str, Any] = {
            "verdict": "true",
            "reasoning": new_reasoning,
            "sources": ["https://original-source.com", "https://new-evidence.com"],
        }

        application: CorrectionApplication = await service.apply_correction(
            correction_id=correction.id,
            applied_by_id=admin.id,
            changes=changes,
            changes_summary="Major correction: verdict changed from false to true",
        )

        # Verify full history preserved
        assert application.previous_content["verdict"] == "false"
        assert application.previous_content["reasoning"] == original_reasoning
        assert application.previous_content["sources"] == ["https://original-source.com"]

        assert application.new_content["verdict"] == "true"
        assert application.new_content["reasoning"] == new_reasoning


# =============================================================================
# TEST CLASS: Fact-Check Versioning
# =============================================================================


class TestCorrectionApplicationVersioning:
    """Tests for fact-check versioning when corrections are applied."""

    @pytest.mark.asyncio
    async def test_multiple_corrections_increment_version(self, db_session: AsyncSession) -> None:
        """Test multiple corrections increment the version number."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Multi-version test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.85,
            reasoning="Initial reasoning",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        admin: User = User(
            email="admin_multiversion@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        service: CorrectionApplicationService = CorrectionApplicationService(db_session)

        # Apply first correction
        correction1: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="First correction.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="First fix.",
        )
        db_session.add(correction1)
        await db_session.commit()
        await db_session.refresh(correction1)

        app1: CorrectionApplication = await service.apply_correction(
            correction_id=correction1.id,
            applied_by_id=admin.id,
            changes={"reasoning": "First update"},
            changes_summary="First correction",
        )

        # Apply second correction
        correction2: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            request_details="Second correction.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Second fix.",
        )
        db_session.add(correction2)
        await db_session.commit()
        await db_session.refresh(correction2)

        app2: CorrectionApplication = await service.apply_correction(
            correction_id=correction2.id,
            applied_by_id=admin.id,
            changes={"reasoning": "Second update"},
            changes_summary="Second correction",
        )

        # Assert versions increment
        assert app1.version == 1
        assert app2.version == 2

        # Assert only latest is current
        await db_session.refresh(app1)
        assert app1.is_current is False
        assert app2.is_current is True

    @pytest.mark.asyncio
    async def test_get_correction_history_returns_all_versions(
        self, db_session: AsyncSession
    ) -> None:
        """Test getting correction history returns all versions in order."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="History test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Initial",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        admin: User = User(
            email="admin_gethistory@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        service: CorrectionApplicationService = CorrectionApplicationService(db_session)

        # Create and apply multiple corrections
        for i in range(3):
            correction: Correction = Correction(
                fact_check_id=fact_check.id,
                correction_type=CorrectionType.MINOR,
                request_details=f"Correction {i + 1}.",
                status=CorrectionStatus.ACCEPTED,
                reviewed_by_id=admin.id,
                reviewed_at=datetime.now(timezone.utc),
                resolution_notes=f"Fix {i + 1}.",
            )
            db_session.add(correction)
            await db_session.commit()
            await db_session.refresh(correction)

            await service.apply_correction(
                correction_id=correction.id,
                applied_by_id=admin.id,
                changes={"reasoning": f"Update {i + 1}"},
                changes_summary=f"Correction {i + 1}",
            )

        # Get history
        history: list[CorrectionApplication] = await service.get_correction_history(
            fact_check_id=fact_check.id
        )

        # Assert all versions returned in order
        assert len(history) == 3
        assert history[0].version == 1
        assert history[1].version == 2
        assert history[2].version == 3


# =============================================================================
# TEST CLASS: Resolution Emails
# =============================================================================


class TestCorrectionApplicationResolutionEmail:
    """Tests for sending resolution emails to correction requesters."""

    @pytest.mark.asyncio
    async def test_sends_acceptance_email_when_correction_applied(
        self, db_session: AsyncSession
    ) -> None:
        """Test acceptance email is sent when correction is applied."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Email acceptance test", source="test")
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

        admin: User = User(
            email="admin_email@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Fix typo.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Typo fixed.",
            requester_email="requester@example.com",  # Has email
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Mock the email sending function
        with patch(
            "app.services.correction_application_service.send_correction_resolution_email"
        ) as mock_send:
            mock_send.return_value = True

            service: CorrectionApplicationService = CorrectionApplicationService(db_session)
            await service.apply_correction(
                correction_id=correction.id,
                applied_by_id=admin.id,
                changes={"reasoning": "Fixed typo"},
                changes_summary="Typo correction",
            )

            # Assert email was sent
            mock_send.assert_called_once()
            call_kwargs: dict[str, Any] = mock_send.call_args[1]
            assert call_kwargs["to_email"] == "requester@example.com"
            assert call_kwargs["correction_id"] == correction.id
            assert call_kwargs["status"] == CorrectionStatus.ACCEPTED

    @pytest.mark.asyncio
    async def test_sends_rejection_email_when_correction_rejected(
        self, db_session: AsyncSession
    ) -> None:
        """Test rejection email is sent when correction is rejected."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Email rejection test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check: FactCheck = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.95,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        admin: User = User(
            email="admin_reject@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            request_details="Change rating to FALSE.",
            status=CorrectionStatus.PENDING,
            requester_email="requester2@example.com",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Mock the email sending function
        with patch(
            "app.services.correction_application_service.send_correction_resolution_email"
        ) as mock_send:
            mock_send.return_value = True

            service: CorrectionApplicationService = CorrectionApplicationService(db_session)
            await service.reject_correction(
                correction_id=correction.id,
                reviewer_id=admin.id,
                resolution_notes="Our evidence still supports TRUE rating.",
            )

            # Assert rejection email was sent
            mock_send.assert_called_once()
            call_kwargs: dict[str, Any] = mock_send.call_args[1]
            assert call_kwargs["to_email"] == "requester2@example.com"
            assert call_kwargs["status"] == CorrectionStatus.REJECTED

    @pytest.mark.asyncio
    async def test_no_email_sent_for_anonymous_corrections(self, db_session: AsyncSession) -> None:
        """Test no email is sent for anonymous corrections (no requester_email)."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Anonymous email test", source="test")
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

        admin: User = User(
            email="admin_anon@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Anonymous fix request.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Fixed.",
            requester_email=None,  # Anonymous
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Mock the email sending function
        with patch(
            "app.services.correction_application_service.send_correction_resolution_email"
        ) as mock_send:
            service: CorrectionApplicationService = CorrectionApplicationService(db_session)
            await service.apply_correction(
                correction_id=correction.id,
                applied_by_id=admin.id,
                changes={"reasoning": "Fixed"},
                changes_summary="Anonymous correction applied",
            )

            # Assert email was NOT sent
            mock_send.assert_not_called()


# =============================================================================
# TEST CLASS: Validation and Edge Cases
# =============================================================================


class TestCorrectionApplicationValidation:
    """Tests for validation and edge cases."""

    @pytest.mark.asyncio
    async def test_cannot_apply_correction_to_pending_status(
        self, db_session: AsyncSession
    ) -> None:
        """Test cannot apply a correction that is still PENDING (not accepted)."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
            CorrectionNotAcceptedError,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Pending apply test", source="test")
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

        admin: User = User(
            email="admin_pending@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Still pending.",
            status=CorrectionStatus.PENDING,  # Not yet accepted
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        service: CorrectionApplicationService = CorrectionApplicationService(db_session)

        with pytest.raises(CorrectionNotAcceptedError):
            await service.apply_correction(
                correction_id=correction.id,
                applied_by_id=admin.id,
                changes={"reasoning": "Should fail"},
                changes_summary="Invalid",
            )

    @pytest.mark.asyncio
    async def test_cannot_apply_correction_twice(self, db_session: AsyncSession) -> None:
        """Test cannot apply the same correction twice."""
        from app.services.correction_application_service import (
            CorrectionAlreadyAppliedError,
            CorrectionApplicationService,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Double apply test", source="test")
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

        admin: User = User(
            email="admin_double@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Apply once test.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Approved.",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        service: CorrectionApplicationService = CorrectionApplicationService(db_session)

        # First application should succeed
        await service.apply_correction(
            correction_id=correction.id,
            applied_by_id=admin.id,
            changes={"reasoning": "First apply"},
            changes_summary="First",
        )

        # Second application should fail
        with pytest.raises(CorrectionAlreadyAppliedError):
            await service.apply_correction(
                correction_id=correction.id,
                applied_by_id=admin.id,
                changes={"reasoning": "Second apply"},
                changes_summary="Second - should fail",
            )

    @pytest.mark.asyncio
    async def test_changes_must_include_at_least_one_field(self, db_session: AsyncSession) -> None:
        """Test that changes dict must include at least one field to update."""
        from app.services.correction_application_service import (
            CorrectionApplicationService,
            ValidationError,
        )

        # Create prerequisite entities
        claim: Claim = Claim(content="Empty changes test", source="test")
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

        admin: User = User(
            email="admin_empty@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        correction: Correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            request_details="Empty changes test.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_notes="Approved.",
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        service: CorrectionApplicationService = CorrectionApplicationService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.apply_correction(
                correction_id=correction.id,
                applied_by_id=admin.id,
                changes={},  # Empty changes
                changes_summary="No changes",
            )

        assert "at least one field" in str(exc_info.value).lower()
