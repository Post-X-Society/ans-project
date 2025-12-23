"""
Tests for TransparencyPageService.

Following TDD approach: tests written FIRST, then implementation.
Issue #83: Backend: Transparency Page Service with Versioning

Test Coverage Requirements:
- get_page_by_slug() - retrieve page by slug with language support
- get_page_version() - retrieve specific version of a page
- update_page() - update page with automatic versioning
- get_version_history() - list all versions of a page
- generate_diff() - diff between two versions
- get_pages_due_for_review() - find pages needing annual review
- send_review_reminders() - send email reminders for pages due for review
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transparency_page import TransparencyPage, TransparencyPageVersion
from app.models.user import User, UserRole


class TestTransparencyPageServiceGetPage:
    """Tests for get_page_by_slug functionality."""

    @pytest.mark.asyncio
    async def test_get_page_by_slug_returns_page(self, db_session: AsyncSession) -> None:
        """Test retrieving a transparency page by its slug."""
        from app.services import transparency_page_service

        # Arrange: Create a page
        page = TransparencyPage(
            slug="methodology",
            title={"en": "Methodology", "nl": "Methodologie"},
            content={"en": "Our fact-checking methodology.", "nl": "Onze factcheck-methodologie."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Act: Get the page
        result = await transparency_page_service.get_page_by_slug(db_session, "methodology")

        # Assert
        assert result is not None
        assert result.slug == "methodology"
        assert result.title["en"] == "Methodology"
        assert result.version == 1

    @pytest.mark.asyncio
    async def test_get_page_by_slug_not_found(self, db_session: AsyncSession) -> None:
        """Test retrieving a non-existent page returns None."""
        from app.services import transparency_page_service

        # Act
        result = await transparency_page_service.get_page_by_slug(db_session, "nonexistent")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_page_with_language_filter(self, db_session: AsyncSession) -> None:
        """Test retrieving page content for a specific language."""
        from app.services import transparency_page_service

        # Arrange
        page = TransparencyPage(
            slug="team",
            title={"en": "Our Team", "nl": "Ons Team"},
            content={"en": "Meet our team.", "nl": "Maak kennis met ons team."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        # Act: Get English content
        result = await transparency_page_service.get_page_by_slug(db_session, "team", language="en")

        # Assert
        assert result is not None
        assert result.slug == "team"
        # Page should have full multilingual content (language filter is for response formatting)


class TestTransparencyPageServiceGetVersion:
    """Tests for get_page_version functionality."""

    @pytest.mark.asyncio
    async def test_get_specific_version(self, db_session: AsyncSession) -> None:
        """Test retrieving a specific version of a page."""
        from app.services import transparency_page_service

        # Arrange: Create user first
        user = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create page
        page = TransparencyPage(
            slug="funding",
            title={"en": "Funding", "nl": "Financiering"},
            content={"en": "Version 1 content.", "nl": "Versie 1 inhoud."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Create version history
        version1 = TransparencyPageVersion(
            page_id=page.id,
            version=1,
            title={"en": "Funding", "nl": "Financiering"},
            content={"en": "Version 1 content.", "nl": "Versie 1 inhoud."},
            changed_by_id=user.id,
            change_summary="Initial version",
        )
        db_session.add(version1)
        await db_session.commit()

        # Act
        result = await transparency_page_service.get_page_version(db_session, "funding", 1)

        # Assert
        assert result is not None
        assert result.version == 1
        assert result.content["en"] == "Version 1 content."

    @pytest.mark.asyncio
    async def test_get_nonexistent_version(self, db_session: AsyncSession) -> None:
        """Test retrieving a version that doesn't exist returns None."""
        from app.services import transparency_page_service

        # Arrange: Create page without version history
        page = TransparencyPage(
            slug="privacy",
            title={"en": "Privacy", "nl": "Privacy"},
            content={"en": "Privacy policy.", "nl": "Privacybeleid."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        # Act: Try to get version 99
        result = await transparency_page_service.get_page_version(db_session, "privacy", 99)

        # Assert
        assert result is None


class TestTransparencyPageServiceUpdatePage:
    """Tests for update_page functionality with automatic versioning."""

    @pytest.mark.asyncio
    async def test_update_page_creates_new_version(self, db_session: AsyncSession) -> None:
        """Test that updating a page increments the version and creates version record."""
        from app.services import transparency_page_service

        # Arrange: Create user
        user = User(
            email="editor@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create page
        page = TransparencyPage(
            slug="organization",
            title={"en": "Organization", "nl": "Organisatie"},
            content={"en": "Original content.", "nl": "Originele inhoud."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Act: Update the page
        updated_page = await transparency_page_service.update_page(
            db=db_session,
            slug="organization",
            title={"en": "Organization Updated", "nl": "Organisatie Bijgewerkt"},
            content={"en": "Updated content.", "nl": "Bijgewerkte inhoud."},
            changed_by_id=user.id,
            change_summary="Updated organization info",
        )

        # Assert: Page should have new version
        assert updated_page is not None
        assert updated_page.version == 2
        assert updated_page.title["en"] == "Organization Updated"
        assert updated_page.content["en"] == "Updated content."

        # Assert: Version history should be created
        versions = await transparency_page_service.get_version_history(db_session, "organization")
        assert len(versions) == 1  # Only the previous version is stored
        assert versions[0].version == 1
        assert versions[0].content["en"] == "Original content."

    @pytest.mark.asyncio
    async def test_update_page_updates_review_dates(self, db_session: AsyncSession) -> None:
        """Test that updating a page sets last_reviewed and next_review_due."""
        from app.services import transparency_page_service

        # Arrange
        user = User(
            email="reviewer@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        old_date = datetime.now(timezone.utc) - timedelta(days=400)
        page = TransparencyPage(
            slug="corrections",
            title={"en": "Corrections", "nl": "Correcties"},
            content={"en": "Corrections policy.", "nl": "Correctiebeleid."},
            version=1,
            last_reviewed=old_date,
            next_review_due=old_date + timedelta(days=365),
        )
        db_session.add(page)
        await db_session.commit()

        # Act
        updated_page = await transparency_page_service.update_page(
            db=db_session,
            slug="corrections",
            title={"en": "Corrections Updated", "nl": "Correcties Bijgewerkt"},
            content={"en": "New corrections policy.", "nl": "Nieuw correctiebeleid."},
            changed_by_id=user.id,
            change_summary="Annual review",
        )

        # Assert: Review dates should be updated
        assert updated_page is not None
        assert updated_page.last_reviewed is not None
        # Make sure we compare timezone-aware datetimes
        now = datetime.now(timezone.utc)
        last_reviewed = updated_page.last_reviewed
        if last_reviewed.tzinfo is None:
            last_reviewed = last_reviewed.replace(tzinfo=timezone.utc)
        assert (now - last_reviewed).total_seconds() < 60  # Within last minute
        assert updated_page.next_review_due is not None
        # Next review should be ~1 year from now
        next_review = updated_page.next_review_due
        if next_review.tzinfo is None:
            next_review = next_review.replace(tzinfo=timezone.utc)
        expected_next_review = now + timedelta(days=365)
        delta = abs((next_review - expected_next_review).total_seconds())
        assert delta < 120  # Within 2 minutes tolerance

    @pytest.mark.asyncio
    async def test_update_nonexistent_page_returns_none(self, db_session: AsyncSession) -> None:
        """Test updating a non-existent page returns None."""
        from app.services import transparency_page_service

        # Arrange: Create user but no page
        user = User(
            email="admin@test.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Act
        result = await transparency_page_service.update_page(
            db=db_session,
            slug="nonexistent",
            title={"en": "New Title"},
            content={"en": "New content."},
            changed_by_id=user.id,
            change_summary="Attempt to update",
        )

        # Assert
        assert result is None


class TestTransparencyPageServiceVersionHistory:
    """Tests for get_version_history functionality."""

    @pytest.mark.asyncio
    async def test_get_version_history_returns_all_versions(self, db_session: AsyncSession) -> None:
        """Test retrieving complete version history of a page."""
        from app.services import transparency_page_service

        # Arrange: Create user
        user = User(
            email="historian@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create page
        page = TransparencyPage(
            slug="partnerships",
            title={"en": "Partnerships", "nl": "Partnerschappen"},
            content={"en": "Version 3 content.", "nl": "Versie 3 inhoud."},
            version=3,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Create version history entries
        for v in range(1, 3):
            version = TransparencyPageVersion(
                page_id=page.id,
                version=v,
                title={"en": f"Title v{v}", "nl": f"Titel v{v}"},
                content={"en": f"Version {v} content.", "nl": f"Versie {v} inhoud."},
                changed_by_id=user.id,
                change_summary=f"Version {v}",
            )
            db_session.add(version)
        await db_session.commit()

        # Act
        history = await transparency_page_service.get_version_history(db_session, "partnerships")

        # Assert
        assert len(history) == 2
        assert history[0].version == 1  # Ordered by version
        assert history[1].version == 2

    @pytest.mark.asyncio
    async def test_get_version_history_empty_for_new_page(self, db_session: AsyncSession) -> None:
        """Test version history is empty for a newly created page."""
        from app.services import transparency_page_service

        # Arrange
        page = TransparencyPage(
            slug="new-page",
            title={"en": "New Page", "nl": "Nieuwe Pagina"},
            content={"en": "New content.", "nl": "Nieuwe inhoud."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        # Act
        history = await transparency_page_service.get_version_history(db_session, "new-page")

        # Assert
        assert len(history) == 0


class TestTransparencyPageServiceDiff:
    """Tests for generate_diff functionality."""

    @pytest.mark.asyncio
    async def test_generate_diff_between_versions(self, db_session: AsyncSession) -> None:
        """Test generating diff between two versions of a page."""
        from app.services import transparency_page_service

        # Arrange: Create user
        user = User(
            email="differ@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create page with current version
        page = TransparencyPage(
            slug="diff-test",
            title={"en": "Diff Test", "nl": "Diff Test"},
            content={"en": "This is the updated content.", "nl": "Dit is de bijgewerkte inhoud."},
            version=2,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Create version 1
        version1 = TransparencyPageVersion(
            page_id=page.id,
            version=1,
            title={"en": "Diff Test", "nl": "Diff Test"},
            content={"en": "This is the original content.", "nl": "Dit is de originele inhoud."},
            changed_by_id=user.id,
            change_summary="Initial version",
        )
        db_session.add(version1)
        await db_session.commit()

        # Act: Generate diff between version 1 and current (version 2)
        diff = await transparency_page_service.generate_diff(
            db_session, "diff-test", from_version=1, to_version=2
        )

        # Assert
        assert diff is not None
        assert "diff" in diff
        assert "from_version" in diff
        assert "to_version" in diff
        assert diff["from_version"] == 1
        assert diff["to_version"] == 2
        # The diff should contain information about changes
        assert len(diff["diff"]) > 0

    @pytest.mark.asyncio
    async def test_generate_diff_invalid_version(self, db_session: AsyncSession) -> None:
        """Test generating diff with invalid version returns None."""
        from app.services import transparency_page_service

        # Arrange
        page = TransparencyPage(
            slug="invalid-diff",
            title={"en": "Test", "nl": "Test"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        # Act: Try to diff with non-existent version
        diff = await transparency_page_service.generate_diff(
            db_session, "invalid-diff", from_version=1, to_version=99
        )

        # Assert
        assert diff is None

    @pytest.mark.asyncio
    async def test_generate_diff_with_language(self, db_session: AsyncSession) -> None:
        """Test generating diff for specific language."""
        from app.services import transparency_page_service

        # Arrange
        user = User(
            email="lang-differ@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        page = TransparencyPage(
            slug="lang-diff",
            title={"en": "Language Diff", "nl": "Taal Diff"},
            content={"en": "New English content.", "nl": "Nieuwe Nederlandse inhoud."},
            version=2,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        version1 = TransparencyPageVersion(
            page_id=page.id,
            version=1,
            title={"en": "Language Diff", "nl": "Taal Diff"},
            content={"en": "Old English content.", "nl": "Oude Nederlandse inhoud."},
            changed_by_id=user.id,
            change_summary="Initial",
        )
        db_session.add(version1)
        await db_session.commit()

        # Act: Get English-specific diff
        diff = await transparency_page_service.generate_diff(
            db_session, "lang-diff", from_version=1, to_version=2, language="en"
        )

        # Assert
        assert diff is not None
        # Should contain diff info for English content
        assert "diff" in diff


class TestTransparencyPageServiceAnnualReview:
    """Tests for annual review reminder functionality."""

    @pytest.mark.asyncio
    async def test_get_pages_due_for_review(self, db_session: AsyncSession) -> None:
        """Test finding pages that are due for annual review."""
        from app.services import transparency_page_service

        # Arrange: Create pages with different review dates
        now = datetime.now(timezone.utc)

        # Page overdue for review (last reviewed 400 days ago)
        overdue_page = TransparencyPage(
            slug="overdue-page",
            title={"en": "Overdue", "nl": "Achterstallig"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
            last_reviewed=now - timedelta(days=400),
            next_review_due=now - timedelta(days=35),  # 35 days overdue
        )
        db_session.add(overdue_page)

        # Page due soon (next review in 10 days)
        soon_page = TransparencyPage(
            slug="soon-page",
            title={"en": "Due Soon", "nl": "Binnenkort"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
            last_reviewed=now - timedelta(days=355),
            next_review_due=now + timedelta(days=10),
        )
        db_session.add(soon_page)

        # Page not due (next review in 6 months)
        future_page = TransparencyPage(
            slug="future-page",
            title={"en": "Future", "nl": "Toekomst"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
            last_reviewed=now - timedelta(days=180),
            next_review_due=now + timedelta(days=185),
        )
        db_session.add(future_page)

        await db_session.commit()

        # Act: Get pages due within 30 days
        due_pages = await transparency_page_service.get_pages_due_for_review(
            db_session, days_ahead=30
        )

        # Assert
        assert len(due_pages) == 2
        slugs = [p.slug for p in due_pages]
        assert "overdue-page" in slugs  # Already overdue
        assert "soon-page" in slugs  # Due in 10 days
        assert "future-page" not in slugs  # Not due yet

    @pytest.mark.asyncio
    async def test_get_pages_due_for_review_none_due(self, db_session: AsyncSession) -> None:
        """Test when no pages are due for review."""
        from app.services import transparency_page_service

        # Arrange: Create a page with review far in the future
        now = datetime.now(timezone.utc)
        page = TransparencyPage(
            slug="not-due",
            title={"en": "Not Due", "nl": "Niet Gepland"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
            last_reviewed=now,
            next_review_due=now + timedelta(days=365),
        )
        db_session.add(page)
        await db_session.commit()

        # Act
        due_pages = await transparency_page_service.get_pages_due_for_review(
            db_session, days_ahead=30
        )

        # Assert
        assert len(due_pages) == 0


class TestTransparencyPageServiceListAll:
    """Tests for list_all_pages functionality."""

    @pytest.mark.asyncio
    async def test_list_all_pages(self, db_session: AsyncSession) -> None:
        """Test listing all transparency pages."""
        from app.services import transparency_page_service

        # Arrange: Create multiple pages
        pages_data = [
            ("methodology", "Methodology", "Methodologie"),
            ("team", "Team", "Team"),
            ("funding", "Funding", "Financiering"),
        ]
        for slug, en_title, nl_title in pages_data:
            page = TransparencyPage(
                slug=slug,
                title={"en": en_title, "nl": nl_title},
                content={"en": f"{en_title} content.", "nl": f"{nl_title} inhoud."},
                version=1,
            )
            db_session.add(page)
        await db_session.commit()

        # Act
        all_pages = await transparency_page_service.list_all_pages(db_session)

        # Assert
        assert len(all_pages) == 3


class TestTransparencyPageServiceCreate:
    """Tests for create_page functionality."""

    @pytest.mark.asyncio
    async def test_create_page(self, db_session: AsyncSession) -> None:
        """Test creating a new transparency page."""
        from app.services import transparency_page_service

        # Arrange
        user = User(
            email="creator@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Act
        page = await transparency_page_service.create_page(
            db=db_session,
            slug="new-policy",
            title={"en": "New Policy", "nl": "Nieuw Beleid"},
            content={"en": "Policy content.", "nl": "Beleidsinhoud."},
            created_by_id=user.id,
        )

        # Assert
        assert page is not None
        assert page.slug == "new-policy"
        assert page.version == 1
        assert page.title["en"] == "New Policy"
        assert page.last_reviewed is not None
        assert page.next_review_due is not None

    @pytest.mark.asyncio
    async def test_create_page_duplicate_slug_fails(self, db_session: AsyncSession) -> None:
        """Test creating a page with duplicate slug raises error."""
        from sqlalchemy.exc import IntegrityError

        from app.services import transparency_page_service

        # Arrange
        user = User(
            email="duptest@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create first page
        await transparency_page_service.create_page(
            db=db_session,
            slug="unique-slug",
            title={"en": "Title", "nl": "Titel"},
            content={"en": "Content.", "nl": "Inhoud."},
            created_by_id=user.id,
        )

        # Act & Assert: Try to create with same slug
        with pytest.raises(IntegrityError):
            await transparency_page_service.create_page(
                db=db_session,
                slug="unique-slug",  # Duplicate!
                title={"en": "Another Title", "nl": "Andere Titel"},
                content={"en": "Other content.", "nl": "Andere inhoud."},
                created_by_id=user.id,
            )


class TestTransparencyPageServiceReviewReminders:
    """Tests for annual review reminder email functionality."""

    @pytest.mark.asyncio
    async def test_send_review_reminders_no_pages_due(self, db_session: AsyncSession) -> None:
        """Test when no pages are due, no email is sent."""
        from app.services import transparency_page_service

        # Arrange: Create page with review far in future
        now = datetime.now(timezone.utc)
        page = TransparencyPage(
            slug="not-due-reminder",
            title={"en": "Not Due", "nl": "Niet Gepland"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
            last_reviewed=now,
            next_review_due=now + timedelta(days=365),
        )
        db_session.add(page)
        await db_session.commit()

        # Act
        result = await transparency_page_service.send_review_reminders(db_session, days_ahead=30)

        # Assert
        assert result["sent"] is False
        assert result["pages_due"] == 0
        assert result["email_sent_to"] is None
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_send_review_reminders_no_admin_email(self, db_session: AsyncSession) -> None:
        """Test when pages are due but no admin email configured."""
        from app.services import transparency_page_service

        # Arrange: Create overdue page
        now = datetime.now(timezone.utc)
        page = TransparencyPage(
            slug="overdue-no-email",
            title={"en": "Overdue", "nl": "Achterstallig"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
            last_reviewed=now - timedelta(days=400),
            next_review_due=now - timedelta(days=35),
        )
        db_session.add(page)
        await db_session.commit()

        # Act: Call without admin_email and with settings.ADMIN_EMAIL = None
        with patch("app.core.config.settings.ADMIN_EMAIL", None):
            result = await transparency_page_service.send_review_reminders(
                db_session, days_ahead=30, admin_email=None
            )

        # Assert
        assert result["sent"] is False
        assert result["pages_due"] == 1
        assert result["email_sent_to"] is None
        assert result["error"] == "No admin email configured"

    @pytest.mark.asyncio
    async def test_send_review_reminders_with_admin_email(self, db_session: AsyncSession) -> None:
        """Test sending reminders when pages are due and admin email is provided."""
        from app.services import transparency_page_service

        # Arrange: Create overdue page
        now = datetime.now(timezone.utc)
        page = TransparencyPage(
            slug="overdue-with-email",
            title={"en": "Overdue Page", "nl": "Achterstallige Pagina"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
            last_reviewed=now - timedelta(days=400),
            next_review_due=now - timedelta(days=35),
        )
        db_session.add(page)
        await db_session.commit()

        # Act: Mock the email sending function (patch at import location in service)
        with patch("app.services.email_service.send_review_reminder_email") as mock_send:
            mock_send.return_value = True
            result = await transparency_page_service.send_review_reminders(
                db_session, days_ahead=30, admin_email="admin@test.com"
            )

        # Assert
        assert result["sent"] is True
        assert result["pages_due"] == 1
        assert result["email_sent_to"] == "admin@test.com"
        assert result["error"] is None
        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_review_reminders_email_fails(self, db_session: AsyncSession) -> None:
        """Test when email sending fails."""
        from app.services import transparency_page_service

        # Arrange
        now = datetime.now(timezone.utc)
        page = TransparencyPage(
            slug="email-fail-test",
            title={"en": "Test Page", "nl": "Test Pagina"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
            last_reviewed=now - timedelta(days=400),
            next_review_due=now - timedelta(days=35),
        )
        db_session.add(page)
        await db_session.commit()

        # Act: Mock email sending to fail
        with patch("app.services.email_service.send_review_reminder_email") as mock_send:
            mock_send.return_value = False
            result = await transparency_page_service.send_review_reminders(
                db_session, days_ahead=30, admin_email="admin@test.com"
            )

        # Assert
        assert result["sent"] is False
        assert result["pages_due"] == 1
        assert result["email_sent_to"] is None
        assert result["error"] == "Failed to send email"


class TestTransparencyPageServiceDeletePage:
    """Tests for delete_page functionality."""

    @pytest.mark.asyncio
    async def test_delete_page_success(self, db_session: AsyncSession) -> None:
        """Test deleting an existing page."""
        from app.services import transparency_page_service

        # Arrange
        page = TransparencyPage(
            slug="to-delete",
            title={"en": "Delete Me", "nl": "Verwijder Mij"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        # Act
        result = await transparency_page_service.delete_page(db_session, "to-delete")

        # Assert
        assert result is True
        # Verify page is gone
        deleted_page = await transparency_page_service.get_page_by_slug(db_session, "to-delete")
        assert deleted_page is None

    @pytest.mark.asyncio
    async def test_delete_page_not_found(self, db_session: AsyncSession) -> None:
        """Test deleting a non-existent page returns False."""
        from app.services import transparency_page_service

        # Act
        result = await transparency_page_service.delete_page(db_session, "nonexistent-page")

        # Assert
        assert result is False


class TestEmailService:
    """Tests for EmailService class."""

    def test_email_service_not_configured(self) -> None:
        """Test EmailService returns False when SMTP not configured."""
        from app.services.email_service import EmailService

        # Create email service - SMTP is not configured in test environment
        service = EmailService()
        # In test environment, SMTP should not be configured
        # So send_email should return False
        result = service.send_email(
            to_email="test@example.com",
            subject="Test",
            body_html="<p>Test</p>",
        )
        # Since SMTP is not configured in test env, this should return False
        assert result is False
        # Also verify the is_configured property returns False
        assert service.is_configured is False

    def test_send_review_reminder_email_empty_list(self) -> None:
        """Test sending reminder with empty page list returns True."""
        from app.services.email_service import send_review_reminder_email

        result = send_review_reminder_email(
            to_email="admin@test.com",
            page_slugs=[],
            page_titles=[],
            due_dates=[],
        )
        assert result is True  # No email needed for empty list
