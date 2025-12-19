"""add spotlight content table

Revision ID: d58eee634f3a
Revises: 361544390a58
Create Date: 2025-12-18 12:19:53.085434

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d58eee634f3a"
down_revision: Union[str, None] = "361544390a58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create spotlight_contents table
    op.create_table(
        "spotlight_contents",
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
        sa.Column("spotlight_link", sa.String(length=500), nullable=False),
        sa.Column("spotlight_id", sa.String(length=200), nullable=False),
        sa.Column("video_url", sa.Text(), nullable=False),
        sa.Column("video_local_path", sa.String(length=500), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("creator_username", sa.String(length=200), nullable=True),
        sa.Column("creator_name", sa.String(length=200), nullable=True),
        sa.Column("creator_url", sa.String(length=500), nullable=True),
        sa.Column("view_count", sa.BigInteger(), nullable=True),
        sa.Column("share_count", sa.Integer(), nullable=True),
        sa.Column("comment_count", sa.Integer(), nullable=True),
        sa.Column("boost_count", sa.Integer(), nullable=True),
        sa.Column("recommend_count", sa.Integer(), nullable=True),
        sa.Column("upload_timestamp", sa.BigInteger(), nullable=True),
        sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["submissions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_spotlight_contents_submission_id"),
        "spotlight_contents",
        ["submission_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_spotlight_contents_spotlight_id"),
        "spotlight_contents",
        ["spotlight_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_spotlight_contents_spotlight_id"), table_name="spotlight_contents")
    op.drop_index(op.f("ix_spotlight_contents_submission_id"), table_name="spotlight_contents")
    op.drop_table("spotlight_contents")
