"""Add rtbf_requests table for Right to be Forgotten workflow

Issue #92: Backend: Right to be Forgotten Workflow (TDD)
Part of EPIC #53: GDPR & Data Retention Compliance

- Add rtbf_requests table for tracking RTBF requests
- Support for minor detection (automatic approval for users <18)
- Deletion summary storage for audit trail

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-01-06 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "j0k1l2m3n4o5"
down_revision: Union[str, None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add rtbf_requests table for GDPR Right to be Forgotten requests."""

    # Create RTBFRequestStatus enum using raw SQL with IF NOT EXISTS
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rtbfrequeststatus') THEN
                CREATE TYPE rtbfrequeststatus AS ENUM (
                    'pending', 'processing', 'completed', 'rejected'
                );
            END IF;
        END$$;
        """
    )

    # Reference the enum
    rtbf_status_enum = sa.Enum(
        "pending",
        "processing",
        "completed",
        "rejected",
        name="rtbfrequeststatus",
        create_type=False,
    )

    # Create rtbf_requests table
    op.create_table(
        "rtbf_requests",
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
        # Foreign key to user requesting deletion
        sa.Column("user_id", sa.UUID(), nullable=False),
        # Reason for the request
        sa.Column("reason", sa.Text(), nullable=False),
        # Request status
        sa.Column(
            "status",
            rtbf_status_enum,
            nullable=False,
            server_default="pending",
        ),
        # Date of birth for minor detection (optional)
        sa.Column("requester_date_of_birth", sa.Date(), nullable=True),
        # Processing information
        sa.Column("processed_by_id", sa.UUID(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Rejection information
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        # Deletion summary (JSONB for PostgreSQL)
        sa.Column("deletion_summary", JSONB, nullable=True),
        # Email for notifications (stored separately in case user is deleted)
        sa.Column("notification_email", sa.String(255), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["processed_by_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for efficient querying
    op.create_index(
        op.f("ix_rtbf_requests_user_id"),
        "rtbf_requests",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rtbf_requests_status"),
        "rtbf_requests",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rtbf_requests_processed_by_id"),
        "rtbf_requests",
        ["processed_by_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop rtbf_requests table."""

    # Drop indexes
    op.drop_index(
        op.f("ix_rtbf_requests_processed_by_id"),
        table_name="rtbf_requests",
    )
    op.drop_index(
        op.f("ix_rtbf_requests_status"),
        table_name="rtbf_requests",
    )
    op.drop_index(
        op.f("ix_rtbf_requests_user_id"),
        table_name="rtbf_requests",
    )

    # Drop table
    op.drop_table("rtbf_requests")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS rtbfrequeststatus CASCADE")
