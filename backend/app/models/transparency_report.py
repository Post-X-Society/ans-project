"""
TransparencyReport model for storing automated monthly transparency reports.

Issue #89: Backend - Automated Monthly Transparency Reports (TDD)
EPIC #52: Analytics & EFCSN Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

Stores:
- Monthly transparency reports with analytics data
- Publication status and timestamps
- JSON report data for PDF/CSV export
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.models.base import Base

# Cross-database compatible JSONB type (JSONB for PostgreSQL, JSON for SQLite)
JSONType = JSON().with_variant(JSONB, "postgresql")


class TransparencyReport(Base):
    """
    Model for storing monthly transparency reports.

    Attributes:
        id: Unique identifier
        year: Report year (e.g., 2025)
        month: Report month (1-12)
        report_data: JSON containing all report metrics
        is_published: Whether report is publicly visible
        published_at: When report was published
        generated_at: When report was generated
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "transparency_reports"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Report period
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Report content (JSON with all analytics data)
    report_data: Mapped[dict[str, Any]] = mapped_column(
        JSONType,
        nullable=False,
        default=dict,
        doc="JSON containing all report metrics and data",
    )

    # Report title (multilingual)
    title: Mapped[dict[str, str]] = mapped_column(
        JSONType,
        nullable=False,
        default=lambda: {"en": "", "nl": ""},
        doc="Multilingual report title",
    )

    # Report summary (multilingual)
    summary: Mapped[dict[str, str]] = mapped_column(
        JSONType,
        nullable=False,
        default=lambda: {"en": "", "nl": ""},
        doc="Multilingual report summary",
    )

    # Publication status
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Generation timestamp
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Standard timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        """String representation of the report."""
        status: str = "Published" if self.is_published else "Draft"
        return f"<TransparencyReport {self.year}-{self.month:02d} ({status})>"
