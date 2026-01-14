"""add submitter_comment to submissions table

Revision ID: m3n4o5p6q7r8
Revises: l2m3n4o5p6q7
Create Date: 2026-01-14 15:00:00.000000

Issue #177: Add Submitter Comment Field to Submission Form

This migration adds an optional submitter_comment field to the submissions table,
allowing users to provide context about why content requires fact-checking.
The field is limited to 500 characters and is nullable for backward compatibility.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "m3n4o5p6q7r8"
down_revision: Union[str, None] = "l2m3n4o5p6q7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add submitter_comment column to submissions table.

    This optional text field allows users to provide additional context
    when submitting content for fact-checking. Maximum length is 500 characters.
    """
    op.add_column(
        "submissions",
        sa.Column(
            "submitter_comment",
            sa.Text(),
            nullable=True,
            comment="Optional comment from submitter providing context (max 500 chars)",
        ),
    )


def downgrade() -> None:
    """
    Remove submitter_comment column from submissions table.
    """
    op.drop_column("submissions", "submitter_comment")
