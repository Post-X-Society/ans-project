"""
Archive Service for URL archiving via Wayback Machine.

Issue #71: Backend: URL Archiving Integration (Wayback Machine)
EPIC #49: Evidence & Source Management
ADR 0005: EFCSN Compliance Architecture

This service provides:
- URL archiving via Internet Archive Wayback Machine
- Retry logic with exponential backoff for failed requests
- Checking for existing archives before creating new ones
- Graceful error handling with detailed result objects
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx


class ArchiveServiceError(Exception):
    """Base exception for Archive Service errors."""

    pass


class ArchiveValidationError(ArchiveServiceError):
    """Raised when URL validation fails."""

    pass


class ArchiveError(ArchiveServiceError):
    """Raised when archiving operation fails."""

    pass


@dataclass
class ArchiveResult:
    """Result of an archive operation.

    Attributes:
        success: Whether the archiving was successful
        original_url: The original URL that was archived
        archived_url: The archived URL (if successful)
        archived_at: When the archive was created
        method: The method used for archiving ('wayback', 'screenshot', etc.)
        error: Error message if archiving failed
    """

    success: bool
    original_url: str
    archived_url: Optional[str]
    archived_at: Optional[datetime]
    method: str
    error: Optional[str] = None


class ArchiveService:
    """Service for archiving URLs via Wayback Machine.

    This service integrates with the Internet Archive's Wayback Machine API
    to create and retrieve archived snapshots of web pages.

    Attributes:
        wayback_save_url: URL for saving new archives
        wayback_check_url: URL for checking existing archives
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (exponential backoff)
        timeout: HTTP request timeout in seconds
    """

    WAYBACK_SAVE_URL = "https://web.archive.org/save/"
    WAYBACK_CHECK_URL = "https://archive.org/wayback/available"
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 2.0
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the Archive Service.

        Args:
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Initial delay between retries (uses exponential backoff)
            timeout: HTTP request timeout in seconds
        """
        self.wayback_save_url = self.WAYBACK_SAVE_URL
        self.wayback_check_url = self.WAYBACK_CHECK_URL
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    def _validate_url(self, url: str) -> str:
        """Validate and normalize a URL.

        Args:
            url: The URL to validate

        Returns:
            The normalized URL

        Raises:
            ArchiveValidationError: If the URL is invalid
        """
        if not url:
            raise ArchiveValidationError("URL cannot be empty")

        # Trim whitespace
        url = url.strip()

        if not url:
            raise ArchiveValidationError("URL cannot be empty")

        # Check URL scheme
        if not url.startswith(("http://", "https://")):
            raise ArchiveValidationError("URL must start with http:// or https://")

        return url

    async def check_existing_archive(self, url: str) -> Optional[str]:
        """Check if an archive already exists for a URL.

        Args:
            url: The URL to check for existing archive

        Returns:
            The archived URL if one exists, None otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.wayback_check_url,
                    params={"url": url},
                )
                response.raise_for_status()

                data = response.json()
                snapshots = data.get("archived_snapshots", {})
                closest = snapshots.get("closest", {})

                if closest.get("available"):
                    archived_url: str | None = closest.get("url")
                    return archived_url

                return None

        except (httpx.HTTPError, Exception):
            # If we can't check, return None and proceed with archiving
            return None

    def _extract_archived_url(self, response: httpx.Response, original_url: str) -> str:
        """Extract the archived URL from the response.

        Args:
            response: The HTTP response from the Wayback Machine
            original_url: The original URL that was archived

        Returns:
            The full archived URL
        """
        # Try Content-Location header first
        content_location: str | None = response.headers.get("Content-Location")
        if content_location:
            if content_location.startswith("/web/"):
                return f"https://web.archive.org{content_location}"
            return str(content_location)

        # Try Location header (for redirects)
        location: str | None = response.headers.get("Location")
        if location:
            if location.startswith("/web/"):
                return f"https://web.archive.org{location}"
            return str(location)

        # Fall back to constructing URL from timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"https://web.archive.org/web/{timestamp}/{original_url}"

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error should trigger a retry.

        Args:
            error: The exception that occurred

        Returns:
            True if the error is retryable, False otherwise
        """
        # Connection errors are always retryable
        if isinstance(error, (httpx.ConnectError, httpx.TimeoutException)):
            return True

        # HTTP status errors - retry on server errors
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            # Retry on 5xx errors and 429 (rate limiting)
            return status_code >= 500 or status_code == 429

        return False

    async def archive(self, url: str) -> ArchiveResult:
        """Archive a URL via Wayback Machine.

        Args:
            url: The URL to archive

        Returns:
            ArchiveResult with success status and archived URL

        Raises:
            ArchiveValidationError: If the URL is invalid
        """
        # Validate URL (raises ArchiveValidationError if invalid)
        normalized_url = self._validate_url(url)

        last_error: Optional[Exception] = None
        attempt = 0

        while attempt < self.max_retries:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    save_url = f"{self.wayback_save_url}{normalized_url}"
                    response = await client.get(save_url)

                    # Check for success (200-299 or redirect 3xx)
                    if response.status_code < 400:
                        archived_url = self._extract_archived_url(response, normalized_url)
                        return ArchiveResult(
                            success=True,
                            original_url=normalized_url,
                            archived_url=archived_url,
                            archived_at=datetime.now(timezone.utc),
                            method="wayback",
                        )

                    # Raise for status to trigger retry logic
                    response.raise_for_status()

            except Exception as e:
                last_error = e
                attempt += 1

                if attempt < self.max_retries and self._is_retryable_error(e):
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
                    continue

                # Non-retryable error or max retries exceeded
                break

        # All retries exhausted
        error_message = str(last_error) if last_error else "Unknown error"
        return ArchiveResult(
            success=False,
            original_url=normalized_url,
            archived_url=None,
            archived_at=None,
            method="wayback",
            error=error_message,
        )


# Singleton instance
_archive_service: Optional[ArchiveService] = None


def get_archive_service() -> ArchiveService:
    """Get the singleton ArchiveService instance.

    Returns:
        The ArchiveService singleton
    """
    global _archive_service
    if _archive_service is None:
        _archive_service = ArchiveService()
    return _archive_service


async def archive_url(
    url: str,
    max_retries: Optional[int] = None,
    retry_delay: Optional[float] = None,
    timeout: Optional[float] = None,
) -> ArchiveResult:
    """Archive a URL via Wayback Machine.

    This is a convenience function that uses the singleton ArchiveService.

    Args:
        url: The URL to archive
        max_retries: Optional custom max retries (uses default if not specified)
        retry_delay: Optional custom retry delay (uses default if not specified)
        timeout: Optional custom timeout (uses default if not specified)

    Returns:
        ArchiveResult with success status and archived URL

    Raises:
        ArchiveValidationError: If the URL is invalid
    """
    # Create custom service if any parameters are provided
    if any([max_retries, retry_delay, timeout]):
        service = ArchiveService(
            max_retries=max_retries or ArchiveService.DEFAULT_MAX_RETRIES,
            retry_delay=retry_delay or ArchiveService.DEFAULT_RETRY_DELAY,
            timeout=timeout or ArchiveService.DEFAULT_TIMEOUT,
        )
        return await service.archive(url)

    # Use singleton for default parameters
    return await get_archive_service().archive(url)


async def archive_source_url(
    url: Optional[str],
    max_retries: Optional[int] = None,
    retry_delay: Optional[float] = None,
    timeout: Optional[float] = None,
) -> Optional[ArchiveResult]:
    """Archive a source URL for EFCSN compliance.

    This function is designed for integration with the Source Service.
    It gracefully handles empty/None URLs by returning None instead of raising.

    Args:
        url: The source URL to archive (can be None or empty)
        max_retries: Optional custom max retries (uses default if not specified)
        retry_delay: Optional custom retry delay (uses default if not specified)
        timeout: Optional custom timeout (uses default if not specified)

    Returns:
        ArchiveResult if URL was provided and archiving was attempted,
        None if URL was empty/None
    """
    # Return None for empty/None URLs instead of raising
    if not url or not url.strip():
        return None

    # Attempt to archive
    try:
        return await archive_url(
            url,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
        )
    except ArchiveValidationError:
        # Return None for invalid URLs instead of raising
        return None
