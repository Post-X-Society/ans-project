"""
Tests for PeerReview model - TDD approach: Write tests FIRST
Issue #63: Database Schema for Peer Review Tables
"""

import enum
from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole


class TestPeerReviewModel:
    """Tests for PeerReview model - tracks peer reviews on fact checks"""

    @pytest.mark.asyncio
    async def test_create_peer_review(self, db_session: AsyncSession) -> None:
        """Test creating a peer review with all required fields"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.peer_review import ApprovalStatus, PeerReview
        from app.models.user import User

        # Create prerequisite entities
        reviewer = User(
            email="peer_reviewer@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        claim = Claim(content="Test claim for peer review", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.95,
            reasoning="This is false based on evidence",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create peer review
        comments = "I have reviewed this fact check and agree with the verdict based on my independent analysis."
        peer_review = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer.id,
            approval_status=ApprovalStatus.APPROVED,
            comments=comments,
        )
        db_session.add(peer_review)
        await db_session.commit()
        await db_session.refresh(peer_review)

        assert peer_review.id is not None
        assert isinstance(peer_review.id, UUID)
        assert peer_review.fact_check_id == fact_check.id
        assert peer_review.reviewer_id == reviewer.id
        assert peer_review.approval_status == ApprovalStatus.APPROVED
        assert peer_review.comments == comments
        assert isinstance(peer_review.created_at, datetime)
        assert isinstance(peer_review.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_peer_review_approval_statuses(self, db_session: AsyncSession) -> None:
        """Test all approval status values"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.peer_review import ApprovalStatus, PeerReview
        from app.models.user import User

        reviewer = User(
            email="status_tester@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        claim = Claim(content="Status test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        # Test each approval status
        for status in [ApprovalStatus.PENDING, ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
            fact_check = FactCheck(
                claim_id=claim.id,
                verdict="true",
                confidence=0.9,
                reasoning=f"Test for {status.value}",
                sources=["https://example.com"],
            )
            db_session.add(fact_check)
            await db_session.commit()
            await db_session.refresh(fact_check)

            peer_review = PeerReview(
                fact_check_id=fact_check.id,
                reviewer_id=reviewer.id,
                approval_status=status,
                comments=f"Testing {status.value} status with detailed review comments.",
            )
            db_session.add(peer_review)
            await db_session.commit()
            await db_session.refresh(peer_review)

            assert peer_review.approval_status == status

    @pytest.mark.asyncio
    async def test_peer_review_fact_check_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between PeerReview and FactCheck"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.peer_review import ApprovalStatus, PeerReview
        from app.models.user import User

        reviewer = User(
            email="rel_test@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

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

        peer_review = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer.id,
            approval_status=ApprovalStatus.APPROVED,
            comments="Verified and approved after thorough peer review process.",
        )
        db_session.add(peer_review)
        await db_session.commit()

        # Verify relationship exists
        result = await db_session.execute(
            select(PeerReview).where(PeerReview.fact_check_id == fact_check.id)
        )
        loaded_review = result.scalar_one()
        assert loaded_review.fact_check_id == fact_check.id

    @pytest.mark.asyncio
    async def test_peer_review_reviewer_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between PeerReview and User (reviewer)"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.peer_review import ApprovalStatus, PeerReview
        from app.models.user import User

        reviewer = User(
            email="reviewer_rel@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
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
            verdict="partially_true",
            confidence=0.7,
            reasoning="Partially verified",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        peer_review = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer.id,
            approval_status=ApprovalStatus.PENDING,
            comments="Review is pending additional verification from the peer reviewer.",
        )
        db_session.add(peer_review)
        await db_session.commit()

        # Verify relationship
        result = await db_session.execute(
            select(PeerReview).where(PeerReview.reviewer_id == reviewer.id)
        )
        loaded_review = result.scalar_one()
        assert loaded_review.reviewer_id == reviewer.id

    @pytest.mark.asyncio
    async def test_peer_review_cascade_delete_via_orm(self, db_session: AsyncSession) -> None:
        """Test that peer reviews are deleted when fact_check is deleted (via ORM cascade)"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.peer_review import ApprovalStatus, PeerReview
        from app.models.user import User

        reviewer = User(
            email="cascade@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        claim = Claim(content="Cascade delete test", source="test")
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

        peer_review = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer.id,
            approval_status=ApprovalStatus.REJECTED,
            comments="This peer review will be cascade deleted when the fact check is removed.",
        )
        db_session.add(peer_review)
        await db_session.commit()
        await db_session.refresh(peer_review)

        # Load fact_check with its peer_reviews relationship to trigger ORM cascade
        await db_session.refresh(fact_check, ["peer_reviews"])

        review_id = peer_review.id

        # Delete fact check - ORM cascade="all, delete-orphan" should handle this
        await db_session.delete(fact_check)
        await db_session.commit()

        # Verify peer review was cascade deleted via ORM
        result = await db_session.execute(select(PeerReview).where(PeerReview.id == review_id))
        deleted_review = result.scalar_one_or_none()
        assert deleted_review is None

    @pytest.mark.asyncio
    async def test_peer_review_requires_fact_check_field(self, db_session: AsyncSession) -> None:
        """Test that peer review fact_check_id field is required"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.peer_review import ApprovalStatus, PeerReview
        from app.models.user import User

        reviewer = User(
            email="fk_test@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
        )
        db_session.add(reviewer)

        claim = Claim(content="FK test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(reviewer)
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

        # Test that fact_check_id is required by creating valid peer review
        peer_review = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer.id,
            approval_status=ApprovalStatus.APPROVED,
            comments="This tests that fact_check_id field is properly required.",
        )
        db_session.add(peer_review)
        await db_session.commit()
        await db_session.refresh(peer_review)

        # Verify the fact_check_id is set correctly
        assert peer_review.fact_check_id == fact_check.id
        assert peer_review.fact_check_id is not None

    @pytest.mark.asyncio
    async def test_peer_review_requires_reviewer_field(self, db_session: AsyncSession) -> None:
        """Test that peer review reviewer_id field is required"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.peer_review import ApprovalStatus, PeerReview
        from app.models.user import User

        reviewer = User(
            email="reviewer_fk@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
        )
        db_session.add(reviewer)

        claim = Claim(content="Reviewer FK test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(reviewer)
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

        # Test that reviewer_id is required by creating valid peer review
        peer_review = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer.id,
            approval_status=ApprovalStatus.APPROVED,
            comments="This tests that reviewer_id field is properly required.",
        )
        db_session.add(peer_review)
        await db_session.commit()
        await db_session.refresh(peer_review)

        # Verify the reviewer_id is set correctly
        assert peer_review.reviewer_id == reviewer.id
        assert peer_review.reviewer_id is not None

    @pytest.mark.asyncio
    async def test_peer_review_repr(self, db_session: AsyncSession) -> None:
        """Test string representation of PeerReview"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.peer_review import ApprovalStatus, PeerReview
        from app.models.user import User

        reviewer = User(
            email="repr@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
        )
        db_session.add(reviewer)
        claim = Claim(content="Repr test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(reviewer)
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

        peer_review = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer.id,
            approval_status=ApprovalStatus.APPROVED,
            comments="Testing the string representation of the PeerReview model object.",
        )
        db_session.add(peer_review)
        await db_session.commit()
        await db_session.refresh(peer_review)

        repr_str = repr(peer_review)
        assert "PeerReview" in repr_str
        assert str(peer_review.id) in repr_str
        assert "approved" in repr_str

    @pytest.mark.asyncio
    async def test_multiple_peer_reviews_for_same_fact_check(
        self, db_session: AsyncSession
    ) -> None:
        """Test that multiple peer reviews can exist for the same fact check"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.peer_review import ApprovalStatus, PeerReview
        from app.models.user import User

        reviewer1 = User(
            email="reviewer1@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
        )
        reviewer2 = User(
            email="reviewer2@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add_all([reviewer1, reviewer2])
        await db_session.commit()
        await db_session.refresh(reviewer1)
        await db_session.refresh(reviewer2)

        claim = Claim(content="Multiple reviews test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.5,
            reasoning="Needs multiple reviews",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create multiple peer reviews from different reviewers
        review1 = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer1.id,
            approval_status=ApprovalStatus.APPROVED,
            comments="First reviewer approves this fact check after detailed analysis.",
        )
        review2 = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer2.id,
            approval_status=ApprovalStatus.APPROVED,
            comments="Second reviewer also approves this fact check based on evidence.",
        )
        db_session.add_all([review1, review2])
        await db_session.commit()

        # Query all reviews for this fact check
        result = await db_session.execute(
            select(PeerReview).where(PeerReview.fact_check_id == fact_check.id)
        )
        all_reviews = result.scalars().all()
        assert len(all_reviews) == 2

    @pytest.mark.asyncio
    async def test_peer_review_with_nullable_comments(self, db_session: AsyncSession) -> None:
        """Test that peer review comments are nullable"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.peer_review import ApprovalStatus, PeerReview
        from app.models.user import User

        reviewer = User(
            email="null_comments@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
        )
        db_session.add(reviewer)
        claim = Claim(content="Null comments test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(reviewer)
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

        # Create peer review without comments
        peer_review = PeerReview(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer.id,
            approval_status=ApprovalStatus.APPROVED,
            comments=None,
        )
        db_session.add(peer_review)
        await db_session.commit()
        await db_session.refresh(peer_review)

        assert peer_review.comments is None


class TestApprovalStatusEnum:
    """Tests for ApprovalStatus enum values"""

    def test_approval_status_values(self) -> None:
        """Test that ApprovalStatus has the expected values"""
        from app.models.peer_review import ApprovalStatus

        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"

    def test_approval_status_is_string_enum(self) -> None:
        """Test that ApprovalStatus is a string enum"""
        from app.models.peer_review import ApprovalStatus

        assert issubclass(ApprovalStatus, enum.Enum)
        # Verify values are strings
        for status in ApprovalStatus:
            assert isinstance(status.value, str)
