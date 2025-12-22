"""
RatingDefinition model for EFCSN rating categories

This model stores the 6 EFCSN rating definitions with multilingual support.
Each rating has a unique key, title, description (in JSONB for i18n),
visual styling information, and display order.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# Cross-database compatible JSON type: uses JSON for SQLite, JSONB for PostgreSQL
JSONType = JSON().with_variant(JSONB, "postgresql")


class RatingDefinition(Base):
    """
    Rating definition model for EFCSN fact-check ratings.

    Stores the 6 standard EFCSN ratings:
    - TRUE: Claim is accurate
    - PARTLY_FALSE: Claim contains some false elements
    - FALSE: Claim is inaccurate
    - MISSING_CONTEXT: Claim lacks important context
    - ALTERED: Content has been digitally altered
    - SATIRE: Content is satirical

    Attributes:
        id: Unique identifier (UUID)
        rating_key: Unique identifier key (e.g., 'TRUE', 'FALSE')
        title: Multilingual title as JSONB (e.g., {"en": "True", "nl": "Waar"})
        description: Multilingual description as JSONB
        visual_color: Hex color code for UI display (e.g., "#00AA00")
        icon_name: Icon identifier for UI (e.g., "check-circle")
        display_order: Order for display in UI
        created_at: Timestamp when record was created
    """

    __tablename__ = "rating_definitions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    rating_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    description: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    visual_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    icon_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<RatingDefinition(rating_key={self.rating_key}, display_order={self.display_order})>"
        )
