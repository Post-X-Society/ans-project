"""
Tests for PeerReviewService Consensus Logic - TDD approach: Write tests FIRST
Issue #65: Backend Peer Review Consensus Logic

This module tests:
1. submit_peer_review() - Submit approval/rejection decisions
2. check_consensus() - Check for unanimous approval requirement
3. Self-review prevention - Prevent authors from reviewing their own fact-checks
4. 7-day timeout with automatic escalation
5. Reviewer notifications - Email alerts for pending reviews
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.fact_check import FactCheck
from app.models.peer_review import ApprovalStatus, PeerReview
from app.models.user import User, UserRole

# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing."""
    user = User(
        email="admin@test.com",
        password_hash="hashed",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def reviewer_user(db_session: AsyncSession) -> User:
    """Create a reviewer user for testing."""
    user = User(
        email="reviewer@test.com",
        password_hash="hashed",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def second_reviewer(db_session: AsyncSession) -> User:
    """Create a second reviewer user for testing consensus."""
    user = User(
        email="reviewer2@test.com",
        password_hash="hashed",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def third_reviewer(db_session: AsyncSession) -> User:
    """Create a third reviewer user for testing multiple reviews."""
    user = User(
        email="reviewer3@test.com",
        password_hash="hashed",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_claim(db_session: AsyncSession) -> Claim:
    """Create a sample claim for testing."""
    claim = Claim(
        content="Test claim for peer review consensus",
        source="test_source",
    )
    db_session.add(claim)
    await db_session.commit()
    await db_session.refresh(claim)
    return claim


@pytest.fixture
async def sample_fact_check(
    db_session: AsyncSession,
    sample_claim: Claim,
) -> FactCheck:
    """Create a sample fact check for testing peer reviews."""
    fact_check = FactCheck(
        claim_id=sample_claim.id,
        verdict="false",
        confidence=0.85,
        reasoning="Test reasoning for fact check",
        sources=["https://source1.com", "https://source2.com"],
        sources_count=2,
    )
    db_session.add(fact_check)
    await db_session.commit()
    await db_session.refresh(fact_check)
    return fact_check


# ==============================================================================
# TEST CLASS: Submit Peer Review
# ==============================================================================


class TestSubmitPeerReview:
    """Tests for submit_peer_review() functionality."""

    @pytest.mark.asyncio
    async def test_submit_peer_review_creates_review(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
    ) -> None:
        """Test that submitting a peer review creates a new PeerReview record."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)
        review = await service.submit_peer_review(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approved=True,
            comments="Looks good to me!",
        )

        assert review is not None
        assert review.fact_check_id == sample_fact_check.id
        assert review.reviewer_id == reviewer_user.id
        assert review.approval_status == ApprovalStatus.APPROVED
        assert review.comments == "Looks good to me!"

    @pytest.mark.asyncio
    async def test_submit_peer_review_rejected(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
    ) -> None:
        """Test that submitting a rejection creates a REJECTED status."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)
        review = await service.submit_peer_review(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approved=False,
            comments="Need more evidence for this claim.",
        )

        assert review is not None
        assert review.approval_status == ApprovalStatus.REJECTED
        assert review.comments is not None and "more evidence" in review.comments

    @pytest.mark.asyncio
    async def test_submit_peer_review_updates_existing(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
    ) -> None:
        """Test that submitting again updates the existing review."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)

        # First submission - reject
        review1 = await service.submit_peer_review(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approved=False,
            comments="Initial rejection",
        )

        # Second submission - approve (reviewer changed their mind)
        review2 = await service.submit_peer_review(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approved=True,
            comments="After further review, I approve",
        )

        # Should be the same record, updated
        assert review1.id == review2.id
        assert review2.approval_status == ApprovalStatus.APPROVED
        assert review2.comments == "After further review, I approve"

    @pytest.mark.asyncio
    async def test_submit_peer_review_invalid_fact_check(
        self,
        db_session: AsyncSession,
        reviewer_user: User,
    ) -> None:
        """Test that submitting for non-existent fact check raises error."""
        from app.services.peer_review_service import (
            PeerReviewNotFoundError,
            PeerReviewService,
        )

        service = PeerReviewService(db_session)
        fake_fact_check_id = uuid4()

        with pytest.raises(PeerReviewNotFoundError):
            await service.submit_peer_review(
                fact_check_id=fake_fact_check_id,
                reviewer_id=reviewer_user.id,
                approved=True,
                comments="This should fail",
            )

    @pytest.mark.asyncio
    async def test_submit_peer_review_comments_optional(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
    ) -> None:
        """Test that comments are optional when submitting review."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)
        review = await service.submit_peer_review(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approved=True,
            comments=None,
        )

        assert review is not None
        assert review.comments is None


# ==============================================================================
# TEST CLASS: Check Consensus (Unanimous Approval)
# ==============================================================================


class TestCheckConsensus:
    """Tests for check_consensus() functionality - unanimous approval requirement."""

    @pytest.mark.asyncio
    async def test_consensus_reached_with_all_approved(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
        second_reviewer: User,
    ) -> None:
        """Test consensus is reached when all reviews are approved."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)

        # Both reviewers approve
        await service.submit_peer_review(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approved=True,
            comments="Approved",
        )
        await service.submit_peer_review(
            fact_check_id=sample_fact_check.id,
            reviewer_id=second_reviewer.id,
            approved=True,
            comments="Also approved",
        )

        result = await service.check_consensus(sample_fact_check.id)

        assert result.consensus_reached is True
        assert result.approved is True
        assert result.total_reviews == 2
        assert result.approved_count == 2
        assert result.rejected_count == 0
        assert result.pending_count == 0

    @pytest.mark.asyncio
    async def test_no_consensus_with_one_rejection(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
        second_reviewer: User,
    ) -> None:
        """Test consensus is NOT reached if even one review is rejected."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)

        # One approves, one rejects
        await service.submit_peer_review(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approved=True,
            comments="Approved",
        )
        await service.submit_peer_review(
            fact_check_id=sample_fact_check.id,
            reviewer_id=second_reviewer.id,
            approved=False,
            comments="I disagree with the verdict",
        )

        result = await service.check_consensus(sample_fact_check.id)

        assert result.consensus_reached is True  # Decision made, but rejected
        assert result.approved is False
        assert result.approved_count == 1
        assert result.rejected_count == 1

    @pytest.mark.asyncio
    async def test_no_consensus_with_pending_reviews(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
        second_reviewer: User,
    ) -> None:
        """Test consensus is NOT reached if reviews are still pending."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)

        # Only one reviewer has submitted
        await service.submit_peer_review(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approved=True,
            comments="Approved",
        )

        # Create a pending review for the second reviewer
        pending_review = PeerReview(
            fact_check_id=sample_fact_check.id,
            reviewer_id=second_reviewer.id,
            approval_status=ApprovalStatus.PENDING,
        )
        db_session.add(pending_review)
        await db_session.commit()

        result = await service.check_consensus(sample_fact_check.id)

        assert result.consensus_reached is False
        assert result.pending_count == 1
        assert result.approved_count == 1

    @pytest.mark.asyncio
    async def test_no_reviews_returns_no_consensus(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
    ) -> None:
        """Test that fact check with no reviews has no consensus."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)
        result = await service.check_consensus(sample_fact_check.id)

        assert result.consensus_reached is False
        assert result.total_reviews == 0

    @pytest.mark.asyncio
    async def test_consensus_requires_minimum_reviewers(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
    ) -> None:
        """Test that consensus requires minimum number of reviewers (at least 2)."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)

        # Only one reviewer approves
        await service.submit_peer_review(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approved=True,
            comments="Approved",
        )

        result = await service.check_consensus(sample_fact_check.id, min_reviewers=2)

        assert result.consensus_reached is False
        assert result.approved_count == 1
        assert result.needs_more_reviewers is True


# ==============================================================================
# TEST CLASS: Self-Review Prevention
# ==============================================================================


class TestSelfReviewPrevention:
    """Tests for self-review prevention mechanism."""

    @pytest.mark.asyncio
    async def test_cannot_review_own_fact_check(
        self,
        db_session: AsyncSession,
        sample_claim: Claim,
        reviewer_user: User,
    ) -> None:
        """Test that a user cannot review a fact check they authored."""
        from app.services.peer_review_service import (
            PeerReviewService,
            SelfReviewNotAllowedError,
        )

        # Create fact check authored by the reviewer (simulated via draft)
        # We need to link the reviewer as the author
        fact_check = FactCheck(
            claim_id=sample_claim.id,
            verdict="false",
            confidence=0.85,
            reasoning="Test reasoning",
            sources=["https://source1.com"],
            sources_count=1,
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        service = PeerReviewService(db_session)

        # Try to review with author_id check
        with pytest.raises(SelfReviewNotAllowedError):
            await service.submit_peer_review(
                fact_check_id=fact_check.id,
                reviewer_id=reviewer_user.id,
                approved=True,
                comments="Trying to approve my own work",
                author_id=reviewer_user.id,  # Same user as reviewer
            )

    @pytest.mark.asyncio
    async def test_can_review_other_fact_check(
        self,
        db_session: AsyncSession,
        sample_claim: Claim,
        reviewer_user: User,
        admin_user: User,
    ) -> None:
        """Test that a user CAN review a fact check authored by someone else."""
        from app.services.peer_review_service import PeerReviewService

        # Create fact check authored by admin
        fact_check = FactCheck(
            claim_id=sample_claim.id,
            verdict="false",
            confidence=0.85,
            reasoning="Test reasoning",
            sources=["https://source1.com"],
            sources_count=1,
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        service = PeerReviewService(db_session)

        # Different user (reviewer) reviews admin's fact check
        review = await service.submit_peer_review(
            fact_check_id=fact_check.id,
            reviewer_id=reviewer_user.id,
            approved=True,
            comments="Good work!",
            author_id=admin_user.id,  # Author is different from reviewer
        )

        assert review is not None
        assert review.reviewer_id == reviewer_user.id


# ==============================================================================
# TEST CLASS: 7-Day Timeout with Escalation
# ==============================================================================


class TestTimeoutAndEscalation:
    """Tests for 7-day timeout with automatic escalation."""

    @pytest.mark.asyncio
    async def test_get_overdue_reviews_after_7_days(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
    ) -> None:
        """Test identifying reviews that are overdue (pending > 7 days)."""
        from app.services.peer_review_service import PeerReviewService

        # Create an old pending review (8 days ago)
        old_review = PeerReview(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approval_status=ApprovalStatus.PENDING,
        )
        db_session.add(old_review)
        await db_session.commit()
        await db_session.refresh(old_review)

        # Manually set created_at to 8 days ago
        old_review.created_at = datetime.now(timezone.utc) - timedelta(days=8)
        await db_session.commit()

        service = PeerReviewService(db_session)
        overdue = await service.get_overdue_reviews(days=7)

        assert len(overdue) == 1
        assert overdue[0].id == old_review.id

    @pytest.mark.asyncio
    async def test_no_overdue_reviews_within_7_days(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
    ) -> None:
        """Test that recent pending reviews are not marked as overdue."""
        from app.services.peer_review_service import PeerReviewService

        # Create a recent pending review (1 day ago)
        recent_review = PeerReview(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approval_status=ApprovalStatus.PENDING,
        )
        db_session.add(recent_review)
        await db_session.commit()

        service = PeerReviewService(db_session)
        overdue = await service.get_overdue_reviews(days=7)

        assert len(overdue) == 0

    @pytest.mark.asyncio
    async def test_completed_reviews_not_overdue(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
    ) -> None:
        """Test that completed reviews are never marked as overdue."""
        from app.services.peer_review_service import PeerReviewService

        # Create an old but completed review
        completed_review = PeerReview(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approval_status=ApprovalStatus.APPROVED,
        )
        db_session.add(completed_review)
        await db_session.commit()
        await db_session.refresh(completed_review)

        # Set created_at to 30 days ago
        completed_review.created_at = datetime.now(timezone.utc) - timedelta(days=30)
        await db_session.commit()

        service = PeerReviewService(db_session)
        overdue = await service.get_overdue_reviews(days=7)

        assert len(overdue) == 0

    @pytest.mark.asyncio
    async def test_escalate_overdue_review(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
        admin_user: User,
    ) -> None:
        """Test that overdue reviews can be escalated to admin."""
        from app.services.peer_review_service import PeerReviewService

        # Create an overdue pending review
        overdue_review = PeerReview(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approval_status=ApprovalStatus.PENDING,
        )
        db_session.add(overdue_review)
        await db_session.commit()
        await db_session.refresh(overdue_review)

        overdue_review.created_at = datetime.now(timezone.utc) - timedelta(days=8)
        await db_session.commit()

        service = PeerReviewService(db_session)
        result = await service.escalate_overdue_review(
            review_id=overdue_review.id,
            escalate_to_id=admin_user.id,
            reason="Review overdue by 8 days",
        )

        assert result.escalated is True
        assert result.escalated_to_id == admin_user.id

    @pytest.mark.asyncio
    async def test_bulk_escalate_overdue_reviews(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
        second_reviewer: User,
        admin_user: User,
    ) -> None:
        """Test bulk escalation of all overdue reviews."""
        from app.services.peer_review_service import PeerReviewService

        # Create multiple overdue reviews
        for reviewer in [reviewer_user, second_reviewer]:
            review = PeerReview(
                fact_check_id=sample_fact_check.id,
                reviewer_id=reviewer.id,
                approval_status=ApprovalStatus.PENDING,
            )
            db_session.add(review)

        await db_session.commit()

        # Update created_at for both
        from sqlalchemy import update

        await db_session.execute(
            update(PeerReview).values(created_at=datetime.now(timezone.utc) - timedelta(days=10))
        )
        await db_session.commit()

        service = PeerReviewService(db_session)
        results = await service.bulk_escalate_overdue(
            escalate_to_id=admin_user.id,
            days=7,
        )

        assert results.escalated_count == 2
        assert results.failed_count == 0


# ==============================================================================
# TEST CLASS: Reviewer Notifications
# ==============================================================================


class TestReviewerNotifications:
    """Tests for sending notifications to pending reviewers."""

    @pytest.mark.asyncio
    async def test_send_pending_review_notification(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
    ) -> None:
        """Test sending notification for a pending review."""
        from unittest.mock import MagicMock, patch

        from app.services.peer_review_service import PeerReviewService

        # Create pending review
        pending_review = PeerReview(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approval_status=ApprovalStatus.PENDING,
        )
        db_session.add(pending_review)
        await db_session.commit()
        await db_session.refresh(pending_review)

        # Mock the EmailService to simulate successful email sending
        with patch("app.services.peer_review_service.EmailService") as mock_email_class:
            mock_email_instance = MagicMock()
            mock_email_instance.send_email.return_value = True
            mock_email_class.return_value = mock_email_instance

            service = PeerReviewService(db_session)
            result = await service.send_pending_review_notification(
                review_id=pending_review.id,
            )

        assert result.attempted is True
        assert result.sent is True
        assert result.reviewer_email == reviewer_user.email

    @pytest.mark.asyncio
    async def test_notify_all_pending_reviewers(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
        second_reviewer: User,
    ) -> None:
        """Test notifying all pending reviewers for a fact check."""
        from unittest.mock import MagicMock, patch

        from app.services.peer_review_service import PeerReviewService

        # Create multiple pending reviews
        for reviewer in [reviewer_user, second_reviewer]:
            review = PeerReview(
                fact_check_id=sample_fact_check.id,
                reviewer_id=reviewer.id,
                approval_status=ApprovalStatus.PENDING,
            )
            db_session.add(review)

        await db_session.commit()

        # Mock the EmailService to simulate successful email sending
        with patch("app.services.peer_review_service.EmailService") as mock_email_class:
            mock_email_instance = MagicMock()
            mock_email_instance.send_email.return_value = True
            mock_email_class.return_value = mock_email_instance

            service = PeerReviewService(db_session)
            results = await service.notify_pending_reviewers(
                fact_check_id=sample_fact_check.id,
            )

        assert results.notification_count == 2
        assert results.sent_count == 2
        assert reviewer_user.email in results.notified_emails
        assert second_reviewer.email in results.notified_emails

    @pytest.mark.asyncio
    async def test_no_notification_for_completed_reviews(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
    ) -> None:
        """Test that completed reviews don't get notifications."""
        from app.services.peer_review_service import PeerReviewService

        # Create completed review
        completed_review = PeerReview(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approval_status=ApprovalStatus.APPROVED,
        )
        db_session.add(completed_review)
        await db_session.commit()

        service = PeerReviewService(db_session)
        results = await service.notify_pending_reviewers(
            fact_check_id=sample_fact_check.id,
        )

        assert results.notification_count == 0


# ==============================================================================
# TEST CLASS: Assign Reviewers
# ==============================================================================


class TestAssignReviewers:
    """Tests for assigning reviewers to a fact check."""

    @pytest.mark.asyncio
    async def test_assign_reviewers_to_fact_check(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
        second_reviewer: User,
    ) -> None:
        """Test assigning multiple reviewers creates pending reviews."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)
        reviews = await service.assign_reviewers(
            fact_check_id=sample_fact_check.id,
            reviewer_ids=[reviewer_user.id, second_reviewer.id],
        )

        assert len(reviews) == 2
        for review in reviews:
            assert review.approval_status == ApprovalStatus.PENDING
            assert review.fact_check_id == sample_fact_check.id

    @pytest.mark.asyncio
    async def test_assign_reviewers_prevents_duplicates(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
    ) -> None:
        """Test that assigning the same reviewer twice doesn't create duplicates."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)

        # First assignment
        await service.assign_reviewers(
            fact_check_id=sample_fact_check.id,
            reviewer_ids=[reviewer_user.id],
        )

        # Second assignment of same reviewer
        reviews = await service.assign_reviewers(
            fact_check_id=sample_fact_check.id,
            reviewer_ids=[reviewer_user.id],
        )

        # Should return the existing review, not create duplicate
        assert len(reviews) == 1


# ==============================================================================
# TEST CLASS: Get Reviews for Fact Check
# ==============================================================================


class TestGetReviewsForFactCheck:
    """Tests for retrieving all peer reviews for a fact check."""

    @pytest.mark.asyncio
    async def test_get_reviews_for_fact_check(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
        reviewer_user: User,
        second_reviewer: User,
    ) -> None:
        """Test retrieving all reviews for a fact check."""
        from app.services.peer_review_service import PeerReviewService

        # Create reviews
        review1 = PeerReview(
            fact_check_id=sample_fact_check.id,
            reviewer_id=reviewer_user.id,
            approval_status=ApprovalStatus.APPROVED,
            comments="Good work",
        )
        review2 = PeerReview(
            fact_check_id=sample_fact_check.id,
            reviewer_id=second_reviewer.id,
            approval_status=ApprovalStatus.PENDING,
        )
        db_session.add_all([review1, review2])
        await db_session.commit()

        service = PeerReviewService(db_session)
        reviews = await service.get_reviews_for_fact_check(sample_fact_check.id)

        assert len(reviews) == 2

    @pytest.mark.asyncio
    async def test_get_reviews_empty_for_new_fact_check(
        self,
        db_session: AsyncSession,
        sample_fact_check: FactCheck,
    ) -> None:
        """Test that new fact check has no reviews."""
        from app.services.peer_review_service import PeerReviewService

        service = PeerReviewService(db_session)
        reviews = await service.get_reviews_for_fact_check(sample_fact_check.id)

        assert len(reviews) == 0
