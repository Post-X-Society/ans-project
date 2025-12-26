"""
Rating API Endpoints for EFCSN-compliant fact-check ratings.

Issue #60: Backend: Rating & Workflow API Endpoints (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- POST /ratings/seed - Seed rating definitions (admin-only)
- GET /ratings/definitions - Get all rating definitions (public)
- POST /fact-checks/{id}/rating - Assign rating (admin-only, versioned)
- GET /fact-checks/{id}/ratings - Get rating history (public)
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.rating_definition import RatingDefinition
from app.models.user import User
from app.schemas.rating import (
    CurrentRatingResponse,
    RatingCreate,
    RatingHistoryResponse,
    RatingResponse,
)
from app.services.rating_service import (
    RatingPermissionError,
    RatingValidationError,
    assign_rating,
    get_current_rating,
    get_rating_history,
)

router = APIRouter()


# EFCSN Rating definitions for seeding
EFCSN_RATING_DEFINITIONS: list[dict[str, Any]] = [
    {
        "rating_key": "TRUE",
        "title": {"en": "True", "nl": "Waar"},
        "description": {
            "en": "The claim is completely accurate based on available evidence.",
            "nl": "De bewering is volledig juist op basis van beschikbaar bewijs.",
        },
        "visual_color": "#00AA00",
        "icon_name": "check-circle",
        "display_order": 1,
    },
    {
        "rating_key": "PARTLY_FALSE",
        "title": {"en": "Partly False", "nl": "Gedeeltelijk Onwaar"},
        "description": {
            "en": "The claim contains some false elements mixed with true ones.",
            "nl": "De bewering bevat enkele onjuiste elementen vermengd met juiste.",
        },
        "visual_color": "#FFA500",
        "icon_name": "alert-circle",
        "display_order": 2,
    },
    {
        "rating_key": "FALSE",
        "title": {"en": "False", "nl": "Onwaar"},
        "description": {
            "en": "The claim is completely inaccurate.",
            "nl": "De bewering is volledig onjuist.",
        },
        "visual_color": "#FF0000",
        "icon_name": "x-circle",
        "display_order": 3,
    },
    {
        "rating_key": "MISSING_CONTEXT",
        "title": {"en": "Missing Context", "nl": "Context Ontbreekt"},
        "description": {
            "en": "The claim is technically true but lacks important context.",
            "nl": "De bewering is technisch waar maar mist belangrijke context.",
        },
        "visual_color": "#9932CC",
        "icon_name": "info",
        "display_order": 4,
    },
    {
        "rating_key": "ALTERED",
        "title": {"en": "Altered", "nl": "Gemanipuleerd"},
        "description": {
            "en": "The content has been digitally manipulated or altered.",
            "nl": "De inhoud is digitaal gemanipuleerd of gewijzigd.",
        },
        "visual_color": "#8B0000",
        "icon_name": "edit",
        "display_order": 5,
    },
    {
        "rating_key": "SATIRE",
        "title": {"en": "Satire", "nl": "Satire"},
        "description": {
            "en": "The content is satirical and not intended to be factual.",
            "nl": "De inhoud is satirisch en niet bedoeld als feitelijk.",
        },
        "visual_color": "#4169E1",
        "icon_name": "smile",
        "display_order": 6,
    },
    {
        "rating_key": "UNVERIFIABLE",
        "title": {"en": "Unverifiable", "nl": "Niet Verifieerbaar"},
        "description": {
            "en": "The claim cannot be verified with available evidence.",
            "nl": "De bewering kan niet worden geverifieerd met beschikbaar bewijs.",
        },
        "visual_color": "#808080",
        "icon_name": "help-circle",
        "display_order": 7,
    },
]


class RatingDefinitionResponse(BaseModel):
    """Response schema for a single rating definition."""

    id: UUID
    rating_key: str
    title: dict[str, Any]
    description: dict[str, Any]
    visual_color: str | None
    icon_name: str | None
    display_order: int | None

    model_config = {"from_attributes": True}


class SeedResponse(BaseModel):
    """Response for seeding operation."""

    message: str
    count: int


@router.post(
    "/ratings/seed",
    response_model=SeedResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["ratings"],
    summary="Seed rating definitions",
    description="Seed the database with EFCSN-compliant rating definitions. Admin only.",
)
async def seed_rating_definitions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SeedResponse:
    """
    Seed the database with EFCSN rating definitions.

    Only admins and super admins can seed rating definitions.
    This operation is idempotent - existing definitions are skipped.
    """
    created_count = 0

    for defn_data in EFCSN_RATING_DEFINITIONS:
        # Check if already exists
        stmt = select(RatingDefinition).where(
            RatingDefinition.rating_key == defn_data["rating_key"]
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            definition = RatingDefinition(
                rating_key=defn_data["rating_key"],
                title=defn_data["title"],
                description=defn_data["description"],
                visual_color=defn_data["visual_color"],
                icon_name=defn_data["icon_name"],
                display_order=defn_data["display_order"],
            )
            db.add(definition)
            created_count += 1

    await db.commit()

    return SeedResponse(
        message=f"Successfully seeded {created_count} rating definitions",
        count=created_count,
    )


@router.get(
    "/ratings/definitions",
    response_model=list[RatingDefinitionResponse],
    tags=["ratings"],
    summary="Get all rating definitions",
    description="Retrieve all EFCSN rating definitions. Public endpoint.",
)
async def get_rating_definitions(
    db: AsyncSession = Depends(get_db),
) -> list[RatingDefinition]:
    """
    Get all rating definitions ordered by display_order.

    This is a public endpoint - no authentication required.
    """
    stmt = select(RatingDefinition).order_by(RatingDefinition.display_order)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post(
    "/fact-checks/{fact_check_id}/rating",
    response_model=RatingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["ratings"],
    summary="Assign rating to fact-check",
    description="Assign a rating to a fact-check with automatic versioning. Admin only.",
)
async def create_fact_check_rating(
    fact_check_id: UUID,
    rating_data: RatingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RatingResponse:
    """
    Assign a rating to a fact-check.

    Creates a new versioned rating. Only admins and super admins can assign ratings.
    The rating history is preserved - previous ratings are marked as not current.
    """
    try:
        rating = await assign_rating(
            db=db,
            fact_check_id=fact_check_id,
            rating_data=rating_data,
            assigned_by_id=current_user.id,
        )
        return RatingResponse.model_validate(rating)

    except RatingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except RatingPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e


@router.get(
    "/fact-checks/{fact_check_id}/ratings",
    response_model=RatingHistoryResponse,
    tags=["ratings"],
    summary="Get rating history",
    description="Retrieve the complete rating history for a fact-check. Public endpoint.",
)
async def get_fact_check_ratings(
    fact_check_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> RatingHistoryResponse:
    """
    Get the complete rating history for a fact-check.

    Returns all rating versions ordered by version number.
    This is a public endpoint - no authentication required.
    """
    try:
        return await get_rating_history(db=db, fact_check_id=fact_check_id)
    except RatingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get(
    "/fact-checks/{fact_check_id}/rating",
    response_model=CurrentRatingResponse,
    tags=["ratings"],
    summary="Get current rating",
    description="Retrieve the current (latest) rating for a fact-check. Public endpoint.",
)
async def get_current_fact_check_rating(
    fact_check_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CurrentRatingResponse:
    """
    Get the current rating for a fact-check.

    Returns the most recent rating (is_current=True) or indicates no rating exists.
    This is a public endpoint - no authentication required.
    """
    try:
        return await get_current_rating(db=db, fact_check_id=fact_check_id)
    except RatingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
