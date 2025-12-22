"""add corrections tables

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2025-12-22 18:00:00.000000

Issue #75: Database Schema for Corrections Tables
EFCSN-compliant corrections system with:
- corrections table for correction requests
- correction_applications table for applied corrections with versioning
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
    """Create corrections and correction_applications tables."""
    # STEP 1: Create enums using raw SQL with IF NOT EXISTS
    # This prevents duplicate enum errors on fresh database deployments

    # Create correctiontype enum
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'correctiontype') THEN
                CREATE TYPE correctiontype AS ENUM ('minor', 'update', 'substantial');
            END IF;
        END$$;
        """
    )

    # Create correctionstatus enum
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'correctionstatus') THEN
                CREATE TYPE correctionstatus AS ENUM ('pending', 'accepted', 'rejected');
            END IF;
        END$$;
        """
    )

    # STEP 2: Reference existing enums with create_type=False and schema_type=False
    correction_type_enum = postgresql.ENUM(
        "minor",
        "update",
        "substantial",
        name="correctiontype",
        create_type=False,
        schema_type=False,
    )

    correction_status_enum = postgresql.ENUM(
        "pending",
        "accepted",
        "rejected",
        name="correctionstatus",
        create_type=False,
        schema_type=False,
    )

    # STEP 3: Create corrections table
    op.create_table(
        "corrections",
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
        # Foreign key to fact_check
        sa.Column("fact_check_id", sa.UUID(), nullable=False),
        # Correction type
        sa.Column(
            "correction_type",
            correction_type_enum,
            nullable=False,
        ),
        # Requester information (optional for anonymous corrections)
        sa.Column("requester_email", sa.String(255), nullable=True),
        # Request details (required)
        sa.Column("request_details", sa.Text(), nullable=False),
        # Status
        sa.Column(
            "status",
            correction_status_enum,
            nullable=False,
            server_default="pending",
        ),
        # Reviewer information
        sa.Column("reviewed_by_id", sa.UUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        # SLA deadline
        sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(
            ["fact_check_id"],
            ["fact_checks.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for corrections
    op.create_index(
        op.f("ix_corrections_fact_check_id"),
        "corrections",
        ["fact_check_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_corrections_status"),
        "corrections",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_corrections_reviewed_by_id"),
        "corrections",
        ["reviewed_by_id"],
        unique=False,
    )

    # STEP 4: Create correction_applications table
    op.create_table(
        "correction_applications",
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
        # Foreign key to correction
        sa.Column("correction_id", sa.UUID(), nullable=False),
        # User who applied the correction
        sa.Column("applied_by_id", sa.UUID(), nullable=False),
        # Version number
        sa.Column("version", sa.Integer(), nullable=False),
        # When applied
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Changes summary
        sa.Column("changes_summary", sa.Text(), nullable=False),
        # Content snapshots (JSONB for PostgreSQL)
        sa.Column("previous_content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("new_content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        # Current version flag
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        # Constraints
        sa.ForeignKeyConstraint(
            ["correction_id"],
            ["corrections.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["applied_by_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for correction_applications
    op.create_index(
        op.f("ix_correction_applications_correction_id"),
        "correction_applications",
        ["correction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_correction_applications_applied_by_id"),
        "correction_applications",
        ["applied_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_correction_applications_is_current"),
        "correction_applications",
        ["is_current"],
        unique=False,
    )


def downgrade() -> None:
    """Drop corrections and correction_applications tables."""
    # Drop indexes and tables in reverse order
    op.drop_index(
        op.f("ix_correction_applications_is_current"),
        table_name="correction_applications",
    )
    op.drop_index(
        op.f("ix_correction_applications_applied_by_id"),
        table_name="correction_applications",
    )
    op.drop_index(
        op.f("ix_correction_applications_correction_id"),
        table_name="correction_applications",
    )
    op.drop_table("correction_applications")

    op.drop_index(
        op.f("ix_corrections_reviewed_by_id"),
        table_name="corrections",
    )
    op.drop_index(
        op.f("ix_corrections_status"),
        table_name="corrections",
    )
    op.drop_index(
        op.f("ix_corrections_fact_check_id"),
        table_name="corrections",
    )
    op.drop_table("corrections")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS correctionstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS correctiontype CASCADE")
