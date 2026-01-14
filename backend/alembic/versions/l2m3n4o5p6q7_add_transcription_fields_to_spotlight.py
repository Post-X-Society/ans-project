"""add transcription fields to spotlight contents

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-01-14 10:00:00.000000

Issue #175: Audio Extraction and Whisper Transcription
ADR 0005: EFCSN Compliance Architecture

This migration adds transcription fields to spotlight_contents table:
- transcription (TEXT): The transcribed text from Whisper API
- transcription_language (VARCHAR(10)): Detected language (e.g., 'nl', 'en')
- transcription_confidence (FLOAT): Confidence score from Whisper (0.0-1.0)
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "l2m3n4o5p6q7"
down_revision: Union[str, None] = "k1l2m3n4o5p6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add transcription fields to spotlight_contents table.

    These fields store the results of OpenAI Whisper transcription
    for Snapchat Spotlight video content.
    """
    # Add transcription text field
    op.add_column(
        "spotlight_contents",
        sa.Column("transcription", sa.Text(), nullable=True),
    )

    # Add transcription language field (e.g., 'nl', 'en')
    op.add_column(
        "spotlight_contents",
        sa.Column("transcription_language", sa.String(length=10), nullable=True),
    )

    # Add transcription confidence score (0.0 to 1.0)
    op.add_column(
        "spotlight_contents",
        sa.Column("transcription_confidence", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    """
    Remove transcription fields from spotlight_contents table.
    """
    op.drop_column("spotlight_contents", "transcription_confidence")
    op.drop_column("spotlight_contents", "transcription_language")
    op.drop_column("spotlight_contents", "transcription")
