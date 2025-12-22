"""add fact_check_ratings table

Revision ID: a2b3c4d5e6f7
Revises: f65f03a3cc01
Create Date: 2025-12-22 10:00:00.000000

Issue #56: Database Schema for Fact Check Rating History
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create fact_check_ratings table for versioned rating history with justifications."""
    op.create_table(
        "fact_check_ratings",
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
        sa.Column("assigned_by_id", sa.UUID(), nullable=False),
        # Rating data
        sa.Column("rating", sa.String(50), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        # Versioning support
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        # Assignment timestamp
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Constraints
        sa.ForeignKeyConstraint(
            ["fact_check_id"],
            ["fact_checks.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create indexes for query performance
    op.create_index(
        op.f("ix_fact_check_ratings_fact_check_id"),
        "fact_check_ratings",
        ["fact_check_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fact_check_ratings_is_current"),
        "fact_check_ratings",
        ["is_current"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fact_check_ratings_assigned_by_id"),
        "fact_check_ratings",
        ["assigned_by_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop fact_check_ratings table."""
    op.drop_index(op.f("ix_fact_check_ratings_assigned_by_id"), table_name="fact_check_ratings")
    op.drop_index(op.f("ix_fact_check_ratings_is_current"), table_name="fact_check_ratings")
    op.drop_index(op.f("ix_fact_check_ratings_fact_check_id"), table_name="fact_check_ratings")
    op.drop_table("fact_check_ratings")
