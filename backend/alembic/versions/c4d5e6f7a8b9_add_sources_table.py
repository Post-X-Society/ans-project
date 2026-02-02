"""add sources table

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2025-12-22 14:00:00.000000

Issue #69: Database Schema: Sources Table
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create sources table and add sources_count to fact_checks."""
    # STEP 1: Create enums using raw SQL with IF NOT EXISTS
    # This prevents duplicate enum errors on fresh database deployments

    # Create sourcetype enum
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sourcetype') THEN
                CREATE TYPE sourcetype AS ENUM (
                    'primary',
                    'secondary',
                    'expert',
                    'media',
                    'government',
                    'academic'
                );
            END IF;
        END$$;
        """)

    # Create sourcerelevance enum
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sourcerelevance') THEN
                CREATE TYPE sourcerelevance AS ENUM (
                    'supports',
                    'contradicts',
                    'contextualizes'
                );
            END IF;
        END$$;
        """)

    # STEP 2: Reference existing enums with create_type=False and schema_type=False
    source_type_enum = postgresql.ENUM(
        "primary",
        "secondary",
        "expert",
        "media",
        "government",
        "academic",
        name="sourcetype",
        create_type=False,
        schema_type=False,
    )

    source_relevance_enum = postgresql.ENUM(
        "supports",
        "contradicts",
        "contextualizes",
        name="sourcerelevance",
        create_type=False,
        schema_type=False,
    )

    # STEP 3: Create sources table
    op.create_table(
        "sources",
        # Primary key and timestamps (from TimeStampedModel)
        sa.Column("id", sa.UUID(), nullable=False),
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
        # Foreign key to fact_checks
        sa.Column("fact_check_id", sa.UUID(), nullable=False),
        # Source type (required)
        sa.Column("source_type", source_type_enum, nullable=False),
        # Title (required)
        sa.Column("title", sa.String(500), nullable=False),
        # URL (optional)
        sa.Column("url", sa.Text(), nullable=True),
        # Publication date (optional)
        sa.Column("publication_date", sa.Date(), nullable=True),
        # Access date (required)
        sa.Column("access_date", sa.Date(), nullable=False),
        # Credibility score (optional, 1-5)
        sa.Column("credibility_score", sa.Integer(), nullable=True),
        # Relevance (optional)
        sa.Column("relevance", source_relevance_enum, nullable=True),
        # Archived URL (optional)
        sa.Column("archived_url", sa.Text(), nullable=True),
        # Notes (optional)
        sa.Column("notes", sa.Text(), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(
            ["fact_check_id"],
            ["fact_checks.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        # Check constraint for credibility_score (1-5)
        sa.CheckConstraint(
            "credibility_score IS NULL OR (credibility_score >= 1 AND credibility_score <= 5)",
            name="ck_sources_credibility_score_range",
        ),
    )

    # STEP 4: Create indexes for sources table
    op.create_index(
        op.f("ix_sources_fact_check_id"),
        "sources",
        ["fact_check_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sources_source_type"),
        "sources",
        ["source_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sources_relevance"),
        "sources",
        ["relevance"],
        unique=False,
    )

    # STEP 5: Add sources_count column to fact_checks table
    op.add_column(
        "fact_checks",
        sa.Column(
            "sources_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    """Drop sources table and remove sources_count from fact_checks."""
    # Remove sources_count column from fact_checks
    op.drop_column("fact_checks", "sources_count")

    # Drop indexes
    op.drop_index(op.f("ix_sources_relevance"), table_name="sources")
    op.drop_index(op.f("ix_sources_source_type"), table_name="sources")
    op.drop_index(op.f("ix_sources_fact_check_id"), table_name="sources")

    # Drop sources table
    op.drop_table("sources")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS sourcerelevance CASCADE")
    op.execute("DROP TYPE IF EXISTS sourcetype CASCADE")
