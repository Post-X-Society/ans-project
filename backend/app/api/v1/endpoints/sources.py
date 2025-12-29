"""
Source API Endpoints for EFCSN-compliant evidence management.

Issue #70: Backend: Source Management Service (TDD)
EPIC #49: Evidence & Source Management
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- POST /fact-checks/{id}/sources - Add source to fact-check
- GET /fact-checks/{id}/sources - List sources for fact-check
- GET /fact-checks/{id}/sources/citations - List sources with citation numbers
- GET /sources/{id} - Get single source
- PATCH /sources/{id} - Update source
- DELETE /sources/{id} - Delete source
- GET /fact-checks/{id}/sources/validate - Validate minimum source count
- GET /fact-checks/{id}/sources/credibility - Get credibility summary
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_reviewer
from app.models.user import User
from app.schemas.source import (
    SourceCreate,
    SourceCredibilityResponse,
    SourceListResponse,
    SourceResponse,
    SourcesWithCitationsResponse,
    SourceUpdate,
    SourceValidationResponse,
    SourceWithCitationResponse,
)
from app.services.source_service import (
    MINIMUM_SOURCES_REQUIRED,
    SourceValidationError,
    create_source,
    delete_source,
    get_average_credibility_score,
    get_source,
    get_source_count,
    get_sources_by_min_credibility,
    get_sources_for_fact_check,
    get_sources_with_citations,
    update_source,
)

router = APIRouter()


# =============================================================================
# Source CRUD Endpoints
# =============================================================================


@router.post(
    "/fact-checks/{fact_check_id}/sources",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["sources"],
    summary="Add source to fact-check",
    description="Add a new evidence source to a fact-check. Requires reviewer role or higher.",
)
async def add_source(
    fact_check_id: UUID,
    source_data: SourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> SourceResponse:
    """
    Add a new source to a fact-check.

    Automatically updates the fact-check's sources_count.
    Requires reviewer, admin, or super_admin role.
    """
    # Ensure fact_check_id in path matches body
    if source_data.fact_check_id != fact_check_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fact_check_id in path must match fact_check_id in request body",
        )

    try:
        source = await create_source(db=db, source_data=source_data)
        return SourceResponse.model_validate(source)
    except SourceValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get(
    "/fact-checks/{fact_check_id}/sources",
    response_model=SourceListResponse,
    tags=["sources"],
    summary="List sources for fact-check",
    description="Retrieve all sources for a fact-check. Public endpoint.",
)
async def list_sources(
    fact_check_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceListResponse:
    """
    List all sources for a fact-check.

    Sources are returned in order of creation (oldest first).
    This is a public endpoint - no authentication required.
    """
    sources = await get_sources_for_fact_check(db=db, fact_check_id=fact_check_id)

    return SourceListResponse(
        fact_check_id=fact_check_id,
        sources=[SourceResponse.model_validate(s) for s in sources],
        total_count=len(sources),
    )


@router.get(
    "/fact-checks/{fact_check_id}/sources/citations",
    response_model=SourcesWithCitationsResponse,
    tags=["sources"],
    summary="List sources with citation numbers",
    description="Retrieve sources with automatic citation numbering [1], [2], etc.",
)
async def list_sources_with_citations(
    fact_check_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SourcesWithCitationsResponse:
    """
    List all sources for a fact-check with citation numbers.

    Sources are numbered in order of creation:
    - First source added = [1]
    - Second source added = [2]
    - etc.

    This is a public endpoint - no authentication required.
    """
    cited_sources = await get_sources_with_citations(db=db, fact_check_id=fact_check_id)

    sources_with_citations = [
        SourceWithCitationResponse(
            source=SourceResponse.model_validate(item["source"]),
            citation_number=item["citation_number"],
            citation_string=item["citation_string"],
        )
        for item in cited_sources
    ]

    return SourcesWithCitationsResponse(
        fact_check_id=fact_check_id,
        sources=sources_with_citations,
        total_count=len(sources_with_citations),
    )


@router.get(
    "/sources/{source_id}",
    response_model=SourceResponse,
    tags=["sources"],
    summary="Get single source",
    description="Retrieve a single source by ID. Public endpoint.",
)
async def get_single_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    """
    Get a single source by ID.

    This is a public endpoint - no authentication required.
    """
    try:
        source = await get_source(db=db, source_id=source_id)
        return SourceResponse.model_validate(source)
    except SourceValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.patch(
    "/sources/{source_id}",
    response_model=SourceResponse,
    tags=["sources"],
    summary="Update source",
    description="Update an existing source. Requires reviewer role or higher.",
)
async def update_single_source(
    source_id: UUID,
    update_data: SourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> SourceResponse:
    """
    Update an existing source.

    Only provided fields will be updated.
    Requires reviewer, admin, or super_admin role.
    """
    try:
        source = await update_source(db=db, source_id=source_id, update_data=update_data)
        return SourceResponse.model_validate(source)
    except SourceValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.delete(
    "/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["sources"],
    summary="Delete source",
    description="Delete a source. Requires reviewer role or higher.",
)
async def delete_single_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> None:
    """
    Delete a source.

    Automatically updates the fact-check's sources_count.
    Requires reviewer, admin, or super_admin role.
    """
    try:
        await delete_source(db=db, source_id=source_id)
    except SourceValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


# =============================================================================
# Source Validation Endpoints
# =============================================================================


@router.get(
    "/fact-checks/{fact_check_id}/sources/validate",
    response_model=SourceValidationResponse,
    tags=["sources"],
    summary="Validate source count",
    description="Check if fact-check has minimum required sources for publishing.",
)
async def validate_sources(
    fact_check_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceValidationResponse:
    """
    Validate that a fact-check has the minimum required sources.

    EFCSN requires minimum 2 sources per fact-check.
    Returns validation status without raising an error.
    """
    count = await get_source_count(db=db, fact_check_id=fact_check_id)
    is_valid = count >= MINIMUM_SOURCES_REQUIRED

    if is_valid:
        message = f"Fact-check has {count} sources, meeting the minimum requirement of {MINIMUM_SOURCES_REQUIRED}."
    else:
        message = f"Fact-check has {count} sources, but requires minimum {MINIMUM_SOURCES_REQUIRED} for publishing."

    return SourceValidationResponse(
        fact_check_id=fact_check_id,
        is_valid=is_valid,
        source_count=count,
        minimum_required=MINIMUM_SOURCES_REQUIRED,
        message=message,
    )


# =============================================================================
# Credibility Endpoints
# =============================================================================


@router.get(
    "/fact-checks/{fact_check_id}/sources/credibility",
    response_model=SourceCredibilityResponse,
    tags=["sources"],
    summary="Get source credibility summary",
    description="Get average credibility score and statistics for a fact-check's sources.",
)
async def get_credibility_summary(
    fact_check_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceCredibilityResponse:
    """
    Get credibility summary for a fact-check's sources.

    Returns:
    - Total number of sources
    - Number of sources with credibility scores
    - Average credibility score (if any sources have scores)
    """
    sources = await get_sources_for_fact_check(db=db, fact_check_id=fact_check_id)
    sources_with_scores = [s for s in sources if s.credibility_score is not None]
    avg_score = await get_average_credibility_score(db=db, fact_check_id=fact_check_id)

    return SourceCredibilityResponse(
        fact_check_id=fact_check_id,
        total_sources=len(sources),
        sources_with_scores=len(sources_with_scores),
        average_credibility=avg_score,
    )


@router.get(
    "/fact-checks/{fact_check_id}/sources/high-credibility",
    response_model=SourceListResponse,
    tags=["sources"],
    summary="Get high-credibility sources",
    description="Get sources with credibility score at or above a threshold.",
)
async def get_high_credibility_sources(
    fact_check_id: UUID,
    min_score: int = Query(
        default=4,
        ge=1,
        le=5,
        description="Minimum credibility score (1-5)",
    ),
    db: AsyncSession = Depends(get_db),
) -> SourceListResponse:
    """
    Get sources with high credibility scores.

    Returns sources with credibility_score >= min_score, ordered by score descending.
    """
    sources = await get_sources_by_min_credibility(
        db=db, fact_check_id=fact_check_id, min_score=min_score
    )

    return SourceListResponse(
        fact_check_id=fact_check_id,
        sources=[SourceResponse.model_validate(s) for s in sources],
        total_count=len(sources),
    )
