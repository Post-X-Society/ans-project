"""
Source model for tracking evidence sources in fact checks
Issue #69: Database Schema: Sources Table
"""

import enum
from datetime import date
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.fact_check import FactCheck


class SourceType(str, enum.Enum):
    """Source type enumeration for categorizing evidence sources"""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    EXPERT = "expert"
    MEDIA = "media"
    GOVERNMENT = "government"
    ACADEMIC = "academic"


class SourceRelevance(str, enum.Enum):
    """Source relevance enumeration for categorizing how a source relates to a claim"""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXTUALIZES = "contextualizes"


class Source(TimeStampedModel):
    """
    Source model for tracking evidence sources used in fact checks.

    This model supports the EFCSN compliance requirement for comprehensive
    source documentation. Each source includes:
    - Type categorization (primary, secondary, expert, etc.)
    - URL and title for reference
    - Publication and access dates for temporal tracking
    - Credibility scoring (1-5)
    - Relevance classification (supports, contradicts, contextualizes)
    - Archive URL for reproducibility
    - Notes for additional context

    Attributes:
        fact_check_id: Reference to the fact check this source supports
        source_type: Category of the source (primary, secondary, etc.)
        title: Title or description of the source
        url: URL to the source (if available online)
        publication_date: Date the source was published
        access_date: Date when the source was accessed
        credibility_score: Credibility rating from 1-5
        relevance: How the source relates to the claim
        archived_url: Archived URL (e.g., Wayback Machine)
        notes: Additional notes about the source
    """

    __tablename__ = "sources"

    # Foreign key to fact_checks with cascade delete
    fact_check_id: Mapped[UUID] = mapped_column(
        ForeignKey("fact_checks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source type (required)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True,
    )

    # Title (required)
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # URL (optional)
    url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Publication date (optional)
    publication_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Access date (required - when the source was accessed)
    access_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Credibility score (optional, 1-5)
    # Note: Database-level CHECK constraint is added in migration
    credibility_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relevance (optional)
    relevance: Mapped[Optional[SourceRelevance]] = mapped_column(
        Enum(SourceRelevance, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
        index=True,
    )

    # Archived URL (optional - e.g., Wayback Machine snapshot)
    archived_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Notes (optional - additional context about the source)
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    fact_check: Mapped["FactCheck"] = relationship(
        "FactCheck",
        back_populates="source_records",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, type={self.source_type.value}, title={self.title[:30]}...)>"
