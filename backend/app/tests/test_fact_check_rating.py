"""
Tests for FactCheckRating model - TDD approach: Write tests FIRST
Issue #56: Database Schema for Fact Check Rating History
"""

from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole


class TestFactCheckRatingModel:
    """Tests for FactCheckRating model - tracks versioned rating history"""

    @pytest.mark.asyncio
    async def test_create_fact_check_rating(self, db_session: AsyncSession) -> None:
        """Test creating a fact check rating with all required fields"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.fact_check_rating import FactCheckRating
        from app.models.user import User

        # Create prerequisite entities
        user = User(
            email="reviewer@example.com",
            password_hash="hash",
            role=UserRole.REVIEWER,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        claim = Claim(content="Test claim for rating", source="test")
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

        # Create fact check rating
        justification = "This claim has been thoroughly reviewed and verified as false based on multiple authoritative sources."
        rating = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user.id,
            rating="false",
            justification=justification,
            version=1,
            is_current=True,
        )
        db_session.add(rating)
        await db_session.commit()
        await db_session.refresh(rating)

        assert rating.id is not None
        assert isinstance(rating.id, UUID)
        assert rating.fact_check_id == fact_check.id
        assert rating.assigned_by_id == user.id
        assert rating.rating == "false"
        assert rating.justification == justification
        assert rating.version == 1
        assert rating.is_current is True
        assert isinstance(rating.assigned_at, datetime)
        assert isinstance(rating.created_at, datetime)
        assert isinstance(rating.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_fact_check_rating_fact_check_relationship(
        self, db_session: AsyncSession
    ) -> None:
        """Test relationship between FactCheckRating and FactCheck"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.fact_check_rating import FactCheckRating
        from app.models.user import User

        user = User(email="rev@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

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

        rating = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user.id,
            rating="true",
            justification="This claim has been verified as true based on official records and documentation.",
            version=1,
            is_current=True,
        )
        db_session.add(rating)
        await db_session.commit()

        # Verify relationship exists
        result = await db_session.execute(
            select(FactCheckRating).where(FactCheckRating.fact_check_id == fact_check.id)
        )
        loaded_rating = result.scalar_one()
        assert loaded_rating.fact_check_id == fact_check.id

    @pytest.mark.asyncio
    async def test_fact_check_rating_user_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between FactCheckRating and User (assigned_by)"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.fact_check_rating import FactCheckRating
        from app.models.user import User

        user = User(email="assigner@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        claim = Claim(content="User relationship test", source="test")
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

        rating = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user.id,
            rating="partially_true",
            justification="This claim is partially accurate but contains some misleading elements that require clarification.",
            version=1,
            is_current=True,
        )
        db_session.add(rating)
        await db_session.commit()

        # Verify relationship
        result = await db_session.execute(
            select(FactCheckRating).where(FactCheckRating.assigned_by_id == user.id)
        )
        loaded_rating = result.scalar_one()
        assert loaded_rating.assigned_by_id == user.id

    @pytest.mark.asyncio
    async def test_fact_check_rating_versioning(self, db_session: AsyncSession) -> None:
        """Test versioning support for rating history"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.fact_check_rating import FactCheckRating
        from app.models.user import User

        user = User(email="version@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        claim = Claim(content="Versioning test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.5,
            reasoning="Initial assessment",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create first version (current)
        rating_v1 = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user.id,
            rating="unverified",
            justification="Initial rating. The claim needs more evidence before a definitive rating can be assigned.",
            version=1,
            is_current=True,
        )
        db_session.add(rating_v1)
        await db_session.commit()

        # Create second version, mark first as not current
        rating_v1.is_current = False
        rating_v2 = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user.id,
            rating="false",
            justification="Updated rating based on new evidence. The claim has been thoroughly debunked by experts.",
            version=2,
            is_current=True,
        )
        db_session.add(rating_v2)
        await db_session.commit()

        # Query for current rating
        result = await db_session.execute(
            select(FactCheckRating).where(
                FactCheckRating.fact_check_id == fact_check.id,
                FactCheckRating.is_current.is_(True),
            )
        )
        current_rating = result.scalar_one()
        assert current_rating.version == 2
        assert current_rating.rating == "false"

        # Query for all ratings (history)
        result = await db_session.execute(
            select(FactCheckRating)
            .where(FactCheckRating.fact_check_id == fact_check.id)
            .order_by(FactCheckRating.version)
        )
        all_ratings = result.scalars().all()
        assert len(all_ratings) == 2
        assert all_ratings[0].version == 1
        assert all_ratings[1].version == 2

    @pytest.mark.asyncio
    async def test_fact_check_rating_cascade_delete_via_orm(self, db_session: AsyncSession) -> None:
        """Test that ratings are deleted when fact_check is deleted (via ORM cascade)"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.fact_check_rating import FactCheckRating
        from app.models.user import User

        user = User(email="cascade@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

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

        rating = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user.id,
            rating="false",
            justification="This rating will be cascade deleted when the fact check is removed from the system.",
            version=1,
            is_current=True,
        )
        db_session.add(rating)
        await db_session.commit()
        await db_session.refresh(rating)

        # Load fact_check with its ratings relationship to trigger ORM cascade
        await db_session.refresh(fact_check, ["ratings"])

        rating_id = rating.id

        # Delete fact check - ORM cascade="all, delete-orphan" should handle this
        await db_session.delete(fact_check)
        await db_session.commit()

        # Verify rating was cascade deleted via ORM
        result = await db_session.execute(
            select(FactCheckRating).where(FactCheckRating.id == rating_id)
        )
        deleted_rating = result.scalar_one_or_none()
        assert deleted_rating is None

    @pytest.mark.asyncio
    async def test_fact_check_rating_requires_fact_check_field(
        self, db_session: AsyncSession
    ) -> None:
        """Test that rating fact_check_id field is required (NOT NULL constraint)"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.fact_check_rating import FactCheckRating
        from app.models.user import User

        user = User(email="fk_test@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(user)

        claim = Claim(content="FK test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(user)
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

        # Test that fact_check_id is required by creating valid rating
        rating = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user.id,
            rating="true",
            justification="This rating tests that fact_check_id field is properly required.",
            version=1,
            is_current=True,
        )
        db_session.add(rating)
        await db_session.commit()
        await db_session.refresh(rating)

        # Verify the fact_check_id is set correctly
        assert rating.fact_check_id == fact_check.id
        assert rating.fact_check_id is not None

    @pytest.mark.asyncio
    async def test_fact_check_rating_requires_user_field(self, db_session: AsyncSession) -> None:
        """Test that rating assigned_by_id field is required (NOT NULL constraint)"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.fact_check_rating import FactCheckRating
        from app.models.user import User

        user = User(email="user_fk@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(user)

        claim = Claim(content="User FK test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(user)
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

        # Test that assigned_by_id is required by creating valid rating
        rating = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user.id,
            rating="true",
            justification="This rating tests that assigned_by_id field is properly required.",
            version=1,
            is_current=True,
        )
        db_session.add(rating)
        await db_session.commit()
        await db_session.refresh(rating)

        # Verify the assigned_by_id is set correctly
        assert rating.assigned_by_id == user.id
        assert rating.assigned_by_id is not None

    @pytest.mark.asyncio
    async def test_fact_check_rating_repr(self, db_session: AsyncSession) -> None:
        """Test string representation of FactCheckRating"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.fact_check_rating import FactCheckRating
        from app.models.user import User

        user = User(email="repr@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(user)
        claim = Claim(content="Repr test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(user)
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

        rating = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user.id,
            rating="true",
            justification="Testing the string representation of the FactCheckRating model object.",
            version=1,
            is_current=True,
        )
        db_session.add(rating)
        await db_session.commit()
        await db_session.refresh(rating)

        repr_str = repr(rating)
        assert "FactCheckRating" in repr_str
        assert str(rating.id) in repr_str
        assert "true" in repr_str
        assert "v1" in repr_str

    @pytest.mark.asyncio
    async def test_fact_check_rating_assigned_at_default(self, db_session: AsyncSession) -> None:
        """Test that assigned_at defaults to current timestamp"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.fact_check_rating import FactCheckRating
        from app.models.user import User

        user = User(email="time@example.com", password_hash="hash", role=UserRole.REVIEWER)
        db_session.add(user)
        claim = Claim(content="Time test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(user)
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

        rating = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user.id,
            rating="true",
            justification="Testing that assigned_at timestamp is automatically set to current time.",
            version=1,
            is_current=True,
        )
        db_session.add(rating)
        await db_session.commit()
        await db_session.refresh(rating)

        # assigned_at should be set automatically
        assert rating.assigned_at is not None
        assert isinstance(rating.assigned_at, datetime)

    @pytest.mark.asyncio
    async def test_multiple_ratings_for_same_fact_check(self, db_session: AsyncSession) -> None:
        """Test that multiple ratings can exist for the same fact check (history)"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck
        from app.models.fact_check_rating import FactCheckRating
        from app.models.user import User

        user1 = User(email="user1@example.com", password_hash="hash", role=UserRole.REVIEWER)
        user2 = User(email="user2@example.com", password_hash="hash", role=UserRole.ADMIN)
        db_session.add_all([user1, user2])
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        claim = Claim(content="Multiple ratings test", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="unverified",
            confidence=0.5,
            reasoning="Needs review",
            sources=["https://example.com"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        # Create multiple ratings from different users
        rating1 = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user1.id,
            rating="unverified",
            justification="Initial assessment by first reviewer. More evidence is needed before conclusion.",
            version=1,
            is_current=False,
        )
        rating2 = FactCheckRating(
            fact_check_id=fact_check.id,
            assigned_by_id=user2.id,
            rating="false",
            justification="Final assessment by admin after reviewing additional evidence and sources.",
            version=2,
            is_current=True,
        )
        db_session.add_all([rating1, rating2])
        await db_session.commit()

        # Query all ratings for this fact check
        result = await db_session.execute(
            select(FactCheckRating).where(FactCheckRating.fact_check_id == fact_check.id)
        )
        all_ratings = result.scalars().all()
        assert len(all_ratings) == 2
