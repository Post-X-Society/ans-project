"""
Tests for database models - TDD approach: Write tests FIRST
"""
import pytest
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Models will be imported once they're created
# from app.models.user import User
# from app.models.submission import Submission
# from app.models.claim import Claim
# from app.models.fact_check import FactCheck
# from app.models.volunteer import Volunteer


class TestUserModel:
    """Tests for User model"""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession) -> None:
        """Test creating a user with all required fields"""
        from app.models.user import User

        user = User(
            email="test@example.com",
            password_hash="hashed_password_here",
            role="user",
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, UUID)
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_here"
        assert user.role == "user"
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_user_email_unique(self, db_session: AsyncSession) -> None:
        """Test that user email must be unique"""
        from app.models.user import User
        from sqlalchemy.exc import IntegrityError

        user1 = User(email="test@example.com", password_hash="hash1", role="user")
        db_session.add(user1)
        await db_session.commit()

        user2 = User(email="test@example.com", password_hash="hash2", role="user")
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_role_validation(self, db_session: AsyncSession) -> None:
        """Test that user role must be valid enum"""
        from app.models.user import User

        # Valid roles: user, volunteer, admin
        user = User(email="admin@example.com", password_hash="hash", role="admin")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.role == "admin"


class TestSubmissionModel:
    """Tests for Submission model"""

    @pytest.mark.asyncio
    async def test_create_submission(self, db_session: AsyncSession) -> None:
        """Test creating a submission"""
        from app.models.user import User
        from app.models.submission import Submission

        # Create a user first
        user = User(email="user@example.com", password_hash="hash", role="user")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create submission
        submission = Submission(
            user_id=user.id,
            content="Is this claim true?",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        assert submission.id is not None
        assert submission.user_id == user.id
        assert submission.content == "Is this claim true?"
        assert submission.submission_type == "text"
        assert submission.status == "pending"
        assert isinstance(submission.created_at, datetime)

    @pytest.mark.asyncio
    async def test_submission_user_relationship(self, db_session: AsyncSession) -> None:
        """Test that submission has relationship to user"""
        from app.models.user import User
        from app.models.submission import Submission

        user = User(email="user@example.com", password_hash="hash", role="user")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        submission = Submission(
            user_id=user.id,
            content="Test content",
            submission_type="text",
            status="pending",
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)

        # Load with relationship
        result = await db_session.execute(select(Submission).where(Submission.id == submission.id))
        loaded_submission = result.scalar_one()

        assert loaded_submission.user_id == user.id


class TestClaimModel:
    """Tests for Claim model with pgvector support"""

    @pytest.mark.asyncio
    async def test_create_claim(self, db_session: AsyncSession) -> None:
        """Test creating a claim with text content"""
        from app.models.claim import Claim

        claim = Claim(
            content="The earth is flat",
            source="user_submission",
        )
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        assert claim.id is not None
        assert claim.content == "The earth is flat"
        assert claim.source == "user_submission"
        assert claim.embedding is None  # Initially no embedding
        assert isinstance(claim.created_at, datetime)

    @pytest.mark.asyncio
    async def test_claim_with_embedding(self, db_session: AsyncSession) -> None:
        """Test creating a claim with vector embedding"""
        from app.models.claim import Claim

        # Create a sample embedding (1536 dimensions for text-embedding-3-small)
        sample_embedding = [0.1] * 1536

        claim = Claim(
            content="Test claim",
            source="test",
            embedding=sample_embedding,
        )
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        assert claim.embedding is not None
        assert len(claim.embedding) == 1536


class TestFactCheckModel:
    """Tests for FactCheck model"""

    @pytest.mark.asyncio
    async def test_create_fact_check(self, db_session: AsyncSession) -> None:
        """Test creating a fact check"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck

        # Create claim first
        claim = Claim(content="Test claim", source="test")
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        # Create fact check
        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="false",
            confidence=0.95,
            reasoning="This has been debunked by multiple sources",
            sources=["https://example.com/fact1", "https://example.com/fact2"],
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)

        assert fact_check.id is not None
        assert fact_check.claim_id == claim.id
        assert fact_check.verdict == "false"
        assert fact_check.confidence == 0.95
        assert fact_check.reasoning == "This has been debunked by multiple sources"
        assert len(fact_check.sources) == 2

    @pytest.mark.asyncio
    async def test_fact_check_claim_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between fact check and claim"""
        from app.models.claim import Claim
        from app.models.fact_check import FactCheck

        claim = Claim(content="Test claim", source="test")
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

        # Verify relationship
        result = await db_session.execute(select(FactCheck).where(FactCheck.claim_id == claim.id))
        loaded_fc = result.scalar_one()

        assert loaded_fc.claim_id == claim.id


class TestVolunteerModel:
    """Tests for Volunteer model"""

    @pytest.mark.asyncio
    async def test_create_volunteer(self, db_session: AsyncSession) -> None:
        """Test creating a volunteer"""
        from app.models.user import User
        from app.models.volunteer import Volunteer

        # Create user first
        user = User(email="volunteer@example.com", password_hash="hash", role="volunteer")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create volunteer profile
        volunteer = Volunteer(
            user_id=user.id,
            score=100.0,
            verified_count=10,
            accuracy_rate=0.95,
        )
        db_session.add(volunteer)
        await db_session.commit()
        await db_session.refresh(volunteer)

        assert volunteer.id is not None
        assert volunteer.user_id == user.id
        assert volunteer.score == 100.0
        assert volunteer.verified_count == 10
        assert volunteer.accuracy_rate == 0.95

    @pytest.mark.asyncio
    async def test_volunteer_user_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between volunteer and user"""
        from app.models.user import User
        from app.models.volunteer import Volunteer

        user = User(email="vol@example.com", password_hash="hash", role="volunteer")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        volunteer = Volunteer(
            user_id=user.id,
            score=50.0,
            verified_count=5,
            accuracy_rate=0.8,
        )
        db_session.add(volunteer)
        await db_session.commit()

        # Verify relationship
        result = await db_session.execute(select(Volunteer).where(Volunteer.user_id == user.id))
        loaded_vol = result.scalar_one()

        assert loaded_vol.user_id == user.id
