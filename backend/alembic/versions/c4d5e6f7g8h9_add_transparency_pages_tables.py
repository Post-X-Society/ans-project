"""add transparency pages tables

Revision ID: c4d5e6f7g8h9
Revises: d5e6f7a8b9c0
Create Date: 2025-12-22 14:00:00.000000

Issue #82: Database Schema: Transparency Pages with Versioning
EPIC #51: Transparency & Methodology Pages
ADR 0005: EFCSN Compliance Architecture
"""

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7g8h9"
down_revision: Union[str, None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create transparency_pages and transparency_page_versions tables with seed data."""
    # STEP 1: Create transparency_pages table
    op.create_table(
        "transparency_pages",
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
        # Transparency page fields
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("title", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_reviewed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_due", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_transparency_pages_slug"),
    )

    # Create index for slug
    op.create_index(
        "idx_transparency_pages_slug",
        "transparency_pages",
        ["slug"],
        unique=False,
    )

    # STEP 2: Create transparency_page_versions table
    op.create_table(
        "transparency_page_versions",
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
        # Version fields
        sa.Column("page_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("changed_by_id", sa.UUID(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["transparency_pages.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for transparency_page_versions
    op.create_index(
        "idx_transparency_page_versions_page_id",
        "transparency_page_versions",
        ["page_id"],
        unique=False,
    )
    op.create_index(
        "idx_transparency_page_versions_changed_by_id",
        "transparency_page_versions",
        ["changed_by_id"],
        unique=False,
    )

    # STEP 3: Seed the 7 required transparency pages
    seed_transparency_pages()


def seed_transparency_pages() -> None:
    """Seed the database with the 7 required EFCSN transparency pages."""
    now = datetime.now(timezone.utc)
    next_review = now + timedelta(days=365)

    # Required transparency pages for EFCSN compliance
    required_pages: list[dict[str, Any]] = [
        {
            "id": str(uuid.uuid4()),
            "slug": "methodology",
            "title": json.dumps(
                {
                    "en": "Fact-Checking Methodology",
                    "nl": "Factcheck-Methodologie",
                }
            ),
            "content": json.dumps(
                {
                    "en": "## How We Fact-Check\n\nThis page describes our fact-checking "
                    "methodology. Content will be added during implementation.\n\n"
                    "### Key Points\n"
                    "- Evidence-based approach\n"
                    "- Minimum 2 sources per claim\n"
                    "- Transparent rating system",
                    "nl": "## Hoe Wij Factchecken\n\nDeze pagina beschrijft onze factcheck-"
                    "methodologie. Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
                    "### Kernpunten\n"
                    "- Bewijsgerichte aanpak\n"
                    "- Minimaal 2 bronnen per claim\n"
                    "- Transparant beoordelingssysteem",
                }
            ),
        },
        {
            "id": str(uuid.uuid4()),
            "slug": "organization",
            "title": json.dumps(
                {
                    "en": "About Our Organization",
                    "nl": "Over Onze Organisatie",
                }
            ),
            "content": json.dumps(
                {
                    "en": "## About AnsCheckt\n\nAnsCheckt is a youth-focused fact-checking "
                    "organization. Content will be added during implementation.\n\n"
                    "### Legal Structure\n"
                    "Information about our legal structure and governance.",
                    "nl": "## Over AnsCheckt\n\nAnsCheckt is een op jongeren gerichte factcheck-"
                    "organisatie. Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
                    "### Juridische Structuur\n"
                    "Informatie over onze juridische structuur en governance.",
                }
            ),
        },
        {
            "id": str(uuid.uuid4()),
            "slug": "team",
            "title": json.dumps(
                {
                    "en": "Our Team",
                    "nl": "Ons Team",
                }
            ),
            "content": json.dumps(
                {
                    "en": "## Meet Our Team\n\nLearn about the people behind AnsCheckt. "
                    "Content will be added during implementation.\n\n"
                    "### Key Staff\n"
                    "Information about our key staff members and their backgrounds.",
                    "nl": "## Maak Kennis Met Ons Team\n\nLeer de mensen achter AnsCheckt kennen. "
                    "Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
                    "### Belangrijke Medewerkers\n"
                    "Informatie over onze belangrijke medewerkers en hun achtergronden.",
                }
            ),
        },
        {
            "id": str(uuid.uuid4()),
            "slug": "funding",
            "title": json.dumps(
                {
                    "en": "Funding Sources",
                    "nl": "Financieringsbronnen",
                }
            ),
            "content": json.dumps(
                {
                    "en": "## Our Funding\n\nTransparency about our funding sources (>1% or >5000). "
                    "Content will be added during implementation.\n\n"
                    "### Funding Disclosure\n"
                    "All funding sources above the EFCSN threshold will be listed here.",
                    "nl": "## Onze Financiering\n\nTransparantie over onze financieringsbronnen "
                    "(>1% of >5000). Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
                    "### Financieringsopenbaarmaking\n"
                    "Alle financieringsbronnen boven de EFCSN-drempel worden hier vermeld.",
                }
            ),
        },
        {
            "id": str(uuid.uuid4()),
            "slug": "partnerships",
            "title": json.dumps(
                {
                    "en": "Partnerships",
                    "nl": "Partnerschappen",
                }
            ),
            "content": json.dumps(
                {
                    "en": "## Our Partnerships\n\nInformation about our platform and organization "
                    "partnerships. Content will be added during implementation.\n\n"
                    "### Partner Organizations\n"
                    "Details about our collaborative partnerships.",
                    "nl": "## Onze Partnerschappen\n\nInformatie over onze platform- en "
                    "organisatiepartnerschappen. Inhoud wordt toegevoegd tijdens de "
                    "implementatie.\n\n"
                    "### Partnerorganisaties\n"
                    "Details over onze samenwerkingspartnerschappen.",
                }
            ),
        },
        {
            "id": str(uuid.uuid4()),
            "slug": "corrections-policy",
            "title": json.dumps(
                {
                    "en": "Corrections Policy",
                    "nl": "Correctiebeleid",
                }
            ),
            "content": json.dumps(
                {
                    "en": "## Corrections Policy\n\nHow to request corrections to our fact-checks. "
                    "Content will be added during implementation.\n\n"
                    "### Types of Corrections\n"
                    "- Minor corrections (typos, formatting)\n"
                    "- Update corrections (new information)\n"
                    "- Substantial corrections (rating changes)\n\n"
                    "### EFCSN Escalation\n"
                    "Unresolved complaints can be escalated to EFCSN.",
                    "nl": "## Correctiebeleid\n\nHoe u correcties aan onze factchecks kunt aanvragen. "
                    "Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
                    "### Soorten Correcties\n"
                    "- Kleine correcties (tikfouten, opmaak)\n"
                    "- Update correcties (nieuwe informatie)\n"
                    "- Substantiele correcties (beoordelingswijzigingen)\n\n"
                    "### EFCSN Escalatie\n"
                    "Onopgeloste klachten kunnen worden geescaleerd naar EFCSN.",
                }
            ),
        },
        {
            "id": str(uuid.uuid4()),
            "slug": "privacy-policy",
            "title": json.dumps(
                {
                    "en": "Privacy Policy",
                    "nl": "Privacybeleid",
                }
            ),
            "content": json.dumps(
                {
                    "en": "## Privacy Policy\n\nHow we handle your personal data in compliance with "
                    "GDPR. Content will be added during implementation.\n\n"
                    "### Data Protection\n"
                    "- GDPR compliance\n"
                    "- Minor anonymization\n"
                    "- Right to be forgotten\n"
                    "- 7-year audit log retention",
                    "nl": "## Privacybeleid\n\nHoe wij uw persoonsgegevens verwerken in "
                    "overeenstemming met AVG. Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
                    "### Gegevensbescherming\n"
                    "- AVG-compliance\n"
                    "- Anonimisering van minderjarigen\n"
                    "- Recht op vergetelheid\n"
                    "- 7 jaar bewaring van auditlogs",
                }
            ),
        },
    ]

    connection = op.get_bind()

    for page in required_pages:
        # Check if page already exists (by slug)
        result = connection.execute(
            text("SELECT COUNT(*) FROM transparency_pages WHERE slug = :slug"),
            {"slug": page["slug"]},
        )
        count = result.scalar()

        if count == 0:
            connection.execute(
                text("""
                    INSERT INTO transparency_pages
                    (id, slug, title, content, version, last_reviewed, next_review_due,
                     created_at, updated_at)
                    VALUES
                    (CAST(:id AS uuid), :slug, CAST(:title AS jsonb), CAST(:content AS jsonb), 1, :last_reviewed,
                     :next_review_due, now(), now())
                    """),
                {
                    "id": page["id"],
                    "slug": page["slug"],
                    "title": page["title"],
                    "content": page["content"],
                    "last_reviewed": now,
                    "next_review_due": next_review,
                },
            )


def downgrade() -> None:
    """Drop transparency_pages and transparency_page_versions tables."""
    # Drop indexes and tables in reverse order
    op.drop_index(
        "idx_transparency_page_versions_changed_by_id",
        table_name="transparency_page_versions",
    )
    op.drop_index(
        "idx_transparency_page_versions_page_id",
        table_name="transparency_page_versions",
    )
    op.drop_table("transparency_page_versions")

    op.drop_index("idx_transparency_pages_slug", table_name="transparency_pages")
    op.drop_table("transparency_pages")
