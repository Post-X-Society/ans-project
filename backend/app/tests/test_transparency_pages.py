"""
Tests for TransparencyPage and TransparencyPageVersion models - TDD approach: Tests FIRST

This test module covers:
- TransparencyPage table creation and fields
- TransparencyPageVersion table creation and fields for version history
- JSONB multilingual content storage (title, content)
- Foreign key relationships and cascade behavior
- Unique constraint on slug
- Index optimization for slug and page_id queries
- Seed data for 7 required transparency pages

Issue #82: Database Schema: Transparency Pages with Versioning
EPIC #51: Transparency & Methodology Pages
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class TestTransparencyPageModel:
    """Tests for TransparencyPage model"""

    @pytest.mark.asyncio
    async def test_create_transparency_page(self, db_session: AsyncSession) -> None:
        """Test creating a transparency page with all required fields"""
        from app.models.transparency_page import TransparencyPage

        title: dict[str, str] = {"en": "Methodology", "nl": "Methodologie"}
        content: dict[str, str] = {
            "en": "Our fact-checking methodology...",
            "nl": "Onze factcheck-methodologie...",
        }

        page = TransparencyPage(
            slug="methodology",
            title=title,
            content=content,
            version=1,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        assert page.id is not None
        assert isinstance(page.id, UUID)
        assert page.slug == "methodology"
        assert page.title == title
        assert page.content == content
        assert page.version == 1
        assert isinstance(page.created_at, datetime)
        assert isinstance(page.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_transparency_page_slug_unique(self, db_session: AsyncSession) -> None:
        """Test that slug field has unique constraint"""
        from app.models.transparency_page import TransparencyPage

        page1 = TransparencyPage(
            slug="methodology",
            title={"en": "Methodology"},
            content={"en": "Content 1"},
            version=1,
        )
        db_session.add(page1)
        await db_session.commit()

        # Attempt to create another page with same slug
        page2 = TransparencyPage(
            slug="methodology",  # Duplicate slug
            title={"en": "Different Title"},
            content={"en": "Content 2"},
            version=1,
        )
        db_session.add(page2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_transparency_page_multilingual_content(self, db_session: AsyncSession) -> None:
        """Test JSONB storage for multilingual title and content"""
        from app.models.transparency_page import TransparencyPage

        title: dict[str, str] = {
            "en": "About Our Organization",
            "nl": "Over Onze Organisatie",
        }
        content: dict[str, str] = {
            "en": "AnsCheckt is a youth-focused fact-checking organization...",
            "nl": "AnsCheckt is een op jongeren gerichte factcheck-organisatie...",
        }

        page = TransparencyPage(
            slug="organization",
            title=title,
            content=content,
            version=1,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Verify multilingual access
        assert page.title["en"] == "About Our Organization"
        assert page.title["nl"] == "Over Onze Organisatie"
        assert "youth-focused" in page.content["en"]
        assert "jongeren gerichte" in page.content["nl"]

    @pytest.mark.asyncio
    async def test_transparency_page_review_dates(self, db_session: AsyncSession) -> None:
        """Test last_reviewed and next_review_due optional date fields"""
        from app.models.transparency_page import TransparencyPage

        now = datetime.now(timezone.utc)
        next_year = now + timedelta(days=365)

        page = TransparencyPage(
            slug="funding",
            title={"en": "Funding Sources"},
            content={"en": "Our funding comes from..."},
            version=1,
            last_reviewed=now,
            next_review_due=next_year,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        assert page.last_reviewed is not None
        assert page.next_review_due is not None
        # Compare timestamps (ignoring microseconds due to DB precision)
        assert page.last_reviewed.date() == now.date()
        assert page.next_review_due.date() == next_year.date()

    @pytest.mark.asyncio
    async def test_transparency_page_review_dates_nullable(self, db_session: AsyncSession) -> None:
        """Test that review dates can be null"""
        from app.models.transparency_page import TransparencyPage

        page = TransparencyPage(
            slug="team",
            title={"en": "Our Team"},
            content={"en": "Meet our team..."},
            version=1,
            # Not setting last_reviewed or next_review_due
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        assert page.last_reviewed is None
        assert page.next_review_due is None

    @pytest.mark.asyncio
    async def test_transparency_page_versions_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between transparency page and its versions"""
        from app.models.transparency_page import TransparencyPage, TransparencyPageVersion

        # Create user for changed_by field
        user = User(
            email="editor@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create page
        page = TransparencyPage(
            slug="partnerships",
            title={"en": "Partnerships"},
            content={"en": "Our partners include..."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Create version
        version = TransparencyPageVersion(
            page_id=page.id,
            version=1,
            title=page.title,
            content=page.content,
            changed_by_id=user.id,
            change_summary="Initial version",
        )
        db_session.add(version)
        await db_session.commit()

        # Verify relationship
        result = await db_session.execute(
            select(TransparencyPage).where(TransparencyPage.id == page.id)
        )
        loaded_page = result.scalar_one()
        assert hasattr(loaded_page, "versions")

    @pytest.mark.asyncio
    async def test_query_transparency_page_by_slug(self, db_session: AsyncSession) -> None:
        """Test querying transparency page by slug (index optimization)"""
        from app.models.transparency_page import TransparencyPage

        # Create multiple pages
        pages_data = [
            ("methodology", {"en": "Methodology"}),
            ("organization", {"en": "Organization"}),
            ("corrections", {"en": "Corrections Policy"}),
        ]

        for slug, title in pages_data:
            page = TransparencyPage(
                slug=slug,
                title=title,
                content={"en": f"Content for {slug}"},
                version=1,
            )
            db_session.add(page)

        await db_session.commit()

        # Query by slug
        result = await db_session.execute(
            select(TransparencyPage).where(TransparencyPage.slug == "corrections")
        )
        page = result.scalar_one()

        assert page.slug == "corrections"
        assert page.title["en"] == "Corrections Policy"


class TestTransparencyPageVersionModel:
    """Tests for TransparencyPageVersion model"""

    @pytest.mark.asyncio
    async def test_create_transparency_page_version(self, db_session: AsyncSession) -> None:
        """Test creating a transparency page version"""
        from app.models.transparency_page import TransparencyPage, TransparencyPageVersion

        # Create user
        user = User(
            email="editor@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create page
        page = TransparencyPage(
            slug="privacy",
            title={"en": "Privacy Policy"},
            content={"en": "Your privacy matters..."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Create version
        version = TransparencyPageVersion(
            page_id=page.id,
            version=1,
            title={"en": "Privacy Policy"},
            content={"en": "Your privacy matters..."},
            changed_by_id=user.id,
            change_summary="Initial version",
        )
        db_session.add(version)
        await db_session.commit()
        await db_session.refresh(version)

        assert version.id is not None
        assert isinstance(version.id, UUID)
        assert version.page_id == page.id
        assert version.version == 1
        assert version.title["en"] == "Privacy Policy"
        assert version.content["en"] == "Your privacy matters..."
        assert version.changed_by_id == user.id
        assert version.change_summary == "Initial version"
        assert isinstance(version.created_at, datetime)

    @pytest.mark.asyncio
    async def test_multiple_versions_for_page(self, db_session: AsyncSession) -> None:
        """Test that a page can have multiple versions (version history)"""
        from app.models.transparency_page import TransparencyPage, TransparencyPageVersion

        # Create user
        user = User(
            email="editor@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create page
        page = TransparencyPage(
            slug="methodology",
            title={"en": "Methodology v3"},
            content={"en": "Updated methodology content"},
            version=3,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Create version history
        versions_data = [
            (1, "Initial methodology", "Initial version"),
            (2, "Improved methodology", "Added source requirements"),
            (3, "Updated methodology content", "Updated for EFCSN compliance"),
        ]

        for ver_num, content, summary in versions_data:
            version = TransparencyPageVersion(
                page_id=page.id,
                version=ver_num,
                title={"en": f"Methodology v{ver_num}"},
                content={"en": content},
                changed_by_id=user.id,
                change_summary=summary,
            )
            db_session.add(version)

        await db_session.commit()

        # Query all versions for this page
        result = await db_session.execute(
            select(TransparencyPageVersion)
            .where(TransparencyPageVersion.page_id == page.id)
            .order_by(TransparencyPageVersion.version)
        )
        all_versions = result.scalars().all()

        assert len(all_versions) == 3
        assert all_versions[0].version == 1
        assert all_versions[-1].version == 3
        assert "EFCSN compliance" in all_versions[-1].change_summary

    @pytest.mark.asyncio
    async def test_version_change_summary_nullable(self, db_session: AsyncSession) -> None:
        """Test that change_summary can be null"""
        from app.models.transparency_page import TransparencyPage, TransparencyPageVersion

        # Create user
        user = User(
            email="editor@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create page
        page = TransparencyPage(
            slug="team",
            title={"en": "Team"},
            content={"en": "Our team..."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Create version without change_summary
        version = TransparencyPageVersion(
            page_id=page.id,
            version=1,
            title={"en": "Team"},
            content={"en": "Our team..."},
            changed_by_id=user.id,
            # change_summary not set
        )
        db_session.add(version)
        await db_session.commit()
        await db_session.refresh(version)

        assert version.change_summary is None

    @pytest.mark.asyncio
    async def test_version_user_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between version and user (changed_by)"""
        from app.models.transparency_page import TransparencyPage, TransparencyPageVersion

        # Create user
        user = User(
            email="editor@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create page
        page = TransparencyPage(
            slug="funding",
            title={"en": "Funding"},
            content={"en": "Our funding..."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Create version
        version = TransparencyPageVersion(
            page_id=page.id,
            version=1,
            title={"en": "Funding"},
            content={"en": "Our funding..."},
            changed_by_id=user.id,
            change_summary="Initial",
        )
        db_session.add(version)
        await db_session.commit()

        # Query version and verify changed_by relationship
        result = await db_session.execute(
            select(TransparencyPageVersion).where(TransparencyPageVersion.changed_by_id == user.id)
        )
        loaded_version = result.scalar_one()
        assert loaded_version.changed_by_id == user.id

    @pytest.mark.asyncio
    async def test_version_page_relationship(self, db_session: AsyncSession) -> None:
        """Test relationship between version and page"""
        from app.models.transparency_page import TransparencyPage, TransparencyPageVersion

        # Create user
        user = User(
            email="editor@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create page
        page = TransparencyPage(
            slug="corrections",
            title={"en": "Corrections"},
            content={"en": "Our corrections policy..."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Create version
        version = TransparencyPageVersion(
            page_id=page.id,
            version=1,
            title={"en": "Corrections"},
            content={"en": "Our corrections policy..."},
            changed_by_id=user.id,
        )
        db_session.add(version)
        await db_session.commit()
        await db_session.refresh(version)

        # Verify page relationship
        assert version.page_id == page.id
        assert hasattr(version, "page")


class TestRequiredTransparencyPages:
    """Tests for the 7 required transparency pages (EFCSN compliance)"""

    REQUIRED_SLUGS = [
        "methodology",
        "organization",
        "team",
        "funding",
        "partnerships",
        "corrections",
        "privacy",
    ]

    @pytest.mark.asyncio
    async def test_seed_creates_all_required_pages(self, db_session: AsyncSession) -> None:
        """Test that seed function creates all 7 required pages"""
        from app.models.transparency_page import (
            TransparencyPage,
            seed_transparency_pages,
        )

        # Run seed function
        await seed_transparency_pages(db_session)

        # Query all pages
        result = await db_session.execute(select(TransparencyPage))
        pages = result.scalars().all()

        assert len(pages) == 7

        # Verify all required slugs exist
        slugs = {page.slug for page in pages}
        for required_slug in self.REQUIRED_SLUGS:
            assert required_slug in slugs, f"Missing required page: {required_slug}"

    @pytest.mark.asyncio
    async def test_seed_pages_have_multilingual_content(self, db_session: AsyncSession) -> None:
        """Test that seeded pages have both EN and NL content"""
        from app.models.transparency_page import (
            TransparencyPage,
            seed_transparency_pages,
        )

        # Run seed function
        await seed_transparency_pages(db_session)

        # Query all pages
        result = await db_session.execute(select(TransparencyPage))
        pages = result.scalars().all()

        for page in pages:
            # Verify title has both languages
            assert "en" in page.title, f"Page {page.slug} missing EN title"
            assert "nl" in page.title, f"Page {page.slug} missing NL title"
            # Verify content has both languages
            assert "en" in page.content, f"Page {page.slug} missing EN content"
            assert "nl" in page.content, f"Page {page.slug} missing NL content"

    @pytest.mark.asyncio
    async def test_seed_is_idempotent(self, db_session: AsyncSession) -> None:
        """Test that running seed multiple times doesn't duplicate pages"""
        from app.models.transparency_page import (
            TransparencyPage,
            seed_transparency_pages,
        )

        # Run seed function twice
        await seed_transparency_pages(db_session)
        await seed_transparency_pages(db_session)

        # Query all pages
        result = await db_session.execute(select(TransparencyPage))
        pages = result.scalars().all()

        # Should still only have 7 pages
        assert len(pages) == 7

    @pytest.mark.asyncio
    async def test_seed_pages_start_at_version_1(self, db_session: AsyncSession) -> None:
        """Test that seeded pages start at version 1"""
        from app.models.transparency_page import (
            TransparencyPage,
            seed_transparency_pages,
        )

        # Run seed function
        await seed_transparency_pages(db_session)

        # Query all pages
        result = await db_session.execute(select(TransparencyPage))
        pages = result.scalars().all()

        for page in pages:
            assert page.version == 1, f"Page {page.slug} should start at version 1"

    @pytest.mark.asyncio
    async def test_seed_pages_set_next_review_date(self, db_session: AsyncSession) -> None:
        """Test that seeded pages have next_review_due set (annual review)"""
        from app.models.transparency_page import (
            TransparencyPage,
            seed_transparency_pages,
        )

        # Run seed function
        await seed_transparency_pages(db_session)

        # Query all pages
        result = await db_session.execute(select(TransparencyPage))
        pages = result.scalars().all()

        for page in pages:
            assert (
                page.next_review_due is not None
            ), f"Page {page.slug} should have next_review_due set"
