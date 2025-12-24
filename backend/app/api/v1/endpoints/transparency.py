"""
Transparency Page API Endpoints.

Issue #84: Backend: Transparency Page API Endpoints
EPIC #51: Transparency & Methodology Pages
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- GET /api/v1/transparency - List all transparency pages
- GET /api/v1/transparency/{slug} - Get page by slug (public)
- PATCH /api/v1/transparency/{slug} - Update page (admin only)
- GET /api/v1/transparency/{slug}/versions - Get version history
- GET /api/v1/transparency/{slug}/diff/{v1}/{v2} - Get diff between versions
- POST /api/v1/transparency/{slug}/review - Mark page as reviewed (admin only)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.transparency_page import (
    TransparencyPageDiff,
    TransparencyPageListResponse,
    TransparencyPageResponse,
    TransparencyPageSummary,
    TransparencyPageUpdate,
    TransparencyPageVersionResponse,
)
from app.services import transparency_page_service

router = APIRouter()


@router.get(
    "",
    response_model=TransparencyPageListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all transparency pages",
    description="Retrieve a list of all transparency pages. Public endpoint.",
)
async def list_transparency_pages(
    db: AsyncSession = Depends(get_db),
) -> TransparencyPageListResponse:
    """
    List all transparency pages.

    Returns a list of all available transparency pages with their metadata.
    This is a public endpoint - no authentication required.
    """
    pages = await transparency_page_service.list_all_pages(db)
    items = [TransparencyPageSummary.model_validate(page) for page in pages]
    return TransparencyPageListResponse(items=items, total=len(items))


@router.get(
    "/{slug}",
    response_model=TransparencyPageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get transparency page by slug",
    description="Retrieve a specific transparency page by its slug. Public endpoint.",
)
async def get_transparency_page(
    slug: str,
    lang: Optional[str] = Query(
        None, description="Language code for response filtering (e.g., 'en', 'nl')"
    ),
    db: AsyncSession = Depends(get_db),
) -> TransparencyPageResponse:
    """
    Get a transparency page by its slug.

    This is a public endpoint - no authentication required.
    The language parameter is for frontend use; the full multilingual
    content is always returned.

    Args:
        slug: URL-friendly page identifier (e.g., "methodology", "funding")
        lang: Optional language code for filtering (passed through for frontend use)
        db: Database session

    Returns:
        TransparencyPageResponse with full page content

    Raises:
        HTTPException 404: If page with given slug is not found
    """
    page = await transparency_page_service.get_page_by_slug(db, slug, language=lang)

    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transparency page '{slug}' not found",
        )

    return TransparencyPageResponse.model_validate(page)


@router.patch(
    "/{slug}",
    response_model=TransparencyPageResponse,
    status_code=status.HTTP_200_OK,
    summary="Update transparency page",
    description="Update a transparency page. Admin only. Creates new version.",
)
async def update_transparency_page(
    slug: str,
    update_data: TransparencyPageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TransparencyPageResponse:
    """
    Update a transparency page with automatic versioning.

    This endpoint is restricted to admin and super_admin roles.
    Each update creates a version history record and increments the version number.
    The review dates are automatically updated.

    Args:
        slug: URL-friendly page identifier
        update_data: Update payload with title, content, and change_summary
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Updated TransparencyPageResponse

    Raises:
        HTTPException 404: If page with given slug is not found
        HTTPException 403: If user doesn't have admin permissions
    """
    updated_page = await transparency_page_service.update_page(
        db=db,
        slug=slug,
        title=update_data.title,
        content=update_data.content,
        changed_by_id=current_user.id,
        change_summary=update_data.change_summary,
    )

    if updated_page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transparency page '{slug}' not found",
        )

    return TransparencyPageResponse.model_validate(updated_page)


@router.get(
    "/{slug}/versions",
    response_model=list[TransparencyPageVersionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get version history",
    description="Get the version history of a transparency page.",
)
async def get_version_history(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> list[TransparencyPageVersionResponse]:
    """
    Get the version history for a transparency page.

    Returns all historical versions of the page, ordered by version number.
    The current version is NOT included in history - only previous versions.

    Args:
        slug: URL-friendly page identifier
        db: Database session

    Returns:
        List of TransparencyPageVersionResponse objects

    Raises:
        HTTPException 404: If page with given slug is not found
    """
    # First check if page exists
    page = await transparency_page_service.get_page_by_slug(db, slug)
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transparency page '{slug}' not found",
        )

    versions = await transparency_page_service.get_version_history(db, slug)
    return [TransparencyPageVersionResponse.model_validate(v) for v in versions]


@router.get(
    "/{slug}/diff/{v1}/{v2}",
    response_model=TransparencyPageDiff,
    status_code=status.HTTP_200_OK,
    summary="Get diff between versions",
    description="Generate a diff between two versions of a transparency page.",
)
async def get_version_diff(
    slug: str,
    v1: int,
    v2: int,
    lang: Optional[str] = Query(
        None, description="Language code to filter diff (e.g., 'en', 'nl')"
    ),
    db: AsyncSession = Depends(get_db),
) -> TransparencyPageDiff:
    """
    Generate a diff between two versions of a transparency page.

    Uses unified diff format to show changes between versions.

    Args:
        slug: URL-friendly page identifier
        v1: Starting version number (from)
        v2: Ending version number (to)
        lang: Optional language code to filter diff to specific language
        db: Database session

    Returns:
        TransparencyPageDiff with diff information

    Raises:
        HTTPException 404: If page or versions not found
    """
    diff_result = await transparency_page_service.generate_diff(
        db=db,
        slug=slug,
        from_version=v1,
        to_version=v2,
        language=lang,
    )

    if diff_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transparency page '{slug}' or version(s) {v1}/{v2} not found",
        )

    return TransparencyPageDiff(**diff_result)


@router.post(
    "/{slug}/review",
    response_model=TransparencyPageResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark page as reviewed",
    description="Mark a transparency page as reviewed. Admin only. Updates review dates.",
)
async def mark_page_reviewed(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TransparencyPageResponse:
    """
    Mark a transparency page as reviewed for annual EFCSN compliance.

    This endpoint updates the last_reviewed and next_review_due dates
    without changing the content or creating a new version.

    Args:
        slug: URL-friendly page identifier
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Updated TransparencyPageResponse with new review dates

    Raises:
        HTTPException 404: If page with given slug is not found
        HTTPException 403: If user doesn't have admin permissions
    """
    # Get the page
    page = await transparency_page_service.get_page_by_slug(db, slug)

    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transparency page '{slug}' not found",
        )

    # Update review dates directly
    now = datetime.now(timezone.utc)
    page.last_reviewed = now
    page.next_review_due = now + timedelta(days=365)

    await db.commit()
    await db.refresh(page)

    return TransparencyPageResponse.model_validate(page)
