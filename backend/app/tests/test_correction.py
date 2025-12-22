"""
Tests for Correction and CorrectionApplication models - TDD approach: Write tests FIRST
Issue #75: Database Schema for Corrections Tables
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole


class TestCorrectionModel:
    """Tests for Correction model - tracks correction requests for fact-checks"""

    @pytest.mark.asyncio
    async def test_create_correction_with_required_fields(self, db_session: AsyncSession) -> None:
        """Test creating a correction request with all required fields"""
        from app.models.claim import Claim
        from app.models.correction import Correction, CorrectionStatus, CorrectionType
        from app.models.fact_check import FactCheck

        # Create prerequisite entities
        claim = Claim(content="Test claim for correction", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.95,
            reasoning="This is false",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create correction request
        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            requester_email="requester@example.com",
            request_details="The rating is incorrect. New evidence shows the claim is actually true.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        assert correction.id is not None
        assert isinstance(correction.id, UUID)
        assert correction.fact_check_id == fact_check.id
        assert correction.correction_type == CorrectionType.SUBSTANTIAL
        assert correction.requester_email == "requester@example.com"
        assert "rating is incorrect" in correction.request_details
        assert correction.status == CorrectionStatus.PENDING
        assert correction.reviewed_by_id is None
        assert correction.reviewed_at is None
        assert correction.resolution_notes is None
        assert isinstance(correction.created_at, datetime)
        assert isinstance(correction.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_correction_type_enum_values(self, db_session: AsyncSession) -> None:
        """Test all CorrectionType enum values"""
        from app.models.claim import Claim
        from app.models.correction import Correction, CorrectionStatus, CorrectionType
        from app.models.fact_check import FactCheck

        claim = Claim(content="Enum test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Verified",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Test each correction type
        correction_types = [
            CorrectionType.MINOR,
            CorrectionType.UPDATE,
            CorrectionType.SUBSTANTIAL,
        ]

        for i, correction_type in enumerate(correction_types):
            correction = Correction(
                fact_check_id=fact_check.id,
                correction_type=correction_type,
                requester_email=f"test{i}@example.com",
                request_details=f"Test correction type: {correction_type.value}",
                status=CorrectionStatus.PENDING,
            )
            db_session.add(correction)

        await db_session.commit()

        # Verify all corrections were created
        result = await db_session.execute(
            select(Correction).where(Correction.fact_check_id == fact_check.id)
        )
        corrections = result.scalars().all()
        assert len(corrections) == 3

        types_found = {c.correction_type for c in corrections}
        assert CorrectionType.MINOR in types_found
        assert CorrectionType.UPDATE in types_found
        assert CorrectionType.SUBSTANTIAL in types_found

    @pytest.mark.asyncio
    async def test_correction_status_enum_values(self, db_session: AsyncSession) -> None:
        """Test all CorrectionStatus enum values"""
        from app.models.claim import Claim
        from app.models.correction import Correction, CorrectionStatus, CorrectionType
        from app.models.fact_check import FactCheck

        claim = Claim(content="Status enum test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.85,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Test each status
        statuses = [
            CorrectionStatus.PENDING,
            CorrectionStatus.ACCEPTED,
            CorrectionStatus.REJECTED,
        ]

        for i, status in enumerate(statuses):
            correction = Correction(
                fact_check_id=fact_check.id,
                correction_type=CorrectionType.UPDATE,
                requester_email=f"status{i}@example.com",
                request_details=f"Test correction status: {status.value}",
                status=status,
            )
            db_session.add(correction)

        await db_session.commit()

        result = await db_session.execute(
            select(Correction).where(Correction.fact_check_id == fact_check.id)
        )
        corrections = result.scalars().all()
        assert len(corrections) == 3

        statuses_found = {c.status for c in corrections}
        assert CorrectionStatus.PENDING in statuses_found
        assert CorrectionStatus.ACCEPTED in statuses_found
        assert CorrectionStatus.REJECTED in statuses_found

    @pytest.mark.asyncio
    async def test_correction_fact_check_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between Correction and FactCheck"""
        from app.models.claim import Claim
        from app.models.correction import Correction, CorrectionStatus, CorrectionType
        from app.models.fact_check import FactCheck

        claim = Claim(content="Relationship test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Verified",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            requester_email="rel@example.com",
            request_details="Testing fact check relationship.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add(correction)
        await db_session.commit()

        # Verify relationship
        result = await db_session.execute(
            select(Correction).where(Correction.fact_check_id == fact_check.id)
        )
        loaded_correction = result.scalar_one()
        assert loaded_correction.fact_check_id == fact_check.id

    @pytest.mark.asyncio
    async def test_correction_reviewer_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between Correction and User (reviewed_by)"""
        from app.models.claim import Claim
        from app.models.correction import Correction, CorrectionStatus, CorrectionType
        from app.models.fact_check import FactCheck
        from app.models.user import User

        reviewer = User(
            email="reviewer@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        claim = Claim(content="Reviewer relationship test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.8,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create correction with reviewer
        now = datetime.now(timezone.utc)
        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            requester_email="user@example.com",
            request_details="Needs review.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=reviewer.id,
            reviewed_at=now,
            resolution_notes="Reviewed and accepted the correction request.",
        )
        db_session.add(correction)
        await db_session.commit()

        result = await db_session.execute(
            select(Correction).where(Correction.reviewed_by_id == reviewer.id)
        )
        loaded_correction = result.scalar_one()
        assert loaded_correction.reviewed_by_id == reviewer.id
        assert loaded_correction.reviewed_at is not None
        assert loaded_correction.resolution_notes is not None
        assert "accepted" in loaded_correction.resolution_notes

    @pytest.mark.asyncio
    async def test_correction_sla_deadline(self, db_session: AsyncSession) -> None:
        """Test SLA deadline field for correction requests"""
        from app.models.claim import Claim
        from app.models.correction import Correction, CorrectionStatus, CorrectionType
        from app.models.fact_check import FactCheck

        claim = Claim(content="SLA test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create correction with SLA deadline (e.g., 7 days from now)
        sla_deadline = datetime.now(timezone.utc) + timedelta(days=7)
        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            requester_email="sla@example.com",
            request_details="Test SLA deadline tracking.",
            status=CorrectionStatus.PENDING,
            sla_deadline=sla_deadline,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        assert correction.sla_deadline is not None
        assert isinstance(correction.sla_deadline, datetime)

    @pytest.mark.asyncio
    async def test_correction_optional_requester_email(self, db_session: AsyncSession) -> None:
        """Test that requester_email is optional (anonymous corrections)"""
        from app.models.claim import Claim
        from app.models.correction import Correction, CorrectionStatus, CorrectionType
        from app.models.fact_check import FactCheck

        claim = Claim(content="Anonymous correction test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create correction without email (anonymous)
        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            requester_email=None,
            request_details="Anonymous correction request.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        assert correction.requester_email is None
        assert correction.id is not None

    @pytest.mark.asyncio
    async def test_correction_cascade_delete_via_orm(self, db_session: AsyncSession) -> None:
        """Test that corrections are deleted when fact_check is deleted"""
        from app.models.claim import Claim
        from app.models.correction import Correction, CorrectionStatus, CorrectionType
        from app.models.fact_check import FactCheck

        claim = Claim(content="Cascade delete test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            requester_email="cascade@example.com",
            request_details="This will be cascade deleted.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        correction_id = correction.id

        # Load fact_check with corrections relationship to trigger ORM cascade
        await db_session.refresh(fact_check, ["corrections"])

        # Delete fact check
        await db_session.delete(fact_check)
        await db_session.commit()

        # Verify correction was cascade deleted
        result = await db_session.execute(select(Correction).where(Correction.id == correction_id))
        deleted_correction = result.scalar_one_or_none()
        assert deleted_correction is None

    @pytest.mark.asyncio
    async def test_correction_repr(self, db_session: AsyncSession) -> None:
        """Test string representation of Correction"""
        from app.models.claim import Claim
        from app.models.correction import Correction, CorrectionStatus, CorrectionType
        from app.models.fact_check import FactCheck

        claim = Claim(content="Repr test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            requester_email="repr@example.com",
            request_details="Test repr.",
            status=CorrectionStatus.PENDING,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        repr_str = repr(correction)
        assert "Correction" in repr_str
        assert str(correction.id) in repr_str
        assert "substantial" in repr_str
        assert "pending" in repr_str

    @pytest.mark.asyncio
    async def test_multiple_corrections_for_same_fact_check(self, db_session: AsyncSession) -> None:
        """Test that multiple corrections can exist for the same fact check"""
        from app.models.claim import Claim
        from app.models.correction import Correction, CorrectionStatus, CorrectionType
        from app.models.fact_check import FactCheck

        claim = Claim(content="Multiple corrections test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
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
        corrections = [
            Correction(
                fact_check_id=fact_check.id,
                correction_type=CorrectionType.MINOR,
                requester_email="user1@example.com",
                request_details="First correction request.",
                status=CorrectionStatus.ACCEPTED,
            ),
            Correction(
                fact_check_id=fact_check.id,
                correction_type=CorrectionType.UPDATE,
                requester_email="user2@example.com",
                request_details="Second correction request.",
                status=CorrectionStatus.REJECTED,
            ),
            Correction(
                fact_check_id=fact_check.id,
                correction_type=CorrectionType.SUBSTANTIAL,
                requester_email="user3@example.com",
                request_details="Third correction request.",
                status=CorrectionStatus.PENDING,
            ),
        ]
        db_session.add_all(corrections)
        await db_session.commit()

        result = await db_session.execute(
            select(Correction).where(Correction.fact_check_id == fact_check.id)
        )
        all_corrections = result.scalars().all()
        assert len(all_corrections) == 3


class TestCorrectionApplicationModel:
    """Tests for CorrectionApplication model - tracks applied corrections with versioning"""

    @pytest.mark.asyncio
    async def test_create_correction_application(self, db_session: AsyncSession) -> None:
        """Test creating a correction application with all required fields"""
        from app.models.claim import Claim
        from app.models.correction import (
            Correction,
            CorrectionApplication,
            CorrectionStatus,
            CorrectionType,
        )
        from app.models.fact_check import FactCheck
        from app.models.user import User

        # Create prerequisite entities
        admin = User(
            email="admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        claim = Claim(content="Application test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.8,
            reasoning="Original reasoning",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            requester_email="requester@example.com",
            request_details="Rating needs to be changed.",
            status=CorrectionStatus.ACCEPTED,
            reviewed_by_id=admin.id,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Create correction application
        application = CorrectionApplication(
            correction_id=correction.id,
            applied_by_id=admin.id,
            version=1,
            changes_summary="Changed verdict from false to true based on new evidence.",
            previous_content={"verdict": "false", "reasoning": "Original reasoning"},
            new_content={"verdict": "true", "reasoning": "Updated with new evidence"},
            is_current=True,
        )
        db_session.add(application)
        await db_session.commit()
        await db_session.refresh(application)

        assert application.id is not None
        assert isinstance(application.id, UUID)
        assert application.correction_id == correction.id
        assert application.applied_by_id == admin.id
        assert application.version == 1
        assert "Changed verdict" in application.changes_summary
        assert application.previous_content["verdict"] == "false"
        assert application.new_content["verdict"] == "true"
        assert application.is_current is True
        assert isinstance(application.applied_at, datetime)
        assert isinstance(application.created_at, datetime)
        assert isinstance(application.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_correction_application_versioning(self, db_session: AsyncSession) -> None:
        """Test versioning support for correction applications"""
        from app.models.claim import Claim
        from app.models.correction import (
            Correction,
            CorrectionApplication,
            CorrectionStatus,
            CorrectionType,
        )
        from app.models.fact_check import FactCheck
        from app.models.user import User

        admin = User(
            email="version_admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        claim = Claim(content="Versioning test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.5,
            reasoning="Initial",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            requester_email="version@example.com",
            request_details="Update needed.",
            status=CorrectionStatus.ACCEPTED,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        # Create first version
        app_v1 = CorrectionApplication(
            correction_id=correction.id,
            applied_by_id=admin.id,
            version=1,
            changes_summary="First application of correction.",
            previous_content={"field": "old_value_1"},
            new_content={"field": "new_value_1"},
            is_current=True,
        )
        db_session.add(app_v1)
        await db_session.commit()

        # Create second version, mark first as not current
        app_v1.is_current = False
        app_v2 = CorrectionApplication(
            correction_id=correction.id,
            applied_by_id=admin.id,
            version=2,
            changes_summary="Second revision of correction.",
            previous_content={"field": "new_value_1"},
            new_content={"field": "new_value_2"},
            is_current=True,
        )
        db_session.add(app_v2)
        await db_session.commit()

        # Query for current application
        result = await db_session.execute(
            select(CorrectionApplication).where(
                CorrectionApplication.correction_id == correction.id,
                CorrectionApplication.is_current.is_(True),
            )
        )
        current_app = result.scalar_one()
        assert current_app.version == 2
        assert current_app.new_content["field"] == "new_value_2"

        # Query for all applications (history)
        result = await db_session.execute(
            select(CorrectionApplication)
            .where(CorrectionApplication.correction_id == correction.id)
            .order_by(CorrectionApplication.version)
        )
        all_apps = result.scalars().all()
        assert len(all_apps) == 2
        assert all_apps[0].version == 1
        assert all_apps[1].version == 2

    @pytest.mark.asyncio
    async def test_correction_application_correction_relationship(
        self, db_session: AsyncSession
    ) -> None:
        """Test relationship between CorrectionApplication and Correction"""
        from app.models.claim import Claim
        from app.models.correction import (
            Correction,
            CorrectionApplication,
            CorrectionStatus,
            CorrectionType,
        )
        from app.models.fact_check import FactCheck
        from app.models.user import User

        admin = User(
            email="rel_admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        claim = Claim(content="Rel test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            requester_email="rel@example.com",
            request_details="Minor fix needed.",
            status=CorrectionStatus.ACCEPTED,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        application = CorrectionApplication(
            correction_id=correction.id,
            applied_by_id=admin.id,
            version=1,
            changes_summary="Applied minor fix.",
            previous_content={},
            new_content={"fix": "applied"},
            is_current=True,
        )
        db_session.add(application)
        await db_session.commit()

        result = await db_session.execute(
            select(CorrectionApplication).where(
                CorrectionApplication.correction_id == correction.id
            )
        )
        loaded_app = result.scalar_one()
        assert loaded_app.correction_id == correction.id

    @pytest.mark.asyncio
    async def test_correction_application_user_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between CorrectionApplication and User (applied_by)"""
        from app.models.claim import Claim
        from app.models.correction import (
            Correction,
            CorrectionApplication,
            CorrectionStatus,
            CorrectionType,
        )
        from app.models.fact_check import FactCheck
        from app.models.user import User

        admin = User(
            email="user_rel@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        claim = Claim(content="User rel test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.UPDATE,
            requester_email="user@example.com",
            request_details="Update request.",
            status=CorrectionStatus.ACCEPTED,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        application = CorrectionApplication(
            correction_id=correction.id,
            applied_by_id=admin.id,
            version=1,
            changes_summary="Applied by admin.",
            previous_content={},
            new_content={},
            is_current=True,
        )
        db_session.add(application)
        await db_session.commit()

        result = await db_session.execute(
            select(CorrectionApplication).where(CorrectionApplication.applied_by_id == admin.id)
        )
        loaded_app = result.scalar_one()
        assert loaded_app.applied_by_id == admin.id

    @pytest.mark.asyncio
    async def test_correction_application_cascade_delete(self, db_session: AsyncSession) -> None:
        """Test that applications are deleted when correction is deleted"""
        from app.models.claim import Claim
        from app.models.correction import (
            Correction,
            CorrectionApplication,
            CorrectionStatus,
            CorrectionType,
        )
        from app.models.fact_check import FactCheck
        from app.models.user import User

        admin = User(
            email="cascade_admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        claim = Claim(content="Cascade test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            requester_email="cascade@example.com",
            request_details="Cascade test.",
            status=CorrectionStatus.ACCEPTED,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        application = CorrectionApplication(
            correction_id=correction.id,
            applied_by_id=admin.id,
            version=1,
            changes_summary="Will be cascade deleted.",
            previous_content={},
            new_content={},
            is_current=True,
        )
        db_session.add(application)
        await db_session.commit()
        await db_session.refresh(application)

        app_id = application.id

        # Load correction with applications to trigger ORM cascade
        await db_session.refresh(correction, ["applications"])

        # Delete correction
        await db_session.delete(correction)
        await db_session.commit()

        # Verify application was cascade deleted
        result = await db_session.execute(
            select(CorrectionApplication).where(CorrectionApplication.id == app_id)
        )
        deleted_app = result.scalar_one_or_none()
        assert deleted_app is None

    @pytest.mark.asyncio
    async def test_correction_application_repr(self, db_session: AsyncSession) -> None:
        """Test string representation of CorrectionApplication"""
        from app.models.claim import Claim
        from app.models.correction import (
            Correction,
            CorrectionApplication,
            CorrectionStatus,
            CorrectionType,
        )
        from app.models.fact_check import FactCheck
        from app.models.user import User

        admin = User(
            email="repr_admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        claim = Claim(content="Repr test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.SUBSTANTIAL,
            requester_email="repr@example.com",
            request_details="Repr test.",
            status=CorrectionStatus.ACCEPTED,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        application = CorrectionApplication(
            correction_id=correction.id,
            applied_by_id=admin.id,
            version=1,
            changes_summary="Test repr.",
            previous_content={},
            new_content={},
            is_current=True,
        )
        db_session.add(application)
        await db_session.commit()
        await db_session.refresh(application)

        repr_str = repr(application)
        assert "CorrectionApplication" in repr_str
        assert str(application.id) in repr_str
        assert "v1" in repr_str

    @pytest.mark.asyncio
    async def test_correction_application_applied_at_default(
        self, db_session: AsyncSession
    ) -> None:
        """Test that applied_at defaults to current timestamp"""
        from app.models.claim import Claim
        from app.models.correction import (
            Correction,
            CorrectionApplication,
            CorrectionStatus,
            CorrectionType,
        )
        from app.models.fact_check import FactCheck
        from app.models.user import User

        admin = User(
            email="time_admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        claim = Claim(content="Time test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="true",
            confidence=0.9,
            reasoning="Test",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        correction = Correction(
            fact_check_id=fact_check.id,
            correction_type=CorrectionType.MINOR,
            requester_email="time@example.com",
            request_details="Time test.",
            status=CorrectionStatus.ACCEPTED,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        application = CorrectionApplication(
            correction_id=correction.id,
            applied_by_id=admin.id,
            version=1,
            changes_summary="Testing applied_at default.",
            previous_content={},
            new_content={},
            is_current=True,
        )
        db_session.add(application)
        await db_session.commit()
        await db_session.refresh(application)

        assert application.applied_at is not None
        assert isinstance(application.applied_at, datetime)
