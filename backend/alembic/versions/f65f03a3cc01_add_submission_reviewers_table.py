"""add submission reviewers table

Revision ID: f65f03a3cc01
Revises: d58eee634f3a
Create Date: 2025-12-18 12:42:32.363599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f65f03a3cc01'
down_revision: Union[str, None] = 'd58eee634f3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create submission_reviewers table for many-to-many relationship with assignment tracking."""
    op.create_table(
        "submission_reviewers",
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
        sa.Column("reviewer_id", sa.UUID(), nullable=False),
        sa.Column("assigned_by_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["submissions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("submission_id", "reviewer_id", name="uq_submission_reviewer"),
    )
    op.create_index(
        op.f("ix_submission_reviewers_submission_id"),
        "submission_reviewers",
        ["submission_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_submission_reviewers_reviewer_id"),
        "submission_reviewers",
        ["reviewer_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop submission_reviewers table."""
    op.drop_index(op.f("ix_submission_reviewers_reviewer_id"), table_name="submission_reviewers")
    op.drop_index(op.f("ix_submission_reviewers_submission_id"), table_name="submission_reviewers")
    op.drop_table("submission_reviewers")
