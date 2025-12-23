"""add peer_review tables

Revision ID: b3c4d5e6f7a8
Revises: 67b2ef695615
Create Date: 2025-12-22 12:00:00.000000

Issue #63: Database Schema for Peer Review Tables
"""

from typing import Any, Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "67b2ef695615"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create peer_reviews and peer_review_triggers tables."""
    # STEP 1: Create enums using raw SQL with IF NOT EXISTS
    # This prevents duplicate enum errors on fresh database deployments

    # Create approval_status enum for peer_reviews
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approvalstatus') THEN
                CREATE TYPE approvalstatus AS ENUM ('pending', 'approved', 'rejected');
            END IF;
        END$$;
        """
    )

    # Create trigger_type enum for peer_review_triggers
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'triggertype') THEN
                CREATE TYPE triggertype AS ENUM (
                    'political_keyword',
                    'engagement_threshold',
                    'sensitive_topic',
                    'high_impact'
                );
            END IF;
        END$$;
        """
    )

    # STEP 2: Reference existing enums with create_type=False and schema_type=False
    approval_status_enum = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        name="approvalstatus",
        create_type=False,
        schema_type=False,
    )

    trigger_type_enum = postgresql.ENUM(
        "political_keyword",
        "engagement_threshold",
        "sensitive_topic",
        "high_impact",
        name="triggertype",
        create_type=False,
        schema_type=False,
    )

    # STEP 3: Create peer_reviews table
    op.create_table(
        "peer_reviews",
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
        # Foreign keys
        sa.Column("fact_check_id", sa.UUID(), nullable=False),
        sa.Column("reviewer_id", sa.UUID(), nullable=False),
        # Approval status
        sa.Column(
            "approval_status",
            approval_status_enum,
            nullable=False,
            server_default="pending",
        ),
        # Optional comments
        sa.Column("comments", sa.Text(), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(
            ["fact_check_id"],
            ["fact_checks.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for peer_reviews
    op.create_index(
        op.f("ix_peer_reviews_fact_check_id"),
        "peer_reviews",
        ["fact_check_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_peer_reviews_reviewer_id"),
        "peer_reviews",
        ["reviewer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_peer_reviews_approval_status"),
        "peer_reviews",
        ["approval_status"],
        unique=False,
    )

    # STEP 4: Create peer_review_triggers table
    op.create_table(
        "peer_review_triggers",
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
        # Trigger type
        sa.Column("trigger_type", trigger_type_enum, nullable=False),
        # Enabled flag
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        # Threshold value (JSONB for PostgreSQL, JSON for others)
        sa.Column("threshold_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Optional description
        sa.Column("description", sa.Text(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index for trigger_type
    op.create_index(
        op.f("ix_peer_review_triggers_trigger_type"),
        "peer_review_triggers",
        ["trigger_type"],
        unique=False,
    )

    # STEP 5: Seed default triggers
    seed_default_triggers()


def seed_default_triggers() -> None:
    """Seed the default peer review triggers."""
    import uuid

    from sqlalchemy import text

    default_triggers: list[dict[str, Any]] = [
        {
            "id": str(uuid.uuid4()),
            "trigger_type": "political_keyword",
            "enabled": True,
            "threshold_value": {
                "keywords": [
                    "election",
                    "vote",
                    "politician",
                    "referendum",
                    "parliament",
                    "government",
                    "political party",
                    "campaign",
                    "ballot",
                    "democracy",
                ],
                "min_occurrences": 1,
                "case_sensitive": False,
            },
            "description": "Triggers peer review for content containing political keywords",
        },
        {
            "id": str(uuid.uuid4()),
            "trigger_type": "engagement_threshold",
            "enabled": True,
            "threshold_value": {
                "min_views": 10000,
                "min_shares": 500,
                "min_comments": 100,
            },
            "description": "Triggers peer review for high-engagement content",
        },
        {
            "id": str(uuid.uuid4()),
            "trigger_type": "sensitive_topic",
            "enabled": True,
            "threshold_value": {
                "topics": [
                    "health",
                    "medicine",
                    "vaccination",
                    "public safety",
                    "emergency",
                    "crisis",
                ],
                "severity_threshold": 0.7,
            },
            "description": "Triggers peer review for sensitive health and safety topics",
        },
        {
            "id": str(uuid.uuid4()),
            "trigger_type": "high_impact",
            "enabled": True,
            "threshold_value": {
                "impact_score_threshold": 0.8,
                "viral_potential_threshold": 0.7,
            },
            "description": "Triggers peer review for high-impact content with viral potential",
        },
    ]

    connection = op.get_bind()
    import json

    for trigger in default_triggers:
        # Check if trigger already exists (by description)
        result = connection.execute(
            text("SELECT COUNT(*) FROM peer_review_triggers WHERE description = :description"),
            {"description": trigger["description"]},
        )
        count = result.scalar()

        if count == 0:
            connection.execute(
                text(
                    """
                    INSERT INTO peer_review_triggers
                    (id, trigger_type, enabled, threshold_value, description, created_at, updated_at)
                    VALUES
                    (CAST(:id AS uuid), :trigger_type, :enabled, :threshold_value, :description, now(), now())
                    """
                ),
                {
                    "id": trigger["id"],
                    "trigger_type": trigger["trigger_type"],
                    "enabled": trigger["enabled"],
                    "threshold_value": json.dumps(trigger["threshold_value"]),
                    "description": trigger["description"],
                },
            )


def downgrade() -> None:
    """Drop peer_reviews and peer_review_triggers tables."""
    # Drop indexes and tables in reverse order
    op.drop_index(
        op.f("ix_peer_review_triggers_trigger_type"),
        table_name="peer_review_triggers",
    )
    op.drop_table("peer_review_triggers")

    op.drop_index(
        op.f("ix_peer_reviews_approval_status"),
        table_name="peer_reviews",
    )
    op.drop_index(op.f("ix_peer_reviews_reviewer_id"), table_name="peer_reviews")
    op.drop_index(op.f("ix_peer_reviews_fact_check_id"), table_name="peer_reviews")
    op.drop_table("peer_reviews")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS triggertype CASCADE")
    op.execute("DROP TYPE IF EXISTS approvalstatus CASCADE")
