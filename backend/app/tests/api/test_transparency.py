"""
Tests for Transparency Page API Endpoints - TDD Approach (Tests written FIRST)

Issue #84: Backend: Transparency Page API Endpoints
EPIC #51: Transparency & Methodology Pages
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- GET /api/v1/transparency/{slug} - Public endpoint for page content
- PATCH /api/v1/transparency/{slug} - Admin-only endpoint for updates
- GET /api/v1/transparency/{slug}/versions - Version history
- GET /api/v1/transparency/{slug}/diff/{v1}/{v2} - Version comparison
- POST /api/v1/transparency/{slug}/review - Mark page as reviewed
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.transparency_page import TransparencyPage, TransparencyPageVersion
from app.models.user import User, UserRole
from app.tests.helpers import normalize_dt


class TestGetTransparencyPage:
    """Tests for GET /api/v1/transparency/{slug} - Public endpoint."""

    @pytest.mark.asyncio
    async def test_get_page_success(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test retrieving a transparency page by slug (public access)."""
        # Arrange: Create a transparency page
        page = TransparencyPage(
            slug="methodology",
            title={"en": "Fact-Checking Methodology", "nl": "Factcheck-Methodologie"},
            content={
                "en": "Our fact-checking methodology description.",
                "nl": "Onze factcheck-methodologie beschrijving.",
            },
            version=1,
            last_reviewed=datetime.now(timezone.utc),
            next_review_due=datetime.now(timezone.utc) + timedelta(days=365),
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Act: GET request (no auth required - public endpoint)
        response = client.get("/api/v1/transparency/methodology")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "methodology"
        assert data["title"]["en"] == "Fact-Checking Methodology"
        assert data["title"]["nl"] == "Factcheck-Methodologie"
        assert data["content"]["en"] == "Our fact-checking methodology description."
        assert data["version"] == 1
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_page_with_language_filter(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test retrieving page with language filter in query param."""
        # Arrange
        page = TransparencyPage(
            slug="team",
            title={"en": "Our Team", "nl": "Ons Team"},
            content={"en": "Meet our team.", "nl": "Maak kennis met ons team."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        # Act: GET with language filter
        response = client.get("/api/v1/transparency/team?lang=en")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "team"
        # Page still returns full multilingual content, but lang param can be used by frontend

    @pytest.mark.asyncio
    async def test_get_page_not_found(self, client: TestClient) -> None:
        """Test retrieving non-existent page returns 404."""
        # Act
        response = client.get("/api/v1/transparency/nonexistent-page")

        # Assert
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_page_invalid_slug(self, client: TestClient) -> None:
        """Test retrieving page with invalid slug format."""
        # Act
        response = client.get("/api/v1/transparency/invalid slug with spaces")

        # Assert
        # The route should still work, but page won't be found
        assert response.status_code == 404


class TestUpdateTransparencyPage:
    """Tests for PATCH /api/v1/transparency/{slug} - Admin only."""

    @pytest.mark.asyncio
    async def test_update_page_as_admin_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test updating a page as admin creates new version."""
        # Arrange: Create admin user
        admin = User(
            email="admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Create page to update
        page = TransparencyPage(
            slug="funding",
            title={"en": "Funding Sources", "nl": "Financieringsbronnen"},
            content={"en": "Original funding info.", "nl": "Originele financieringsinfo."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        # Create admin token
        token = create_access_token(data={"sub": str(admin.id)})

        # Act: PATCH request
        payload = {
            "title": {"en": "Updated Funding Sources", "nl": "Bijgewerkte Financieringsbronnen"},
            "content": {"en": "Updated funding info.", "nl": "Bijgewerkte financieringsinfo."},
            "change_summary": "Updated funding disclosure for 2024",
        }
        response = client.patch(
            "/api/v1/transparency/funding",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "funding"
        assert data["title"]["en"] == "Updated Funding Sources"
        assert data["content"]["en"] == "Updated funding info."
        assert data["version"] == 2  # Version should be incremented

    @pytest.mark.asyncio
    async def test_update_page_as_super_admin_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test super admin can also update pages."""
        # Arrange
        super_admin = User(
            email="superadmin@example.com",
            password_hash="hashed",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        db_session.add(super_admin)
        await db_session.commit()
        await db_session.refresh(super_admin)

        page = TransparencyPage(
            slug="privacy",
            title={"en": "Privacy Policy", "nl": "Privacybeleid"},
            content={"en": "Privacy content.", "nl": "Privacy inhoud."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        token = create_access_token(data={"sub": str(super_admin.id)})

        # Act
        payload = {
            "content": {"en": "Updated privacy.", "nl": "Bijgewerkt privacy."},
            "change_summary": "GDPR compliance update",
        }
        response = client.patch(
            "/api/v1/transparency/privacy",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_page_as_submitter_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test submitter cannot update transparency pages."""
        # Arrange
        submitter = User(
            email="submitter@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(submitter)

        page = TransparencyPage(
            slug="corrections",
            title={"en": "Corrections", "nl": "Correcties"},
            content={"en": "Corrections policy.", "nl": "Correctiebeleid."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        token = create_access_token(data={"sub": str(submitter.id)})

        # Act
        payload = {
            "content": {"en": "Hacked content!", "nl": "Gehackte inhoud!"},
            "change_summary": "Malicious update",
        }
        response = client.patch(
            "/api/v1/transparency/corrections",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_page_as_reviewer_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test reviewer cannot update transparency pages."""
        # Arrange
        reviewer = User(
            email="reviewer@example.com",
            password_hash="hashed",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db_session.add(reviewer)
        await db_session.commit()
        await db_session.refresh(reviewer)

        page = TransparencyPage(
            slug="organization",
            title={"en": "Organization", "nl": "Organisatie"},
            content={"en": "Org info.", "nl": "Org info."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        token = create_access_token(data={"sub": str(reviewer.id)})

        # Act
        payload = {
            "content": {"en": "Updated.", "nl": "Bijgewerkt."},
            "change_summary": "Reviewer update attempt",
        }
        response = client.patch(
            "/api/v1/transparency/organization",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_page_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test updating page without auth returns 401."""
        # Arrange
        page = TransparencyPage(
            slug="partnerships",
            title={"en": "Partnerships", "nl": "Partnerschappen"},
            content={"en": "Partners.", "nl": "Partners."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        # Act: No auth header
        payload = {
            "content": {"en": "Hacked!", "nl": "Gehackt!"},
            "change_summary": "Unauthorized update",
        }
        response = client.patch("/api/v1/transparency/partnerships", json=payload)

        # Assert
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_update_page_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test updating non-existent page returns 404."""
        # Arrange: Admin user
        admin = User(
            email="admin2@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        payload = {
            "content": {"en": "Content.", "nl": "Inhoud."},
            "change_summary": "Update attempt",
        }
        response = client.patch(
            "/api/v1/transparency/nonexistent",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_page_missing_change_summary(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test update requires change_summary field."""
        # Arrange
        admin = User(
            email="admin3@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        page = TransparencyPage(
            slug="test-page",
            title={"en": "Test", "nl": "Test"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        token = create_access_token(data={"sub": str(admin.id)})

        # Act: Missing change_summary
        payload = {"content": {"en": "Updated.", "nl": "Bijgewerkt."}}
        response = client.patch(
            "/api/v1/transparency/test-page",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 422  # Validation error


class TestGetVersionHistory:
    """Tests for GET /api/v1/transparency/{slug}/versions."""

    @pytest.mark.asyncio
    async def test_get_versions_success(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test retrieving version history for a page."""
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

        # Create page at version 3
        page = TransparencyPage(
            slug="versioned-page",
            title={"en": "Version 3", "nl": "Versie 3"},
            content={"en": "Content v3.", "nl": "Inhoud v3."},
            version=3,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Create version history
        for v in [1, 2]:
            version = TransparencyPageVersion(
                page_id=page.id,
                version=v,
                title={"en": f"Version {v}", "nl": f"Versie {v}"},
                content={"en": f"Content v{v}.", "nl": f"Inhoud v{v}."},
                changed_by_id=user.id,
                change_summary=f"Update to version {v + 1}",
            )
            db_session.add(version)
        await db_session.commit()

        # Act
        response = client.get("/api/v1/transparency/versioned-page/versions")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2  # v1 and v2 in history
        assert data[0]["version"] == 1
        assert data[1]["version"] == 2
        # Each version should have required fields
        assert "id" in data[0]
        assert "page_id" in data[0]
        assert "title" in data[0]
        assert "content" in data[0]
        assert "changed_by_id" in data[0]
        assert "change_summary" in data[0]
        assert "created_at" in data[0]

    @pytest.mark.asyncio
    async def test_get_versions_empty_for_new_page(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test version history is empty for newly created page."""
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
        response = client.get("/api/v1/transparency/new-page/versions")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_get_versions_page_not_found(self, client: TestClient) -> None:
        """Test getting versions for non-existent page returns 404."""
        # Act
        response = client.get("/api/v1/transparency/nonexistent/versions")

        # Assert
        assert response.status_code == 404


class TestGetVersionDiff:
    """Tests for GET /api/v1/transparency/{slug}/diff/{v1}/{v2}."""

    @pytest.mark.asyncio
    async def test_get_diff_success(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test generating diff between two versions."""
        # Arrange
        user = User(
            email="differ@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create page at version 2
        page = TransparencyPage(
            slug="diff-page",
            title={"en": "Diff Test", "nl": "Diff Test"},
            content={"en": "This is the updated content.", "nl": "Dit is bijgewerkte inhoud."},
            version=2,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        # Create version 1 in history
        version1 = TransparencyPageVersion(
            page_id=page.id,
            version=1,
            title={"en": "Diff Test", "nl": "Diff Test"},
            content={"en": "This is the original content.", "nl": "Dit is originele inhoud."},
            changed_by_id=user.id,
            change_summary="Initial version",
        )
        db_session.add(version1)
        await db_session.commit()

        # Act
        response = client.get("/api/v1/transparency/diff-page/diff/1/2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "diff-page"
        assert data["from_version"] == 1
        assert data["to_version"] == 2
        assert "diff" in data
        assert "content" in data["diff"]
        # The diff should show changes
        assert len(data["diff"]["content"]) > 0

    @pytest.mark.asyncio
    async def test_get_diff_with_language_filter(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting diff for specific language."""
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
            slug="lang-diff-page",
            title={"en": "Language Diff", "nl": "Taal Diff"},
            content={"en": "New English.", "nl": "Nieuwe Nederlandse."},
            version=2,
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)

        version1 = TransparencyPageVersion(
            page_id=page.id,
            version=1,
            title={"en": "Language Diff", "nl": "Taal Diff"},
            content={"en": "Old English.", "nl": "Oude Nederlandse."},
            changed_by_id=user.id,
            change_summary="Initial",
        )
        db_session.add(version1)
        await db_session.commit()

        # Act: Request diff with language filter
        response = client.get("/api/v1/transparency/lang-diff-page/diff/1/2?lang=en")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"

    @pytest.mark.asyncio
    async def test_get_diff_invalid_version(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test getting diff with non-existent version returns 404."""
        # Arrange
        page = TransparencyPage(
            slug="invalid-diff",
            title={"en": "Test", "nl": "Test"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        # Act: Request diff with non-existent version
        response = client.get("/api/v1/transparency/invalid-diff/diff/1/99")

        # Assert
        assert response.status_code == 404
        assert "version" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_diff_page_not_found(self, client: TestClient) -> None:
        """Test getting diff for non-existent page returns 404."""
        # Act
        response = client.get("/api/v1/transparency/nonexistent/diff/1/2")

        # Assert
        assert response.status_code == 404


class TestMarkPageReviewed:
    """Tests for POST /api/v1/transparency/{slug}/review - Mark page as reviewed."""

    @pytest.mark.asyncio
    async def test_mark_reviewed_as_admin_success(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test admin can mark page as reviewed (updates review dates)."""
        # Arrange
        admin = User(
            email="reviewer-admin@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        old_review = datetime.now(timezone.utc) - timedelta(days=400)
        page = TransparencyPage(
            slug="review-page",
            title={"en": "Review Test", "nl": "Review Test"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
            last_reviewed=old_review,
            next_review_due=old_review + timedelta(days=365),
        )
        db_session.add(page)
        await db_session.commit()

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        response = client.post(
            "/api/v1/transparency/review-page/review",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "review-page"
        # last_reviewed should be updated to now
        assert "last_reviewed" in data
        assert "next_review_due" in data
        # The review dates should be recent
        # Parse the datetime string - handle both "Z" suffix and "+00:00" formats
        last_reviewed_str = data["last_reviewed"].replace("Z", "+00:00")
        last_reviewed = datetime.fromisoformat(last_reviewed_str)
        now = datetime.now(timezone.utc)
        # Use normalize_dt helper for SQLite/PostgreSQL compatibility
        assert (normalize_dt(now) - normalize_dt(last_reviewed)).total_seconds() < 60

    @pytest.mark.asyncio
    async def test_mark_reviewed_as_super_admin(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test super admin can mark page as reviewed."""
        # Arrange
        super_admin = User(
            email="super-reviewer@example.com",
            password_hash="hashed",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        db_session.add(super_admin)
        await db_session.commit()
        await db_session.refresh(super_admin)

        page = TransparencyPage(
            slug="super-review-page",
            title={"en": "Super Review", "nl": "Super Review"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        token = create_access_token(data={"sub": str(super_admin.id)})

        # Act
        response = client.post(
            "/api/v1/transparency/super-review-page/review",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_mark_reviewed_as_submitter_forbidden(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test submitter cannot mark pages as reviewed."""
        # Arrange
        submitter = User(
            email="submitter-review@example.com",
            password_hash="hashed",
            role=UserRole.SUBMITTER,
            is_active=True,
        )
        db_session.add(submitter)
        await db_session.commit()
        await db_session.refresh(submitter)

        page = TransparencyPage(
            slug="forbidden-review",
            title={"en": "Forbidden", "nl": "Verboden"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        token = create_access_token(data={"sub": str(submitter.id)})

        # Act
        response = client.post(
            "/api/v1/transparency/forbidden-review/review",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_mark_reviewed_requires_auth(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test marking as reviewed requires authentication."""
        # Arrange
        page = TransparencyPage(
            slug="auth-review",
            title={"en": "Auth Review", "nl": "Auth Review"},
            content={"en": "Content.", "nl": "Inhoud."},
            version=1,
        )
        db_session.add(page)
        await db_session.commit()

        # Act: No auth header
        response = client.post("/api/v1/transparency/auth-review/review")

        # Assert
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_mark_reviewed_page_not_found(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Test marking non-existent page returns 404."""
        # Arrange
        admin = User(
            email="admin-notfound@example.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        token = create_access_token(data={"sub": str(admin.id)})

        # Act
        response = client.post(
            "/api/v1/transparency/nonexistent-review/review",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 404


class TestListTransparencyPages:
    """Tests for GET /api/v1/transparency - List all pages (optional endpoint)."""

    @pytest.mark.asyncio
    async def test_list_all_pages(self, client: TestClient, db_session: AsyncSession) -> None:
        """Test listing all transparency pages."""
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
        response = client.get("/api/v1/transparency")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 3
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_list_pages_empty(self, client: TestClient) -> None:
        """Test listing when no pages exist."""
        # Act
        response = client.get("/api/v1/transparency")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
