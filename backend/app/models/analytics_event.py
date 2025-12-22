"""
AnalyticsEvent model for tracking analytics events.

This model stores analytics events for EFCSN compliance dashboard metrics,
tracking views, shares, correction requests, and other user interactions
with fact-checks, submissions, and other entities.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.models.base import TimeStampedModel

# Cross-database compatible JSONB type (JSONB for PostgreSQL, JSON for SQLite)
JSONType = JSON().with_variant(JSONB, "postgresql")


class AnalyticsEvent(TimeStampedModel):
    """
    Analytics event tracking for EFCSN compliance.

    This table logs all analytics events for the compliance dashboard,
    supporting time-series queries for metrics like:
    - Monthly fact-check views
    - Share counts
    - Correction request rates
    - API access patterns

    Attributes:
        event_type: Type of event (view, share, correction_request, etc.)
        entity_type: Type of entity (fact_check, submission, claim, etc.)
        entity_id: UUID of the entity this event relates to
        event_metadata: Optional JSONB field for event-specific context
        occurred_at: Timestamp when the event actually occurred
    """

    __tablename__ = "analytics_events"

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )
    event_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONType,
        nullable=True,
        default=None,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Indexes for optimized time-series and filtering queries
    __table_args__ = (
        # Composite index for entity lookups (entity_type + entity_id)
        Index("idx_analytics_events_entity", "entity_type", "entity_id"),
        # Composite index for time-series filtering by event type
        Index("idx_analytics_events_type_occurred", "event_type", "occurred_at"),
        # Composite index for time-series filtering by entity type
        Index("idx_analytics_events_entity_type_occurred", "entity_type", "occurred_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AnalyticsEvent(id={self.id}, "
            f"event_type={self.event_type}, "
            f"entity_type={self.entity_type})>"
        )
