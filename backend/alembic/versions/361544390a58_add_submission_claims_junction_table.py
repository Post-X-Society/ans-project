"""add submission claims junction table

Revision ID: 361544390a58
Revises: e015fdaaaad0
Create Date: 2025-12-17 09:57:46.936460

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '361544390a58'
down_revision: Union[str, None] = 'e015fdaaaad0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create submission_claims junction table for many-to-many relationship."""
    op.create_table(
        "submission_claims",
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["submissions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["claims.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("submission_id", "claim_id"),
    )
    op.create_index(
        op.f("ix_submission_claims_submission_id"),
        "submission_claims",
        ["submission_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_submission_claims_claim_id"),
        "submission_claims",
        ["claim_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop submission_claims junction table."""
    op.drop_index(op.f("ix_submission_claims_claim_id"), table_name="submission_claims")
    op.drop_index(op.f("ix_submission_claims_submission_id"), table_name="submission_claims")
    op.drop_table("submission_claims")
