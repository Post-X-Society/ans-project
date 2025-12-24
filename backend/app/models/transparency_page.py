"""
TransparencyPage and TransparencyPageVersion models for EFCSN compliance.

These models support the transparency and methodology pages required by EFCSN:
- TransparencyPage: Main table with slug, multilingual title/content, versioning
- TransparencyPageVersion: Version history for audit trail and accountability

Issue #82: Database Schema: Transparency Pages with Versioning
EPIC #51: Transparency & Methodology Pages
ADR 0005: EFCSN Compliance Architecture
"""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.user import User

# Cross-database compatible JSONB type (JSONB for PostgreSQL, JSON for SQLite)
JSONType = JSON().with_variant(JSONB, "postgresql")


class TransparencyPage(TimeStampedModel):
    """
    Transparency page for EFCSN compliance.

    Stores multilingual content for required transparency pages:
    - /about/methodology
    - /about/organization
    - /about/team
    - /about/funding
    - /about/partnerships
    - /policies/corrections
    - /policies/privacy

    Attributes:
        slug: Unique URL-friendly identifier (e.g., "methodology")
        title: Multilingual title as JSONB {"en": "...", "nl": "..."}
        content: Multilingual markdown content as JSONB
        version: Current version number for the page
        last_reviewed: When the page was last reviewed
        next_review_due: When the annual review is due
    """

    __tablename__ = "transparency_pages"

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    title: Mapped[dict[str, Any]] = mapped_column(
        JSONType,
        nullable=False,
    )
    content: Mapped[dict[str, Any]] = mapped_column(
        JSONType,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
    )
    last_reviewed: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_review_due: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    versions: Mapped[list["TransparencyPageVersion"]] = relationship(
        "TransparencyPageVersion",
        back_populates="page",
        lazy="selectin",
        order_by="TransparencyPageVersion.version",
    )

    # Indexes for optimized queries
    __table_args__ = (Index("idx_transparency_pages_slug", "slug"),)

    def __repr__(self) -> str:
        return f"<TransparencyPage(slug={self.slug}, version={self.version})>"


class TransparencyPageVersion(TimeStampedModel):
    """
    Version history for transparency pages.

    Every change to a transparency page creates a new version record,
    providing a complete audit trail for EFCSN compliance.

    Attributes:
        page_id: FK to the transparency page this version belongs to
        version: Version number at time of change
        title: Title content at this version
        content: Page content at this version
        changed_by_id: FK to the user who made the change
        change_summary: Optional description of what changed
    """

    __tablename__ = "transparency_page_versions"

    page_id: Mapped[UUID] = mapped_column(
        ForeignKey("transparency_pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        nullable=False,
    )
    title: Mapped[dict[str, Any]] = mapped_column(
        JSONType,
        nullable=False,
    )
    content: Mapped[dict[str, Any]] = mapped_column(
        JSONType,
        nullable=False,
    )
    changed_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    change_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    page: Mapped["TransparencyPage"] = relationship(
        "TransparencyPage",
        back_populates="versions",
        lazy="selectin",
    )
    changed_by: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )

    # Indexes for optimized queries
    __table_args__ = (
        Index("idx_transparency_page_versions_page_id", "page_id"),
        Index("idx_transparency_page_versions_changed_by_id", "changed_by_id"),
    )

    def __repr__(self) -> str:
        return f"<TransparencyPageVersion(page_id={self.page_id}, version={self.version})>"


# Required transparency pages for EFCSN compliance
REQUIRED_TRANSPARENCY_PAGES: list[dict[str, Any]] = [
    {
        "slug": "methodology",
        "title": {
            "en": "Fact-Checking Methodology",
            "nl": "Factcheck-Methodologie",
        },
        "content": {
            "en": "## How We Fact-Check\n\nThis page describes our fact-checking methodology. "
            "Content will be added during implementation.\n\n"
            "### Key Points\n"
            "- Evidence-based approach\n"
            "- Minimum 2 sources per claim\n"
            "- Transparent rating system",
            "nl": "## Hoe Wij Factchecken\n\nDeze pagina beschrijft onze factcheck-methodologie. "
            "Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
            "### Kernpunten\n"
            "- Bewijsgerichte aanpak\n"
            "- Minimaal 2 bronnen per claim\n"
            "- Transparant beoordelingssysteem",
        },
    },
    {
        "slug": "organization",
        "title": {
            "en": "About Our Organization",
            "nl": "Over Onze Organisatie",
        },
        "content": {
            "en": "## About AnsCheckt\n\nAnsCheckt is a youth-focused fact-checking organization. "
            "Content will be added during implementation.\n\n"
            "### Legal Structure\n"
            "Information about our legal structure and governance.",
            "nl": "## Over AnsCheckt\n\nAnsCheckt is een op jongeren gerichte factcheck-organisatie. "
            "Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
            "### Juridische Structuur\n"
            "Informatie over onze juridische structuur en governance.",
        },
    },
    {
        "slug": "team",
        "title": {
            "en": "Our Team",
            "nl": "Ons Team",
        },
        "content": {
            "en": "## Meet Our Team\n\nLearn about the people behind AnsCheckt. "
            "Content will be added during implementation.\n\n"
            "### Key Staff\n"
            "Information about our key staff members and their backgrounds.",
            "nl": "## Maak Kennis Met Ons Team\n\nLeer de mensen achter AnsCheckt kennen. "
            "Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
            "### Belangrijke Medewerkers\n"
            "Informatie over onze belangrijke medewerkers en hun achtergronden.",
        },
    },
    {
        "slug": "funding",
        "title": {
            "en": "Funding Sources",
            "nl": "Financieringsbronnen",
        },
        "content": {
            "en": "## Our Funding\n\nTransparency about our funding sources (>1% or >5000). "
            "Content will be added during implementation.\n\n"
            "### Funding Disclosure\n"
            "All funding sources above the EFCSN threshold will be listed here.",
            "nl": "## Onze Financiering\n\nTransparantie over onze financieringsbronnen (>1% of >5000). "
            "Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
            "### Financieringsopenbaarmaking\n"
            "Alle financieringsbronnen boven de EFCSN-drempel worden hier vermeld.",
        },
    },
    {
        "slug": "partnerships",
        "title": {
            "en": "Partnerships",
            "nl": "Partnerschappen",
        },
        "content": {
            "en": "## Our Partnerships\n\nInformation about our platform and organization partnerships. "
            "Content will be added during implementation.\n\n"
            "### Partner Organizations\n"
            "Details about our collaborative partnerships.",
            "nl": "## Onze Partnerschappen\n\nInformatie over onze platform- en organisatiepartnerschappen. "
            "Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
            "### Partnerorganisaties\n"
            "Details over onze samenwerkingspartnerschappen.",
        },
    },
    {
        "slug": "corrections-policy",
        "title": {
            "en": "Corrections Policy",
            "nl": "Correctiebeleid",
        },
        "content": {
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
        },
    },
    {
        "slug": "privacy-policy",
        "title": {
            "en": "Privacy Policy",
            "nl": "Privacybeleid",
        },
        "content": {
            "en": "## Privacy Policy\n\nHow we handle your personal data in compliance with GDPR. "
            "Content will be added during implementation.\n\n"
            "### Data Protection\n"
            "- GDPR compliance\n"
            "- Minor anonymization\n"
            "- Right to be forgotten\n"
            "- 7-year audit log retention",
            "nl": "## Privacybeleid\n\nHoe wij uw persoonsgegevens verwerken in overeenstemming met AVG. "
            "Inhoud wordt toegevoegd tijdens de implementatie.\n\n"
            "### Gegevensbescherming\n"
            "- AVG-compliance\n"
            "- Anonimisering van minderjarigen\n"
            "- Recht op vergetelheid\n"
            "- 7 jaar bewaring van auditlogs",
        },
    },
]


async def seed_transparency_pages(db_session: AsyncSession) -> None:
    """
    Seed the database with the 7 required transparency pages.

    This function is idempotent - it will not create duplicate pages
    if run multiple times.

    Args:
        db_session: Async database session
    """
    from sqlalchemy import select

    for page_data in REQUIRED_TRANSPARENCY_PAGES:
        # Check if page already exists
        result = await db_session.execute(
            select(TransparencyPage).where(TransparencyPage.slug == page_data["slug"])
        )
        existing_page = result.scalar_one_or_none()

        if existing_page is None:
            # Calculate next review date (1 year from now)
            now = datetime.now(timezone.utc)
            next_review = now + timedelta(days=365)

            page = TransparencyPage(
                slug=page_data["slug"],
                title=page_data["title"],
                content=page_data["content"],
                version=1,
                last_reviewed=now,
                next_review_due=next_review,
            )
            db_session.add(page)

    await db_session.commit()
