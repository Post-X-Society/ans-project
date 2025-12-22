"""add workflow transitions audit log

Revision ID: 67b2ef695615
Revises: f65f03a3cc01
Create Date: 2025-12-22 10:00:00.000000

This migration adds:
- workflow_transitions table for immutable audit logging of state changes
- workflow_state, requires_peer_review, peer_review_reason columns to submissions table
- Indexes for optimized query performance
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "67b2ef695615"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# WorkflowState enum values
WORKFLOW_STATES = (
    "submitted",
    "claim_extraction",
    "pending_review",
    "under_review",
    "peer_review_required",
    "peer_review",
    "completed",
    "rejected",
)


def upgrade() -> None:
    """
    Add workflow transitions audit log table and workflow fields to submissions.

    Changes:
    1. Create workflowstate enum type
    2. Add workflow_state, requires_peer_review, peer_review_reason to submissions
    3. Create workflow_transitions table with proper indexes
    """
    # Create the enum type manually using raw SQL
    # We do this once at the top, then use schema_type to reference the existing type
    from sqlalchemy.dialects import postgresql

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'workflowstate') THEN
                CREATE TYPE workflowstate AS ENUM (
                    'submitted', 'claim_extraction', 'pending_review', 'under_review',
                    'peer_review_required', 'peer_review', 'completed', 'rejected'
                );
            END IF;
        END$$;
    """)

    # Reference the existing enum type (don't create it)
    workflow_state_enum = postgresql.ENUM(
        *WORKFLOW_STATES,
        name="workflowstate",
        create_type=False,
        schema_type=False,  # Don't try to manage the type
    )

    # Add new columns to submissions table
    op.add_column(
        "submissions",
        sa.Column(
            "workflow_state",
            workflow_state_enum,
            nullable=True,  # Initially nullable for existing rows
        ),
    )
    op.add_column(
        "submissions",
        sa.Column(
            "requires_peer_review",
            sa.Boolean(),
            nullable=True,  # Initially nullable for existing rows
        ),
    )
    op.add_column(
        "submissions",
        sa.Column(
            "peer_review_reason",
            sa.Text(),
            nullable=True,
        ),
    )

    # Set default values for existing rows
    op.execute("UPDATE submissions SET workflow_state = 'submitted' WHERE workflow_state IS NULL")
    op.execute(
        "UPDATE submissions SET requires_peer_review = FALSE WHERE requires_peer_review IS NULL"
    )

    # Make workflow_state and requires_peer_review NOT NULL after populating defaults
    op.alter_column("submissions", "workflow_state", nullable=False)
    op.alter_column("submissions", "requires_peer_review", nullable=False)

    # Create index on workflow_state for query optimization
    op.create_index(
        "ix_submissions_workflow_state",
        "submissions",
        ["workflow_state"],
        unique=False,
    )

    # Create workflow_transitions table
    op.create_table(
        "workflow_transitions",
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
        sa.Column("submission_id", sa.UUID(), nullable=False),
        sa.Column(
            "from_state",
            workflow_state_enum,
            nullable=True,  # Null for initial transition
        ),
        sa.Column(
            "to_state",
            workflow_state_enum,
            nullable=False,
        ),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("transition_metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["submissions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for query optimization
    op.create_index(
        "idx_workflow_transitions_submission_id",
        "workflow_transitions",
        ["submission_id"],
        unique=False,
    )
    op.create_index(
        "idx_workflow_transitions_actor_id",
        "workflow_transitions",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        "idx_workflow_transitions_created_at",
        "workflow_transitions",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """
    Remove workflow transitions table and workflow fields from submissions.
    """
    # Drop workflow_transitions table and its indexes
    op.drop_index("idx_workflow_transitions_created_at", table_name="workflow_transitions")
    op.drop_index("idx_workflow_transitions_actor_id", table_name="workflow_transitions")
    op.drop_index("idx_workflow_transitions_submission_id", table_name="workflow_transitions")
    op.drop_table("workflow_transitions")

    # Drop new columns from submissions
    op.drop_index("ix_submissions_workflow_state", table_name="submissions")
    op.drop_column("submissions", "peer_review_reason")
    op.drop_column("submissions", "requires_peer_review")
    op.drop_column("submissions", "workflow_state")

    # Drop the enum type
    workflow_state_enum = sa.Enum(*WORKFLOW_STATES, name="workflowstate")
    workflow_state_enum.drop(op.get_bind(), checkfirst=True)
