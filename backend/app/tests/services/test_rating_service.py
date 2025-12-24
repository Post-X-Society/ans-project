"""
Unit tests for Rating Service - TDD approach.

Issue #58: Backend: Rating System Service (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine
ADR 0005: EFCSN Compliance Architecture

Required Test Cases:
1. First version creation
2. Version incrementing behavior
3. Justification validation requirements
4. Rating history retrieval
5. Latest rating retrieval
6. Permission-based access control
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.fact_check import FactCheck
from app.models.fact_check_rating import FactCheckRating
from app.models.user import User, UserRole
from app.schemas.rating import FactCheckRatingValue, RatingCreate
from app.services.rating_service import (
    RatingPermissionError,
    RatingValidationError,
    assign_rating,
    get_current_rating,
    get_rating_history,
)
from app.tests.helpers import normalize_dt


class TestRatingService:
    """Tests for the Rating Service following TDD approach."""

    # ========================================================================
    # Helper methods to create test fixtures
    # ========================================================================

    async def _create_test_user(
        self,
        db_session: AsyncSession,
        email: str = "admin@example.com",
        role: UserRole = UserRole.ADMIN,
    ) -> User:
        """Create a test user with the given role."""
        user = User(
            email=email,
            password_hash="hashed_password",
            role=role,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    async def _create_test_claim(
        self,
        db_session: AsyncSession,
        content: str = "Test claim content for fact checking",
    ) -> Claim:
        """Create a test claim."""
        claim = Claim(
            content=content,
            source="test_source",
        )
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)
        return claim

    async def _create_test_fact_check(
        self,
        db_session: AsyncSession,
        claim: Claim,
    ) -> FactCheck:
        """Create a test fact-check."""
        fact_check = FactCheck(
            claim_id=claim.id,
            verdict="pending",
            confidence=0.0,
            reasoning="Initial fact-check created for testing",
            sources=[],
            sources_count=0,
        )
        db_session.add(fact_check)
        await db_session.commit()
        await db_session.refresh(fact_check)
        return fact_check

    # ========================================================================
    # Test Case 1: First version creation
    # ========================================================================

    @pytest.mark.asyncio
    async def test_assign_rating_creates_first_version(self, db_session: AsyncSession) -> None:
        """Test that assigning a rating to a fact-check creates the first version."""
        # Arrange
        user = await self._create_test_user(db_session)
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        rating_data = RatingCreate(
            rating=FactCheckRatingValue.FALSE,
            justification="This claim has been thoroughly investigated and found "
            "to be completely inaccurate based on multiple reliable sources.",
        )

        # Act
        result = await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=rating_data,
            assigned_by_id=user.id,
        )

        # Assert
        assert result is not None
        assert result.id is not None
        assert result.fact_check_id == fact_check.id
        assert result.assigned_by_id == user.id
        assert result.rating == FactCheckRatingValue.FALSE.value
        assert result.version == 1
        assert result.is_current is True
        assert len(rating_data.justification) >= 50

    @pytest.mark.asyncio
    async def test_assign_rating_sets_assigned_at_timestamp(self, db_session: AsyncSession) -> None:
        """Test that assigned_at is set when rating is created."""
        # Arrange
        user = await self._create_test_user(db_session)
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        rating_data = RatingCreate(
            rating=FactCheckRatingValue.TRUE,
            justification="This claim has been verified as completely accurate "
            "through multiple independent and reliable primary sources.",
        )

        # Act
        result = await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=rating_data,
            assigned_by_id=user.id,
        )

        # Assert
        now = datetime.now(timezone.utc)
        assert result.assigned_at is not None
        # Use normalize_dt and check within a reasonable time window (60 seconds)
        # SQLite may have second-level precision vs microsecond precision in Python
        time_diff = abs((normalize_dt(now) - normalize_dt(result.assigned_at)).total_seconds())
        assert time_diff < 60, "assigned_at should be within 60 seconds of now"

    # ========================================================================
    # Test Case 2: Version incrementing behavior
    # ========================================================================

    @pytest.mark.asyncio
    async def test_assign_rating_increments_version(self, db_session: AsyncSession) -> None:
        """Test that assigning a new rating increments the version number."""
        # Arrange
        user = await self._create_test_user(db_session)
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        first_rating = RatingCreate(
            rating=FactCheckRatingValue.FALSE,
            justification="Initial assessment: This claim has been found to be "
            "inaccurate based on our preliminary fact-checking investigation.",
        )
        second_rating = RatingCreate(
            rating=FactCheckRatingValue.PARTLY_FALSE,
            justification="Updated assessment after further investigation: The claim "
            "contains some accurate elements but is misleading overall.",
        )

        # Act
        first_result = await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=first_rating,
            assigned_by_id=user.id,
        )
        second_result = await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=second_rating,
            assigned_by_id=user.id,
        )

        # Assert
        assert first_result.version == 1
        assert second_result.version == 2

    @pytest.mark.asyncio
    async def test_assign_rating_marks_previous_as_not_current(
        self, db_session: AsyncSession
    ) -> None:
        """Test that assigning a new rating marks the previous rating as not current."""
        # Arrange
        user = await self._create_test_user(db_session)
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        first_rating = RatingCreate(
            rating=FactCheckRatingValue.FALSE,
            justification="Initial assessment: This claim has been found to be "
            "inaccurate based on our preliminary fact-checking investigation.",
        )
        second_rating = RatingCreate(
            rating=FactCheckRatingValue.TRUE,
            justification="Revised assessment: After receiving new evidence, we "
            "have determined that the claim is actually accurate and verified.",
        )

        # Act
        first_result = await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=first_rating,
            assigned_by_id=user.id,
        )
        first_rating_id = first_result.id

        second_result = await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=second_rating,
            assigned_by_id=user.id,
        )

        # Refresh the first rating from database
        stmt = select(FactCheckRating).where(FactCheckRating.id == first_rating_id)
        result = await db_session.execute(stmt)
        refreshed_first = result.scalar_one()

        # Assert
        assert refreshed_first.is_current is False
        assert second_result.is_current is True

    @pytest.mark.asyncio
    async def test_multiple_versions_maintain_correct_order(self, db_session: AsyncSession) -> None:
        """Test that multiple rating versions maintain correct version numbers."""
        # Arrange
        user = await self._create_test_user(db_session)
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        ratings_data = [
            RatingCreate(
                rating=FactCheckRatingValue.FALSE,
                justification="First version: Claim found to be false after "
                "initial investigation with multiple sources confirming this.",
            ),
            RatingCreate(
                rating=FactCheckRatingValue.PARTLY_FALSE,
                justification="Second version: Updated to partly false after "
                "discovering some true elements in the original claim.",
            ),
            RatingCreate(
                rating=FactCheckRatingValue.MISSING_CONTEXT,
                justification="Third version: Changed to missing context as the "
                "claim is technically true but lacks important context.",
            ),
        ]

        # Act
        results = []
        for rating_data in ratings_data:
            result = await assign_rating(
                db=db_session,
                fact_check_id=fact_check.id,
                rating_data=rating_data,
                assigned_by_id=user.id,
            )
            results.append(result)

        # Assert
        assert results[0].version == 1
        assert results[1].version == 2
        assert results[2].version == 3
        assert results[2].is_current is True

    # ========================================================================
    # Test Case 3: Justification validation requirements
    # ========================================================================

    @pytest.mark.asyncio
    async def test_assign_rating_rejects_short_justification(
        self, db_session: AsyncSession
    ) -> None:
        """Test that justification shorter than 50 characters is rejected."""
        # Note: db_session is unused but required by pytest fixture pattern
        _ = db_session  # Mark as intentionally unused

        # Act & Assert - Pydantic validation should reject this
        with pytest.raises(ValueError) as exc_info:
            RatingCreate(
                rating=FactCheckRatingValue.FALSE,
                justification="Too short",  # Less than 50 characters
            )

        assert "at least" in str(exc_info.value).lower() or "50" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assign_rating_rejects_whitespace_only_justification(
        self, db_session: AsyncSession
    ) -> None:
        """Test that whitespace-only justification is rejected."""
        # Note: db_session is unused but required by pytest fixture pattern
        _ = db_session  # Mark as intentionally unused

        # Arrange - 60 spaces should not count as valid 50+ chars
        whitespace_justification = " " * 60

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            RatingCreate(
                rating=FactCheckRatingValue.FALSE,
                justification=whitespace_justification,
            )

        assert "non-whitespace" in str(exc_info.value).lower() or "50" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assign_rating_accepts_exactly_50_char_justification(
        self, db_session: AsyncSession
    ) -> None:
        """Test that justification with exactly 50 characters is accepted."""
        # Arrange
        user = await self._create_test_user(db_session)
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        # Exactly 50 characters
        exactly_50_chars = "A" * 50
        rating_data = RatingCreate(
            rating=FactCheckRatingValue.TRUE,
            justification=exactly_50_chars,
        )

        # Act
        result = await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=rating_data,
            assigned_by_id=user.id,
        )

        # Assert
        assert result is not None
        assert len(result.justification) == 50

    @pytest.mark.asyncio
    async def test_assign_rating_trims_whitespace_from_justification(
        self, db_session: AsyncSession
    ) -> None:
        """Test that leading/trailing whitespace is trimmed from justification."""
        # Arrange
        user = await self._create_test_user(db_session)
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        justification_with_spaces = (
            "   This claim has been verified as accurate through "
            "multiple independent and reliable primary sources.   "
        )
        rating_data = RatingCreate(
            rating=FactCheckRatingValue.TRUE,
            justification=justification_with_spaces,
        )

        # Act
        result = await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=rating_data,
            assigned_by_id=user.id,
        )

        # Assert
        assert not result.justification.startswith(" ")
        assert not result.justification.endswith(" ")

    # ========================================================================
    # Test Case 4: Rating history retrieval
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_rating_history_returns_all_versions(self, db_session: AsyncSession) -> None:
        """Test that get_rating_history returns all rating versions."""
        # Arrange
        user = await self._create_test_user(db_session)
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        ratings_data = [
            RatingCreate(
                rating=FactCheckRatingValue.FALSE,
                justification="First version: Initial assessment found the claim "
                "to be false based on available evidence and sources.",
            ),
            RatingCreate(
                rating=FactCheckRatingValue.PARTLY_FALSE,
                justification="Second version: Revised assessment after new "
                "evidence emerged showing partial accuracy of the claim.",
            ),
            RatingCreate(
                rating=FactCheckRatingValue.TRUE,
                justification="Third version: Final assessment after complete "
                "investigation confirmed the claim is actually accurate.",
            ),
        ]

        for rating_data in ratings_data:
            await assign_rating(
                db=db_session,
                fact_check_id=fact_check.id,
                rating_data=rating_data,
                assigned_by_id=user.id,
            )

        # Act
        history = await get_rating_history(db=db_session, fact_check_id=fact_check.id)

        # Assert
        assert history is not None
        assert history.fact_check_id == fact_check.id
        assert history.total_versions == 3
        assert len(history.ratings) == 3

    @pytest.mark.asyncio
    async def test_get_rating_history_returns_versions_in_order(
        self, db_session: AsyncSession
    ) -> None:
        """Test that rating history is returned in chronological order."""
        # Arrange
        user = await self._create_test_user(db_session)
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        ratings_data = [
            RatingCreate(
                rating=FactCheckRatingValue.FALSE,
                justification="First: This claim was initially determined to be "
                "false after our preliminary fact-checking investigation.",
            ),
            RatingCreate(
                rating=FactCheckRatingValue.TRUE,
                justification="Second: Revised after receiving additional evidence "
                "that supports the accuracy of the original claim.",
            ),
        ]

        for rating_data in ratings_data:
            await assign_rating(
                db=db_session,
                fact_check_id=fact_check.id,
                rating_data=rating_data,
                assigned_by_id=user.id,
            )

        # Act
        history = await get_rating_history(db=db_session, fact_check_id=fact_check.id)

        # Assert
        assert history.ratings[0].version == 1
        assert history.ratings[1].version == 2
        assert history.ratings[0].rating == FactCheckRatingValue.FALSE.value
        assert history.ratings[1].rating == FactCheckRatingValue.TRUE.value

    @pytest.mark.asyncio
    async def test_get_rating_history_empty_for_unrated_fact_check(
        self, db_session: AsyncSession
    ) -> None:
        """Test that get_rating_history returns empty for fact-check with no ratings."""
        # Arrange
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        # Act
        history = await get_rating_history(db=db_session, fact_check_id=fact_check.id)

        # Assert
        assert history is not None
        assert history.fact_check_id == fact_check.id
        assert history.total_versions == 0
        assert len(history.ratings) == 0

    # ========================================================================
    # Test Case 5: Latest rating retrieval
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_current_rating_returns_latest(self, db_session: AsyncSession) -> None:
        """Test that get_current_rating returns the most recent rating."""
        # Arrange
        user = await self._create_test_user(db_session)
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        # Add multiple ratings
        for rating_value in [
            FactCheckRatingValue.FALSE,
            FactCheckRatingValue.PARTLY_FALSE,
            FactCheckRatingValue.TRUE,
        ]:
            await assign_rating(
                db=db_session,
                fact_check_id=fact_check.id,
                rating_data=RatingCreate(
                    rating=rating_value,
                    justification=f"Rating changed to {rating_value.value}. This "
                    "assessment is based on comprehensive fact-checking analysis.",
                ),
                assigned_by_id=user.id,
            )

        # Act
        current = await get_current_rating(db=db_session, fact_check_id=fact_check.id)

        # Assert
        assert current is not None
        assert current.has_rating is True
        assert current.rating is not None
        assert current.rating.rating == FactCheckRatingValue.TRUE.value
        assert current.rating.version == 3
        assert current.rating.is_current is True

    @pytest.mark.asyncio
    async def test_get_current_rating_returns_none_for_unrated(
        self, db_session: AsyncSession
    ) -> None:
        """Test that get_current_rating returns None for unrated fact-check."""
        # Arrange
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        # Act
        current = await get_current_rating(db=db_session, fact_check_id=fact_check.id)

        # Assert
        assert current is not None
        assert current.fact_check_id == fact_check.id
        assert current.has_rating is False
        assert current.rating is None

    @pytest.mark.asyncio
    async def test_get_current_rating_only_returns_current_flag_true(
        self, db_session: AsyncSession
    ) -> None:
        """Test that get_current_rating only returns rating with is_current=True."""
        # Arrange
        user = await self._create_test_user(db_session)
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        # Add two ratings
        await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=RatingCreate(
                rating=FactCheckRatingValue.FALSE,
                justification="First rating: This claim has been determined to be "
                "false based on our comprehensive fact-checking analysis.",
            ),
            assigned_by_id=user.id,
        )
        await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=RatingCreate(
                rating=FactCheckRatingValue.TRUE,
                justification="Second rating: Revised assessment confirms claim "
                "is accurate after receiving new corroborating evidence.",
            ),
            assigned_by_id=user.id,
        )

        # Act
        current = await get_current_rating(db=db_session, fact_check_id=fact_check.id)

        # Assert - should only get the second (current) rating
        assert current.rating is not None
        assert current.rating.rating == FactCheckRatingValue.TRUE.value
        assert current.rating.is_current is True

    # ========================================================================
    # Test Case 6: Permission-based access control
    # ========================================================================

    @pytest.mark.asyncio
    async def test_assign_rating_allowed_for_admin(self, db_session: AsyncSession) -> None:
        """Test that admin users can assign ratings."""
        # Arrange
        admin = await self._create_test_user(
            db_session, email="admin@example.com", role=UserRole.ADMIN
        )
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        rating_data = RatingCreate(
            rating=FactCheckRatingValue.TRUE,
            justification="Admin-assigned rating: This claim has been verified "
            "as accurate through multiple independent and reliable sources.",
        )

        # Act
        result = await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=rating_data,
            assigned_by_id=admin.id,
        )

        # Assert
        assert result is not None
        assert result.assigned_by_id == admin.id

    @pytest.mark.asyncio
    async def test_assign_rating_allowed_for_super_admin(self, db_session: AsyncSession) -> None:
        """Test that super admin users can assign ratings."""
        # Arrange
        super_admin = await self._create_test_user(
            db_session, email="superadmin@example.com", role=UserRole.SUPER_ADMIN
        )
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        rating_data = RatingCreate(
            rating=FactCheckRatingValue.FALSE,
            justification="Super admin rating: This claim has been investigated "
            "and found to be inaccurate based on authoritative sources.",
        )

        # Act
        result = await assign_rating(
            db=db_session,
            fact_check_id=fact_check.id,
            rating_data=rating_data,
            assigned_by_id=super_admin.id,
        )

        # Assert
        assert result is not None
        assert result.assigned_by_id == super_admin.id

    @pytest.mark.asyncio
    async def test_assign_rating_denied_for_reviewer(self, db_session: AsyncSession) -> None:
        """Test that reviewer users cannot assign ratings (they can only suggest)."""
        # Arrange
        reviewer = await self._create_test_user(
            db_session, email="reviewer@example.com", role=UserRole.REVIEWER
        )
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        rating_data = RatingCreate(
            rating=FactCheckRatingValue.TRUE,
            justification="Reviewer attempting to assign rating: This should fail "
            "because reviewers can only suggest, not assign ratings.",
        )

        # Act & Assert
        with pytest.raises(RatingPermissionError) as exc_info:
            await assign_rating(
                db=db_session,
                fact_check_id=fact_check.id,
                rating_data=rating_data,
                assigned_by_id=reviewer.id,
            )

        assert "permission" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_assign_rating_denied_for_submitter(self, db_session: AsyncSession) -> None:
        """Test that submitter users cannot assign ratings."""
        # Arrange
        submitter = await self._create_test_user(
            db_session, email="submitter@example.com", role=UserRole.SUBMITTER
        )
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)

        rating_data = RatingCreate(
            rating=FactCheckRatingValue.TRUE,
            justification="Submitter attempting to assign rating: This should fail "
            "as submitters should not have permission to assign ratings.",
        )

        # Act & Assert
        with pytest.raises(RatingPermissionError) as exc_info:
            await assign_rating(
                db=db_session,
                fact_check_id=fact_check.id,
                rating_data=rating_data,
                assigned_by_id=submitter.id,
            )

        assert "permission" in str(exc_info.value).lower()

    # ========================================================================
    # Additional edge cases and error handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_assign_rating_fails_for_nonexistent_fact_check(
        self, db_session: AsyncSession
    ) -> None:
        """Test that assigning rating to non-existent fact-check fails."""
        # Arrange
        user = await self._create_test_user(db_session)
        nonexistent_id = UUID("00000000-0000-0000-0000-000000000000")

        rating_data = RatingCreate(
            rating=FactCheckRatingValue.TRUE,
            justification="Attempting to rate a non-existent fact-check. This "
            "operation should fail with an appropriate error message.",
        )

        # Act & Assert
        with pytest.raises(RatingValidationError) as exc_info:
            await assign_rating(
                db=db_session,
                fact_check_id=nonexistent_id,
                rating_data=rating_data,
                assigned_by_id=user.id,
            )

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_assign_rating_fails_for_nonexistent_user(self, db_session: AsyncSession) -> None:
        """Test that assigning rating with non-existent user fails."""
        # Arrange
        claim = await self._create_test_claim(db_session)
        fact_check = await self._create_test_fact_check(db_session, claim)
        nonexistent_user_id = UUID("00000000-0000-0000-0000-000000000000")

        rating_data = RatingCreate(
            rating=FactCheckRatingValue.TRUE,
            justification="Attempting to rate with a non-existent user ID. This "
            "operation should fail with an appropriate error message.",
        )

        # Act & Assert
        with pytest.raises(RatingValidationError) as exc_info:
            await assign_rating(
                db=db_session,
                fact_check_id=fact_check.id,
                rating_data=rating_data,
                assigned_by_id=nonexistent_user_id,
            )

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_rating_history_fails_for_nonexistent_fact_check(
        self, db_session: AsyncSession
    ) -> None:
        """Test that getting history for non-existent fact-check fails."""
        # Arrange
        nonexistent_id = UUID("00000000-0000-0000-0000-000000000000")

        # Act & Assert
        with pytest.raises(RatingValidationError) as exc_info:
            await get_rating_history(db=db_session, fact_check_id=nonexistent_id)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_current_rating_fails_for_nonexistent_fact_check(
        self, db_session: AsyncSession
    ) -> None:
        """Test that getting current rating for non-existent fact-check fails."""
        # Arrange
        nonexistent_id = UUID("00000000-0000-0000-0000-000000000000")

        # Act & Assert
        with pytest.raises(RatingValidationError) as exc_info:
            await get_current_rating(db=db_session, fact_check_id=nonexistent_id)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_all_rating_values_can_be_assigned(self, db_session: AsyncSession) -> None:
        """Test that all EFCSN rating values can be successfully assigned."""
        # Arrange
        user = await self._create_test_user(db_session)

        for rating_value in FactCheckRatingValue:
            claim = await self._create_test_claim(
                db_session, content=f"Claim for {rating_value.value} test"
            )
            fact_check = await self._create_test_fact_check(db_session, claim)

            rating_data = RatingCreate(
                rating=rating_value,
                justification=f"Testing {rating_value.value} rating assignment. "
                "This justification meets the minimum 50 character requirement.",
            )

            # Act
            result = await assign_rating(
                db=db_session,
                fact_check_id=fact_check.id,
                rating_data=rating_data,
                assigned_by_id=user.id,
            )

            # Assert
            assert result.rating == rating_value.value
