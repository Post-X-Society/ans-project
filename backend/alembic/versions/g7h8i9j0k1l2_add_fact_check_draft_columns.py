"""add fact check draft columns

Revision ID: g7h8i9j0k1l2
Revises: e6f7a8b9c0d1
Create Date: 2025-12-27 12:00:00.000000

Issue #123: Backend: Fact-Check Draft Storage API (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine

This migration adds:
- draft_content (JSONB) column to fact_checks table for storing reviewer work-in-progress
- draft_updated_at (TIMESTAMP) column for audit tracking
- Index on draft_updated_at for query optimization
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g7h8i9j0k1l2"
down_revision: Union[str, None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add draft_content and draft_updated_at columns to fact_checks table."""
    # Add draft_content column (JSONB for PostgreSQL)
    op.add_column(
        "fact_checks",
        sa.Column(
            "draft_content",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    # Add draft_updated_at column for audit tracking
    op.add_column(
        "fact_checks",
        sa.Column(
            "draft_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Create index on draft_updated_at for efficient queries
    op.create_index(
        op.f("ix_fact_checks_draft_updated_at"),
        "fact_checks",
        ["draft_updated_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove draft_content and draft_updated_at columns from fact_checks table."""
    # Drop index
    op.drop_index(
        op.f("ix_fact_checks_draft_updated_at"),
        table_name="fact_checks",
    )

    # Drop columns
    op.drop_column("fact_checks", "draft_updated_at")
    op.drop_column("fact_checks", "draft_content")
