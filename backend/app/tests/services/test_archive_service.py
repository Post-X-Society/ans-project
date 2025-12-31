"""
Tests for Archive Service - URL Archiving via Wayback Machine.

Issue #71: Backend: URL Archiving Integration (Wayback Machine)
EPIC #49: Evidence & Source Management
ADR 0005: EFCSN Compliance Architecture

TDD: These tests are written FIRST before implementation.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.archive_service import (
    ArchiveResult,
    ArchiveService,
    ArchiveValidationError,
    archive_url,
    get_archive_service,
)


class TestArchiveServiceConfiguration:
    """Tests for Archive Service configuration and initialization."""

    def test_archive_service_initializes_with_defaults(self) -> None:
        """Test that ArchiveService initializes with default configuration."""
        service = ArchiveService()
        assert service.wayback_save_url == "https://web.archive.org/save/"
        assert service.wayback_check_url == "https://archive.org/wayback/available"
        assert service.max_retries == 3
        assert service.retry_delay == 2.0
        assert service.timeout == 30.0

    def test_archive_service_accepts_custom_configuration(self) -> None:
        """Test that ArchiveService accepts custom configuration."""
        service = ArchiveService(
            max_retries=5,
            retry_delay=1.0,
            timeout=60.0,
        )
        assert service.max_retries == 5
        assert service.retry_delay == 1.0
        assert service.timeout == 60.0

    def test_get_archive_service_returns_singleton(self) -> None:
        """Test that get_archive_service returns a singleton instance."""
        service1 = get_archive_service()
        service2 = get_archive_service()
        assert service1 is service2


class TestArchiveResult:
    """Tests for ArchiveResult dataclass."""

    def test_archive_result_success_structure(self) -> None:
        """Test ArchiveResult structure for successful archive."""
        result = ArchiveResult(
            success=True,
            original_url="https://example.com/article",
            archived_url="https://web.archive.org/web/20251231/https://example.com/article",
            archived_at=datetime.now(timezone.utc),
            method="wayback",
        )
        assert result.success is True
        assert result.original_url == "https://example.com/article"
        assert result.archived_url is not None
        assert "web.archive.org" in result.archived_url
        assert result.method == "wayback"
        assert result.error is None

    def test_archive_result_failure_structure(self) -> None:
        """Test ArchiveResult structure for failed archive."""
        result = ArchiveResult(
            success=False,
            original_url="https://example.com/article",
            archived_url=None,
            archived_at=None,
            method="wayback",
            error="Failed to connect to Wayback Machine",
        )
        assert result.success is False
        assert result.archived_url is None
        assert result.error == "Failed to connect to Wayback Machine"


class TestURLValidation:
    """Tests for URL validation in Archive Service."""

    @pytest.mark.asyncio
    async def test_archive_url_rejects_empty_url(self) -> None:
        """Test that empty URLs are rejected."""
        with pytest.raises(ArchiveValidationError) as exc_info:
            await archive_url("")
        assert "URL cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_archive_url_rejects_none_url(self) -> None:
        """Test that None URLs are rejected."""
        with pytest.raises(ArchiveValidationError) as exc_info:
            await archive_url(None)  # type: ignore[arg-type]
        assert "URL cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_archive_url_rejects_invalid_scheme(self) -> None:
        """Test that URLs without http/https scheme are rejected."""
        with pytest.raises(ArchiveValidationError) as exc_info:
            await archive_url("ftp://example.com/file")
        assert "URL must start with http:// or https://" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_archive_url_rejects_malformed_url(self) -> None:
        """Test that malformed URLs are rejected."""
        with pytest.raises(ArchiveValidationError) as exc_info:
            await archive_url("not-a-valid-url")
        assert "URL must start with http:// or https://" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_archive_url_accepts_http_url(self) -> None:
        """Test that http URLs are accepted."""
        service = ArchiveService()
        # Should not raise - validation passes
        service._validate_url("http://example.com/article")

    @pytest.mark.asyncio
    async def test_archive_url_accepts_https_url(self) -> None:
        """Test that https URLs are accepted."""
        service = ArchiveService()
        # Should not raise - validation passes
        service._validate_url("https://example.com/article")


class TestWaybackMachineArchiving:
    """Tests for Wayback Machine archiving functionality."""

    @pytest.mark.asyncio
    async def test_archive_url_success(self) -> None:
        """Test successful URL archiving via Wayback Machine."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            "Content-Location": "/web/20251231120000/https://example.com/article"
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("https://example.com/article")

            assert result.success is True
            assert result.original_url == "https://example.com/article"
            assert result.archived_url is not None
            assert "web.archive.org" in result.archived_url
            assert result.method == "wayback"
            assert result.archived_at is not None

    @pytest.mark.asyncio
    async def test_archive_url_extracts_location_from_response(self) -> None:
        """Test that archived URL is correctly extracted from response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Location": "/web/20251231120000/https://example.com/page"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("https://example.com/page")

            assert (
                result.archived_url
                == "https://web.archive.org/web/20251231120000/https://example.com/page"
            )

    @pytest.mark.asyncio
    async def test_archive_url_handles_redirect_response(self) -> None:
        """Test handling of redirect response from Wayback Machine."""
        mock_response = MagicMock()
        mock_response.status_code = 302
        mock_response.headers = {
            "Location": "https://web.archive.org/web/20251231/https://example.com"
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("https://example.com")

            assert result.success is True
            assert result.archived_url == "https://web.archive.org/web/20251231/https://example.com"


class TestRetryLogic:
    """Tests for retry logic in Archive Service."""

    @pytest.mark.asyncio
    async def test_archive_url_retries_on_connection_error(self) -> None:
        """Test that archive_url retries on connection errors."""
        call_count = 0

        async def mock_get(*args: object, **kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("Connection failed")
            response = MagicMock()
            response.status_code = 200
            response.headers = {"Content-Location": "/web/20251231/https://example.com"}
            return response

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = mock_get
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("https://example.com", max_retries=3)

            assert result.success is True
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_archive_url_retries_on_timeout(self) -> None:
        """Test that archive_url retries on timeout errors."""
        call_count = 0

        async def mock_get(*args: object, **kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("Request timed out")
            response = MagicMock()
            response.status_code = 200
            response.headers = {"Content-Location": "/web/20251231/https://example.com"}
            return response

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = mock_get
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("https://example.com", max_retries=3)

            assert result.success is True
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_archive_url_retries_on_503_error(self) -> None:
        """Test that archive_url retries on 503 Service Unavailable errors."""
        call_count = 0

        async def mock_get(*args: object, **kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            if call_count < 2:
                response.status_code = 503
                response.raise_for_status = MagicMock(
                    side_effect=httpx.HTTPStatusError(
                        "503 Service Unavailable",
                        request=MagicMock(),
                        response=response,
                    )
                )
            else:
                response.status_code = 200
                response.headers = {"Content-Location": "/web/20251231/https://example.com"}
                response.raise_for_status = MagicMock()
            return response

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = mock_get
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("https://example.com", max_retries=3)

            assert result.success is True
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_archive_url_fails_after_max_retries(self) -> None:
        """Test that archive_url fails after exhausting all retries."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = httpx.ConnectError("Connection failed")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("https://example.com", max_retries=3)

            assert result.success is False
            assert result.archived_url is None
            assert result.error is not None
            assert "Connection failed" in result.error

    @pytest.mark.asyncio
    async def test_archive_url_uses_exponential_backoff(self) -> None:
        """Test that retry uses exponential backoff delay."""
        delays: list[float] = []

        async def mock_sleep(delay: float) -> None:
            delays.append(delay)

        with (
            patch("httpx.AsyncClient") as mock_client,
            patch("asyncio.sleep", side_effect=mock_sleep),
        ):
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = httpx.ConnectError("Connection failed")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            await archive_url("https://example.com", max_retries=3, retry_delay=1.0)

            # Should have delays: 1.0, 2.0 (exponential backoff)
            assert len(delays) == 2
            assert delays[0] == 1.0
            assert delays[1] == 2.0


class TestErrorHandling:
    """Tests for error handling in Archive Service."""

    @pytest.mark.asyncio
    async def test_archive_url_handles_http_error_gracefully(self) -> None:
        """Test that HTTP errors are handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=MagicMock(),
                response=mock_response,
            )
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("https://example.com", max_retries=1)

            assert result.success is False
            assert result.error is not None
            assert "500" in result.error or "Internal Server Error" in result.error

    @pytest.mark.asyncio
    async def test_archive_url_handles_network_error_gracefully(self) -> None:
        """Test that network errors are handled gracefully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = httpx.RequestError("Network unreachable")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("https://example.com", max_retries=1)

            assert result.success is False
            assert result.error is not None
            assert "Network unreachable" in result.error

    @pytest.mark.asyncio
    async def test_archive_url_returns_result_not_raises_on_failure(self) -> None:
        """Test that failures return ArchiveResult, not raise exceptions."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = Exception("Unexpected error")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            # Should not raise - returns ArchiveResult with success=False
            result = await archive_url("https://example.com", max_retries=1)

            assert result.success is False
            assert result.error is not None


class TestExistingArchiveCheck:
    """Tests for checking existing archives before creating new ones."""

    @pytest.mark.asyncio
    async def test_check_existing_archive_returns_url_if_exists(self) -> None:
        """Test that existing archive is returned if available."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "archived_snapshots": {
                "closest": {
                    "available": True,
                    "url": "https://web.archive.org/web/20251230/https://example.com",
                    "timestamp": "20251230120000",
                    "status": "200",
                }
            }
        }

        service = ArchiveService()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await service.check_existing_archive("https://example.com")

            assert result is not None
            assert "web.archive.org" in result

    @pytest.mark.asyncio
    async def test_check_existing_archive_returns_none_if_not_exists(self) -> None:
        """Test that None is returned if no archive exists."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"archived_snapshots": {}}

        service = ArchiveService()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await service.check_existing_archive("https://example.com")

            assert result is None


class TestArchiveServiceClass:
    """Tests for ArchiveService class methods."""

    @pytest.mark.asyncio
    async def test_archive_method_validates_url(self) -> None:
        """Test that archive method validates URL before archiving."""
        service = ArchiveService()

        with pytest.raises(ArchiveValidationError):
            await service.archive("")

    @pytest.mark.asyncio
    async def test_archive_method_returns_archive_result(self) -> None:
        """Test that archive method returns ArchiveResult."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Location": "/web/20251231/https://example.com"}

        service = ArchiveService()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await service.archive("https://example.com")

            assert isinstance(result, ArchiveResult)
            assert result.original_url == "https://example.com"


class TestModuleLevelFunction:
    """Tests for module-level archive_url function."""

    @pytest.mark.asyncio
    async def test_archive_url_function_uses_default_service(self) -> None:
        """Test that archive_url uses default service configuration."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Location": "/web/20251231/https://example.com"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("https://example.com")

            assert result.success is True

    @pytest.mark.asyncio
    async def test_archive_url_function_accepts_optional_parameters(self) -> None:
        """Test that archive_url accepts optional retry parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Location": "/web/20251231/https://example.com"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url(
                "https://example.com",
                max_retries=5,
                retry_delay=0.5,
                timeout=10.0,
            )

            assert result.success is True


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_archive_url_handles_long_urls(self) -> None:
        """Test archiving very long URLs."""
        long_path = "a" * 2000
        long_url = f"https://example.com/{long_path}"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Location": f"/web/20251231/{long_url}"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url(long_url)

            assert result.success is True

    @pytest.mark.asyncio
    async def test_archive_url_handles_special_characters_in_url(self) -> None:
        """Test archiving URLs with special characters."""
        special_url = "https://example.com/path?query=value&other=test#fragment"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Location": f"/web/20251231/{special_url}"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url(special_url)

            assert result.success is True

    @pytest.mark.asyncio
    async def test_archive_url_handles_unicode_in_url(self) -> None:
        """Test archiving URLs with unicode characters."""
        unicode_url = "https://example.com/path/日本語"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            "Content-Location": "/web/20251231/https://example.com/path/%E6%97%A5%E6%9C%AC%E8%AA%9E"
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url(unicode_url)

            assert result.success is True

    @pytest.mark.asyncio
    async def test_archive_url_handles_missing_location_header(self) -> None:
        """Test handling response without Content-Location header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}  # No Content-Location

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("https://example.com")

            # Should construct URL from request URL
            assert result.success is True
            assert result.archived_url is not None

    @pytest.mark.asyncio
    async def test_archive_url_trims_whitespace_from_url(self) -> None:
        """Test that whitespace is trimmed from URLs."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Location": "/web/20251231/https://example.com"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_url("  https://example.com  ")

            assert result.success is True
            assert result.original_url == "https://example.com"


class TestSourceArchivingIntegration:
    """Tests for source service integration with archive service."""

    @pytest.mark.asyncio
    async def test_archive_source_url_success(self) -> None:
        """Test archiving a source URL and updating the source."""
        from app.services.archive_service import archive_source_url

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            "Content-Location": "/web/20251231/https://source.example.com/article"
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_source_url("https://source.example.com/article")

            assert result is not None
            assert result.success is True
            assert result.archived_url is not None
            assert "web.archive.org" in result.archived_url

    @pytest.mark.asyncio
    async def test_archive_source_url_returns_none_for_empty_url(self) -> None:
        """Test that archive_source_url returns None for empty URL."""
        from app.services.archive_service import archive_source_url

        result = await archive_source_url("")

        assert result is None

    @pytest.mark.asyncio
    async def test_archive_source_url_returns_none_for_none_url(self) -> None:
        """Test that archive_source_url returns None for None URL."""
        from app.services.archive_service import archive_source_url

        result = await archive_source_url(None)

        assert result is None

    @pytest.mark.asyncio
    async def test_archive_source_url_handles_failure_gracefully(self) -> None:
        """Test that archive_source_url handles failures gracefully."""
        from app.services.archive_service import archive_source_url

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = httpx.ConnectError("Connection failed")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await archive_source_url("https://example.com", max_retries=1)

            # Should return result with failure, not raise
            assert result is not None
            assert result.success is False
