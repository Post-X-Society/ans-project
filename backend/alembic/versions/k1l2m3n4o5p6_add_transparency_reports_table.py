"""add transparency reports table

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2025-12-23 12:00:00.000000

Issue #89: Backend - Automated Monthly Transparency Reports (TDD)
EPIC #52: Analytics & EFCSN Compliance Dashboard
ADR 0005: EFCSN Compliance Architecture

This migration adds:
- transparency_reports table for storing monthly EFCSN transparency reports
- Indexes for year/month and publication status
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "k1l2m3n4o5p6"
down_revision: Union[str, None] = "j0k1l2m3n4o5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create transparency_reports table with indexes.

    The table stores monthly transparency reports for EFCSN compliance,
    including report data, publication status, and multilingual content.
    """
    # Create transparency_reports table
    op.create_table(
        "transparency_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("report_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "title",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='{"en": "", "nl": ""}',
        ),
        sa.Column(
            "summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='{"en": "", "nl": ""}',
        ),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index on year for filtering by year
    op.create_index(
        "ix_transparency_reports_year",
        "transparency_reports",
        ["year"],
        unique=False,
    )

    # Create index on month for filtering by month
    op.create_index(
        "ix_transparency_reports_month",
        "transparency_reports",
        ["month"],
        unique=False,
    )

    # Create index on is_published for filtering published reports
    op.create_index(
        "ix_transparency_reports_is_published",
        "transparency_reports",
        ["is_published"],
        unique=False,
    )

    # Create unique composite index on year+month (only one report per month)
    op.create_index(
        "idx_transparency_reports_year_month",
        "transparency_reports",
        ["year", "month"],
        unique=True,
    )


def downgrade() -> None:
    """
    Remove transparency_reports table and all its indexes.
    """
    # Drop indexes
    op.drop_index("idx_transparency_reports_year_month", table_name="transparency_reports")
    op.drop_index("ix_transparency_reports_is_published", table_name="transparency_reports")
    op.drop_index("ix_transparency_reports_month", table_name="transparency_reports")
    op.drop_index("ix_transparency_reports_year", table_name="transparency_reports")

    # Drop table
    op.drop_table("transparency_reports")
