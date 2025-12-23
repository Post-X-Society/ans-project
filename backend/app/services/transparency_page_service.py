"""
Service layer for Transparency Page operations.

Issue #83: Backend: Transparency Page Service with Versioning
EPIC #51: Transparency & Methodology Pages
ADR 0005: EFCSN Compliance Architecture

Implements:
- CRUD operations for transparency pages
- Automatic versioning on updates
- Version history and diff generation
- Annual review tracking
"""

import difflib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transparency_page import TransparencyPage, TransparencyPageVersion


async def get_page_by_slug(
    db: AsyncSession,
    slug: str,
    language: Optional[str] = None,
) -> Optional[TransparencyPage]:
    """
    Retrieve a transparency page by its slug.

    Args:
        db: Database session
        slug: URL-friendly page identifier (e.g., "methodology")
        language: Optional language code for filtering response (en, nl)
                  Note: Page always contains all languages, this is for API response formatting

    Returns:
        TransparencyPage if found, None otherwise
    """
    stmt = select(TransparencyPage).where(TransparencyPage.slug == slug)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_page_version(
    db: AsyncSession,
    slug: str,
    version: int,
) -> Optional[TransparencyPageVersion]:
    """
    Retrieve a specific version of a transparency page.

    Args:
        db: Database session
        slug: URL-friendly page identifier
        version: Version number to retrieve

    Returns:
        TransparencyPageVersion if found, None otherwise
    """
    # First get the page
    page_stmt = select(TransparencyPage).where(TransparencyPage.slug == slug)
    page_result = await db.execute(page_stmt)
    page = page_result.scalar_one_or_none()

    if page is None:
        return None

    # Get the specific version from history
    version_stmt = select(TransparencyPageVersion).where(
        TransparencyPageVersion.page_id == page.id,
        TransparencyPageVersion.version == version,
    )
    version_result = await db.execute(version_stmt)
    return version_result.scalar_one_or_none()


async def create_page(
    db: AsyncSession,
    slug: str,
    title: dict[str, str],
    content: dict[str, str],
    created_by_id: UUID,
) -> TransparencyPage:
    """
    Create a new transparency page.

    Args:
        db: Database session
        slug: URL-friendly page identifier (must be unique)
        title: Multilingual title dict {"en": "...", "nl": "..."}
        content: Multilingual content dict {"en": "...", "nl": "..."}
        created_by_id: ID of the user creating the page

    Returns:
        Created TransparencyPage

    Raises:
        IntegrityError: If slug already exists
    """
    now = datetime.now(timezone.utc)
    next_review = now + timedelta(days=365)

    page = TransparencyPage(
        slug=slug,
        title=title,
        content=content,
        version=1,
        last_reviewed=now,
        next_review_due=next_review,
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)

    return page


async def update_page(
    db: AsyncSession,
    slug: str,
    title: Optional[dict[str, str]],
    content: Optional[dict[str, str]],
    changed_by_id: UUID,
    change_summary: str,
) -> Optional[TransparencyPage]:
    """
    Update a transparency page with automatic versioning.

    Creates a version history record of the current state before updating.
    Increments the version number and updates review dates.

    Args:
        db: Database session
        slug: URL-friendly page identifier
        title: New multilingual title (or None to keep current)
        content: New multilingual content (or None to keep current)
        changed_by_id: ID of the user making the change
        change_summary: Description of changes made

    Returns:
        Updated TransparencyPage if found, None if page doesn't exist
    """
    # Get the current page
    stmt = select(TransparencyPage).where(TransparencyPage.slug == slug)
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()

    if page is None:
        return None

    # Create version history record of current state BEFORE updating
    version_record = TransparencyPageVersion(
        page_id=page.id,
        version=page.version,
        title=page.title,
        content=page.content,
        changed_by_id=changed_by_id,
        change_summary=change_summary,
    )
    db.add(version_record)

    # Update the page
    if title is not None:
        page.title = title
    if content is not None:
        page.content = content

    page.version += 1

    # Update review dates (marks as reviewed, sets next annual review)
    now = datetime.now(timezone.utc)
    page.last_reviewed = now
    page.next_review_due = now + timedelta(days=365)

    await db.commit()
    await db.refresh(page)

    return page


async def get_version_history(
    db: AsyncSession,
    slug: str,
) -> list[TransparencyPageVersion]:
    """
    Get all version history entries for a page.

    Args:
        db: Database session
        slug: URL-friendly page identifier

    Returns:
        List of TransparencyPageVersion ordered by version (ascending)
    """
    # Get the page first
    page_stmt = select(TransparencyPage).where(TransparencyPage.slug == slug)
    page_result = await db.execute(page_stmt)
    page = page_result.scalar_one_or_none()

    if page is None:
        return []

    # Get all versions
    stmt = (
        select(TransparencyPageVersion)
        .where(TransparencyPageVersion.page_id == page.id)
        .order_by(TransparencyPageVersion.version)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def generate_diff(
    db: AsyncSession,
    slug: str,
    from_version: int,
    to_version: int,
    language: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Generate a diff between two versions of a page.

    Uses Python's difflib to compute unified diff of content.

    Args:
        db: Database session
        slug: URL-friendly page identifier
        from_version: Starting version number
        to_version: Ending version number
        language: Optional language code to diff only that language's content

    Returns:
        Dict with diff information:
        {
            "slug": str,
            "from_version": int,
            "to_version": int,
            "diff": {
                "title": {...},  # Diff for each language
                "content": {...}  # Diff for each language
            },
            "language": str or None
        }
        Returns None if versions don't exist
    """
    # Get the page
    page_stmt = select(TransparencyPage).where(TransparencyPage.slug == slug)
    page_result = await db.execute(page_stmt)
    page = page_result.scalar_one_or_none()

    if page is None:
        return None

    # Get from_version content
    from_content: Optional[dict[str, Any]] = None
    from_title: Optional[dict[str, Any]] = None

    if from_version == page.version:
        # Current version
        from_content = page.content
        from_title = page.title
    else:
        # Historical version
        from_ver = await get_page_version(db, slug, from_version)
        if from_ver is None:
            return None
        from_content = from_ver.content
        from_title = from_ver.title

    # Get to_version content
    to_content: Optional[dict[str, Any]] = None
    to_title: Optional[dict[str, Any]] = None

    if to_version == page.version:
        # Current version
        to_content = page.content
        to_title = page.title
    else:
        # Historical version
        to_ver = await get_page_version(db, slug, to_version)
        if to_ver is None:
            return None
        to_content = to_ver.content
        to_title = to_ver.title

    # Generate diffs
    diff_result: dict[str, Any] = {
        "title": {},
        "content": {},
    }

    # Determine which languages to diff
    languages = [language] if language else list(set(from_content.keys()) | set(to_content.keys()))

    for lang in languages:
        # Title diff
        from_title_text = str(from_title.get(lang, ""))
        to_title_text = str(to_title.get(lang, ""))
        title_diff = list(
            difflib.unified_diff(
                from_title_text.splitlines(keepends=True),
                to_title_text.splitlines(keepends=True),
                fromfile=f"v{from_version}",
                tofile=f"v{to_version}",
                lineterm="",
            )
        )
        diff_result["title"][lang] = "".join(title_diff)

        # Content diff
        from_content_text = str(from_content.get(lang, ""))
        to_content_text = str(to_content.get(lang, ""))
        content_diff = list(
            difflib.unified_diff(
                from_content_text.splitlines(keepends=True),
                to_content_text.splitlines(keepends=True),
                fromfile=f"v{from_version}",
                tofile=f"v{to_version}",
                lineterm="",
            )
        )
        diff_result["content"][lang] = "".join(content_diff)

    return {
        "slug": slug,
        "from_version": from_version,
        "to_version": to_version,
        "diff": diff_result,
        "language": language,
    }


async def get_pages_due_for_review(
    db: AsyncSession,
    days_ahead: int = 30,
) -> list[TransparencyPage]:
    """
    Find transparency pages that are due for annual review.

    Returns pages where next_review_due is within the specified days_ahead
    or already past (overdue).

    Args:
        db: Database session
        days_ahead: Number of days to look ahead for upcoming reviews

    Returns:
        List of TransparencyPage objects due for review
    """
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_ahead)

    stmt = (
        select(TransparencyPage)
        .where(TransparencyPage.next_review_due <= cutoff)
        .order_by(TransparencyPage.next_review_due)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_all_pages(db: AsyncSession) -> list[TransparencyPage]:
    """
    List all transparency pages.

    Args:
        db: Database session

    Returns:
        List of all TransparencyPage objects
    """
    stmt = select(TransparencyPage).order_by(TransparencyPage.slug)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_page(db: AsyncSession, slug: str) -> bool:
    """
    Delete a transparency page and all its version history.

    Args:
        db: Database session
        slug: URL-friendly page identifier

    Returns:
        True if page was deleted, False if page didn't exist
    """
    stmt = select(TransparencyPage).where(TransparencyPage.slug == slug)
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()

    if page is None:
        return False

    await db.delete(page)
    await db.commit()
    return True


async def send_review_reminders(
    db: AsyncSession,
    days_ahead: int = 30,
    admin_email: Optional[str] = None,
) -> dict[str, Any]:
    """
    Send email reminders for transparency pages due for annual review.

    Args:
        db: Database session
        days_ahead: Number of days to look ahead for upcoming reviews
        admin_email: Override admin email (uses settings.ADMIN_EMAIL if not provided)

    Returns:
        Dict with:
        {
            "sent": bool,
            "pages_due": int,
            "email_sent_to": str or None,
            "error": str or None
        }
    """
    from app.core.config import settings
    from app.services.email_service import send_review_reminder_email

    # Get pages due for review
    due_pages = await get_pages_due_for_review(db, days_ahead)

    if not due_pages:
        return {
            "sent": False,
            "pages_due": 0,
            "email_sent_to": None,
            "error": None,
        }

    # Determine recipient
    recipient = admin_email or settings.ADMIN_EMAIL
    if not recipient:
        return {
            "sent": False,
            "pages_due": len(due_pages),
            "email_sent_to": None,
            "error": "No admin email configured",
        }

    # Prepare data for email
    page_slugs = [p.slug for p in due_pages]
    page_titles = [p.title for p in due_pages]
    due_dates = [p.next_review_due for p in due_pages if p.next_review_due]

    # Send the email
    success = send_review_reminder_email(
        to_email=recipient,
        page_slugs=page_slugs,
        page_titles=page_titles,
        due_dates=due_dates,
    )

    return {
        "sent": success,
        "pages_due": len(due_pages),
        "email_sent_to": recipient if success else None,
        "error": None if success else "Failed to send email",
    }
