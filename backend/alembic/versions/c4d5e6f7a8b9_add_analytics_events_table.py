"""add analytics events table

Revision ID: c4d5e6f7a8b9
Revises: 67b2ef695615
Create Date: 2025-12-22 12:00:00.000000

This migration adds:
- analytics_events table for EFCSN compliance tracking
- Indexes for time-series queries and entity lookups
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "67b2ef695615"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create analytics_events table with indexes for time-series queries.

    The table tracks analytics events (views, shares, correction requests, etc.)
    for EFCSN compliance dashboard metrics.
    """
    # Create analytics_events table
    op.create_table(
        "analytics_events",
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
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("event_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create single-column indexes for simple filtering
    op.create_index(
        "ix_analytics_events_event_type",
        "analytics_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_analytics_events_entity_type",
        "analytics_events",
        ["entity_type"],
        unique=False,
    )
    op.create_index(
        "ix_analytics_events_occurred_at",
        "analytics_events",
        ["occurred_at"],
        unique=False,
    )

    # Create composite index for entity lookups (entity_type + entity_id)
    op.create_index(
        "idx_analytics_events_entity",
        "analytics_events",
        ["entity_type", "entity_id"],
        unique=False,
    )

    # Create composite index for time-series filtering by event type
    op.create_index(
        "idx_analytics_events_type_occurred",
        "analytics_events",
        ["event_type", "occurred_at"],
        unique=False,
    )

    # Create composite index for time-series filtering by entity type
    op.create_index(
        "idx_analytics_events_entity_type_occurred",
        "analytics_events",
        ["entity_type", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    """
    Remove analytics_events table and all its indexes.
    """
    # Drop composite indexes
    op.drop_index("idx_analytics_events_entity_type_occurred", table_name="analytics_events")
    op.drop_index("idx_analytics_events_type_occurred", table_name="analytics_events")
    op.drop_index("idx_analytics_events_entity", table_name="analytics_events")

    # Drop single-column indexes
    op.drop_index("ix_analytics_events_occurred_at", table_name="analytics_events")
    op.drop_index("ix_analytics_events_entity_type", table_name="analytics_events")
    op.drop_index("ix_analytics_events_event_type", table_name="analytics_events")

    # Drop table
    op.drop_table("analytics_events")
