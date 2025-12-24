"""
Rating Service for managing fact-check ratings with versioning.

Issue #58: Backend: Rating System Service (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine
ADR 0005: EFCSN Compliance Architecture

This service provides:
- Rating assignment with automatic version tracking
- Rating history retrieval
- Current rating retrieval
- Permission-based access control (only ADMIN and SUPER_ADMIN can assign)
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fact_check import FactCheck
from app.models.fact_check_rating import FactCheckRating
from app.models.user import User, UserRole
from app.schemas.rating import (
    CurrentRatingResponse,
    RatingCreate,
    RatingHistoryResponse,
    RatingResponse,
)


class RatingServiceError(Exception):
    """Base exception for Rating Service errors."""

    pass


class RatingValidationError(RatingServiceError):
    """Raised when validation fails (e.g., entity not found)."""

    pass


class RatingPermissionError(RatingServiceError):
    """Raised when user doesn't have permission to perform action."""

    pass


async def _get_user(db: AsyncSession, user_id: UUID) -> User:
    """Retrieve user by ID or raise RatingValidationError if not found."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise RatingValidationError(f"User with ID {user_id} not found")

    return user


async def _get_fact_check(db: AsyncSession, fact_check_id: UUID) -> FactCheck:
    """Retrieve fact-check by ID or raise RatingValidationError if not found."""
    stmt = select(FactCheck).where(FactCheck.id == fact_check_id)
    result = await db.execute(stmt)
    fact_check = result.scalar_one_or_none()

    if fact_check is None:
        raise RatingValidationError(f"FactCheck with ID {fact_check_id} not found")

    return fact_check


async def _check_rating_permission(user: User) -> None:
    """Check if user has permission to assign ratings.

    Only ADMIN and SUPER_ADMIN roles can assign ratings.
    REVIEWER can suggest ratings but cannot officially assign them.

    Raises:
        RatingPermissionError: If user doesn't have permission
    """
    allowed_roles = {UserRole.ADMIN, UserRole.SUPER_ADMIN}

    if user.role not in allowed_roles:
        raise RatingPermissionError(
            f"User with role '{user.role.value}' does not have permission "
            "to assign ratings. Only ADMIN and SUPER_ADMIN can assign ratings."
        )


async def _get_next_version(db: AsyncSession, fact_check_id: UUID) -> int:
    """Get the next version number for a fact-check rating.

    Returns 1 if no ratings exist, otherwise max(version) + 1.
    """
    stmt = select(FactCheckRating.version).where(FactCheckRating.fact_check_id == fact_check_id)
    result = await db.execute(stmt)
    versions = list(result.scalars().all())

    if not versions:
        return 1

    return max(versions) + 1


async def _mark_previous_ratings_not_current(db: AsyncSession, fact_check_id: UUID) -> None:
    """Mark all existing ratings for a fact-check as not current."""
    stmt = (
        update(FactCheckRating)
        .where(FactCheckRating.fact_check_id == fact_check_id)
        .where(FactCheckRating.is_current.is_(True))
        .values(is_current=False)
    )
    await db.execute(stmt)


async def assign_rating(
    db: AsyncSession,
    fact_check_id: UUID,
    rating_data: RatingCreate,
    assigned_by_id: UUID,
) -> FactCheckRating:
    """Assign a rating to a fact-check with automatic version tracking.

    This function:
    1. Validates that the fact-check and user exist
    2. Checks user has permission to assign ratings
    3. Marks any existing current rating as not current
    4. Creates a new rating with incremented version number

    Args:
        db: Async database session
        fact_check_id: UUID of the fact-check to rate
        rating_data: Rating data including rating value and justification
        assigned_by_id: UUID of the user assigning the rating

    Returns:
        The newly created FactCheckRating

    Raises:
        RatingValidationError: If fact-check or user not found
        RatingPermissionError: If user doesn't have permission
    """
    # Validate user exists and has permission
    user = await _get_user(db, assigned_by_id)
    await _check_rating_permission(user)

    # Validate fact-check exists
    await _get_fact_check(db, fact_check_id)

    # Get next version number
    next_version = await _get_next_version(db, fact_check_id)

    # Mark previous ratings as not current
    await _mark_previous_ratings_not_current(db, fact_check_id)

    # Create new rating
    new_rating = FactCheckRating(
        fact_check_id=fact_check_id,
        assigned_by_id=assigned_by_id,
        rating=rating_data.rating.value,
        justification=rating_data.justification,
        version=next_version,
        is_current=True,
    )

    db.add(new_rating)
    await db.commit()
    await db.refresh(new_rating)

    return new_rating


async def get_rating_history(
    db: AsyncSession,
    fact_check_id: UUID,
) -> RatingHistoryResponse:
    """Retrieve all rating versions for a fact-check.

    Returns ratings ordered by version number (ascending).

    Args:
        db: Async database session
        fact_check_id: UUID of the fact-check

    Returns:
        RatingHistoryResponse containing all ratings and total count

    Raises:
        RatingValidationError: If fact-check not found
    """
    # Validate fact-check exists
    await _get_fact_check(db, fact_check_id)

    # Get all ratings ordered by version
    stmt = (
        select(FactCheckRating)
        .where(FactCheckRating.fact_check_id == fact_check_id)
        .order_by(FactCheckRating.version.asc())
    )
    result = await db.execute(stmt)
    ratings = list(result.scalars().all())

    # Convert to response objects
    rating_responses = [RatingResponse.model_validate(rating) for rating in ratings]

    return RatingHistoryResponse(
        fact_check_id=fact_check_id,
        ratings=rating_responses,
        total_versions=len(rating_responses),
    )


async def get_current_rating(
    db: AsyncSession,
    fact_check_id: UUID,
) -> CurrentRatingResponse:
    """Retrieve the current (latest) rating for a fact-check.

    Args:
        db: Async database session
        fact_check_id: UUID of the fact-check

    Returns:
        CurrentRatingResponse with the current rating or None if unrated

    Raises:
        RatingValidationError: If fact-check not found
    """
    # Validate fact-check exists
    await _get_fact_check(db, fact_check_id)

    # Get current rating (is_current = True)
    stmt = (
        select(FactCheckRating)
        .where(FactCheckRating.fact_check_id == fact_check_id)
        .where(FactCheckRating.is_current.is_(True))
    )
    result = await db.execute(stmt)
    current_rating = result.scalar_one_or_none()

    if current_rating is None:
        return CurrentRatingResponse(
            fact_check_id=fact_check_id,
            rating=None,
            has_rating=False,
        )

    return CurrentRatingResponse(
        fact_check_id=fact_check_id,
        rating=RatingResponse.model_validate(current_rating),
        has_rating=True,
    )
