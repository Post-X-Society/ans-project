"""add rating definitions table

Revision ID: a1b2c3d4e5f6
Revises: f65f03a3cc01
Create Date: 2025-12-22

This migration creates the rating_definitions table for EFCSN rating categories
and seeds the 6 standard EFCSN ratings with EN/NL translations.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f65f03a3cc01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# EFCSN Rating definitions with multilingual content
EFCSN_RATINGS = [
    {
        "rating_key": "TRUE",
        "title": {"en": "True", "nl": "Waar"},
        "description": {
            "en": "The claim is accurate and supported by evidence.",
            "nl": "De claim is accuraat en wordt ondersteund door bewijs.",
        },
        "visual_color": "#00AA00",
        "icon_name": "check-circle",
        "display_order": 1,
    },
    {
        "rating_key": "PARTLY_FALSE",
        "title": {"en": "Partly False", "nl": "Gedeeltelijk onwaar"},
        "description": {
            "en": "The claim contains some accurate information but also includes false or misleading elements.",
            "nl": "De claim bevat enige accurate informatie maar bevat ook onjuiste of misleidende elementen.",
        },
        "visual_color": "#FFA500",
        "icon_name": "alert-circle",
        "display_order": 2,
    },
    {
        "rating_key": "FALSE",
        "title": {"en": "False", "nl": "Onwaar"},
        "description": {
            "en": "The claim is inaccurate and not supported by evidence.",
            "nl": "De claim is onjuist en wordt niet ondersteund door bewijs.",
        },
        "visual_color": "#FF0000",
        "icon_name": "x-circle",
        "display_order": 3,
    },
    {
        "rating_key": "MISSING_CONTEXT",
        "title": {"en": "Missing Context", "nl": "Ontbrekende context"},
        "description": {
            "en": "The claim lacks important context that would give a different impression.",
            "nl": "De claim mist belangrijke context die een andere indruk zou geven.",
        },
        "visual_color": "#FFD700",
        "icon_name": "info-circle",
        "display_order": 4,
    },
    {
        "rating_key": "ALTERED",
        "title": {"en": "Altered", "nl": "Gemanipuleerd"},
        "description": {
            "en": "The content has been digitally altered or manipulated.",
            "nl": "De inhoud is digitaal gewijzigd of gemanipuleerd.",
        },
        "visual_color": "#800080",
        "icon_name": "edit-circle",
        "display_order": 5,
    },
    {
        "rating_key": "SATIRE",
        "title": {"en": "Satire", "nl": "Satire"},
        "description": {
            "en": "The content is satirical in nature and not intended to be taken as fact.",
            "nl": "De inhoud is satirisch van aard en is niet bedoeld om als feit te worden beschouwd.",
        },
        "visual_color": "#808080",
        "icon_name": "smile-circle",
        "display_order": 6,
    },
]


def upgrade() -> None:
    """Create rating_definitions table and seed EFCSN ratings."""
    # Create the rating_definitions table
    op.create_table(
        "rating_definitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("rating_key", sa.String(length=50), nullable=False),
        sa.Column("title", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("description", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("visual_color", sa.String(length=7), nullable=True),
        sa.Column("icon_name", sa.String(length=50), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rating_key", name="uq_rating_definitions_rating_key"),
    )

    # Create indexes for performance
    op.create_index(
        "idx_rating_definitions_rating_key",
        "rating_definitions",
        ["rating_key"],
        unique=True,
    )
    op.create_index(
        "idx_rating_definitions_display_order",
        "rating_definitions",
        ["display_order"],
        unique=False,
    )

    # Seed the 6 EFCSN rating definitions
    bind = op.get_bind()
    import json
    from uuid import uuid4

    for rating in EFCSN_RATINGS:
        bind.execute(
            sa.text("""
                INSERT INTO rating_definitions
                (id, rating_key, title, description, visual_color, icon_name, display_order)
                VALUES
                (:id, :rating_key, :title, :description, :visual_color, :icon_name, :display_order)
                """),
            {
                "id": str(uuid4()),
                "rating_key": rating["rating_key"],
                "title": json.dumps(rating["title"]),
                "description": json.dumps(rating["description"]),
                "visual_color": rating["visual_color"],
                "icon_name": rating["icon_name"],
                "display_order": rating["display_order"],
            },
        )


def downgrade() -> None:
    """Drop rating_definitions table."""
    op.drop_index("idx_rating_definitions_display_order", table_name="rating_definitions")
    op.drop_index("idx_rating_definitions_rating_key", table_name="rating_definitions")
    op.drop_table("rating_definitions")
