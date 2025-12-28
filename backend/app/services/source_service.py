"""
Source Service for managing evidence sources in fact-checks.

Issue #70: Backend: Source Management Service (TDD)
EPIC #49: Evidence & Source Management
ADR 0005: EFCSN Compliance Architecture

This service provides:
- Full CRUD functionality for sources
- Automatic citation numbering ([1], [2], [3])
- Source count tracking for fact-checks
- Minimum 2-source validation before publishing
- Credibility scoring mechanism (1-5 scale)
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fact_check import FactCheck
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate

# Minimum number of sources required for publishing (EFCSN requirement)
MINIMUM_SOURCES_REQUIRED = 2


class SourceServiceError(Exception):
    """Base exception for Source Service errors."""

    pass


class SourceValidationError(SourceServiceError):
    """Raised when validation fails (e.g., entity not found)."""

    pass


class InsufficientSourcesError(SourceServiceError):
    """Raised when fact-check doesn't have enough sources for publishing."""

    pass


async def _get_fact_check(db: AsyncSession, fact_check_id: UUID) -> FactCheck:
    """Retrieve fact-check by ID or raise SourceValidationError if not found."""
    stmt = select(FactCheck).where(FactCheck.id == fact_check_id)
    result = await db.execute(stmt)
    fact_check = result.scalar_one_or_none()

    if fact_check is None:
        raise SourceValidationError(f"FactCheck with ID {fact_check_id} not found")

    return fact_check


async def _get_source(db: AsyncSession, source_id: UUID) -> Source:
    """Retrieve source by ID or raise SourceValidationError if not found."""
    stmt = select(Source).where(Source.id == source_id)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()

    if source is None:
        raise SourceValidationError(f"Source with ID {source_id} not found")

    return source


async def _update_fact_check_sources_count(db: AsyncSession, fact_check_id: UUID) -> None:
    """Update the sources_count on a fact-check based on actual source count."""
    stmt = select(func.count()).where(Source.fact_check_id == fact_check_id)
    result = await db.execute(stmt)
    count = result.scalar() or 0

    fact_check = await _get_fact_check(db, fact_check_id)
    fact_check.sources_count = count
    await db.flush()


# =============================================================================
# CRUD Operations
# =============================================================================


async def create_source(db: AsyncSession, source_data: SourceCreate) -> Source:
    """Create a new source for a fact-check.

    Args:
        db: Async database session
        source_data: Source creation data

    Returns:
        The newly created Source

    Raises:
        SourceValidationError: If fact-check not found
    """
    # Validate fact-check exists
    await _get_fact_check(db, source_data.fact_check_id)

    # Create source
    source = Source(
        fact_check_id=source_data.fact_check_id,
        source_type=source_data.source_type,
        title=source_data.title,
        url=source_data.url,
        publication_date=source_data.publication_date,
        access_date=source_data.access_date,
        credibility_score=source_data.credibility_score,
        relevance=source_data.relevance,
        archived_url=source_data.archived_url,
        notes=source_data.notes,
    )

    db.add(source)
    await db.flush()

    # Update fact-check sources count
    await _update_fact_check_sources_count(db, source_data.fact_check_id)

    await db.commit()
    await db.refresh(source)

    return source


async def get_source(db: AsyncSession, source_id: UUID) -> Source:
    """Retrieve a source by ID.

    Args:
        db: Async database session
        source_id: UUID of the source

    Returns:
        The Source object

    Raises:
        SourceValidationError: If source not found
    """
    return await _get_source(db, source_id)


async def get_sources_for_fact_check(db: AsyncSession, fact_check_id: UUID) -> list[Source]:
    """Retrieve all sources for a fact-check.

    Args:
        db: Async database session
        fact_check_id: UUID of the fact-check

    Returns:
        List of Source objects ordered by creation date
    """
    stmt = (
        select(Source)
        .where(Source.fact_check_id == fact_check_id)
        .order_by(Source.created_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_source(db: AsyncSession, source_id: UUID, update_data: SourceUpdate) -> Source:
    """Update an existing source.

    Args:
        db: Async database session
        source_id: UUID of the source to update
        update_data: Fields to update

    Returns:
        The updated Source

    Raises:
        SourceValidationError: If source not found
    """
    source = await _get_source(db, source_id)

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)

    return source


async def delete_source(db: AsyncSession, source_id: UUID) -> None:
    """Delete a source.

    Args:
        db: Async database session
        source_id: UUID of the source to delete

    Raises:
        SourceValidationError: If source not found
    """
    source = await _get_source(db, source_id)
    fact_check_id = source.fact_check_id

    await db.delete(source)
    await db.flush()

    # Update fact-check sources count
    await _update_fact_check_sources_count(db, fact_check_id)

    await db.commit()


# =============================================================================
# Citation Numbering
# =============================================================================


def format_citation(citation_number: int) -> str:
    """Format a citation number as a string.

    Args:
        citation_number: The citation number (1, 2, 3, etc.)

    Returns:
        Formatted citation string (e.g., "[1]", "[2]")
    """
    return f"[{citation_number}]"


async def get_sources_with_citations(db: AsyncSession, fact_check_id: UUID) -> list[dict[str, Any]]:
    """Get all sources for a fact-check with citation numbers.

    Sources are numbered in order of creation (first created = [1]).

    Args:
        db: Async database session
        fact_check_id: UUID of the fact-check

    Returns:
        List of dicts with 'source', 'citation_number', and 'citation_string' keys
    """
    sources = await get_sources_for_fact_check(db, fact_check_id)

    return [
        {
            "source": source,
            "citation_number": idx + 1,
            "citation_string": format_citation(idx + 1),
        }
        for idx, source in enumerate(sources)
    ]


# =============================================================================
# Source Count and Validation
# =============================================================================


async def get_source_count(db: AsyncSession, fact_check_id: UUID) -> int:
    """Get the number of sources for a fact-check.

    Args:
        db: Async database session
        fact_check_id: UUID of the fact-check

    Returns:
        Number of sources
    """
    stmt = select(func.count()).select_from(Source).where(Source.fact_check_id == fact_check_id)
    result = await db.execute(stmt)
    return result.scalar() or 0


async def validate_minimum_sources(db: AsyncSession, fact_check_id: UUID) -> bool:
    """Validate that a fact-check has the minimum required sources for publishing.

    EFCSN requires minimum 2 sources per fact-check.

    Args:
        db: Async database session
        fact_check_id: UUID of the fact-check

    Returns:
        True if validation passes

    Raises:
        InsufficientSourcesError: If source count is below minimum
    """
    count = await get_source_count(db, fact_check_id)

    if count < MINIMUM_SOURCES_REQUIRED:
        raise InsufficientSourcesError(
            f"Fact-check requires minimum {MINIMUM_SOURCES_REQUIRED} sources "
            f"for publishing, but only has {count}."
        )

    return True


# =============================================================================
# Credibility Scoring
# =============================================================================


async def get_average_credibility_score(db: AsyncSession, fact_check_id: UUID) -> Optional[float]:
    """Calculate the average credibility score for a fact-check's sources.

    Only sources with credibility scores are included in the calculation.

    Args:
        db: Async database session
        fact_check_id: UUID of the fact-check

    Returns:
        Average credibility score (1.0-5.0), or None if no sources have scores
    """
    stmt = select(func.avg(Source.credibility_score)).where(
        Source.fact_check_id == fact_check_id,
        Source.credibility_score.isnot(None),
    )
    result = await db.execute(stmt)
    avg = result.scalar()

    if avg is None:
        return None

    return float(avg)


async def get_sources_by_min_credibility(
    db: AsyncSession, fact_check_id: UUID, min_score: int
) -> list[Source]:
    """Get sources with credibility score at or above a minimum threshold.

    Args:
        db: Async database session
        fact_check_id: UUID of the fact-check
        min_score: Minimum credibility score (1-5)

    Returns:
        List of Source objects meeting the credibility threshold
    """
    stmt = (
        select(Source)
        .where(
            Source.fact_check_id == fact_check_id,
            Source.credibility_score >= min_score,
        )
        .order_by(Source.credibility_score.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
