"""
Tests for CORS (Cross-Origin Resource Sharing) configuration

Security requirement: The application should only allow specific origins,
not wildcard "*" which allows any origin.

Following TDD: These tests should FAIL initially, then PASS after implementation.
"""

import pytest
from fastapi.testclient import TestClient


def test_cors_allows_configured_origin(client: TestClient) -> None:
    """
    Test that requests from configured origins are allowed.

    Expected behavior:
    - Origin in CORS_ORIGINS list should receive Access-Control-Allow-Origin header
    - Response should include the requested origin (not wildcard)
    """
    configured_origin = "https://app.example.com"

    response = client.options(
        "/",
        headers={
            "Origin": configured_origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    # Should return 200 OK for preflight
    assert response.status_code == 200

    # Should include the specific origin (not "*")
    assert response.headers.get("access-control-allow-origin") == configured_origin

    # Should allow credentials
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_blocks_unknown_origin(client: TestClient) -> None:
    """
    Test that requests from unknown origins are blocked.

    Security requirement: Only whitelisted origins should be allowed.
    FastAPI's CORSMiddleware returns 400 Bad Request for preflight from unknown origins.
    """
    unknown_origin = "https://malicious-site.com"

    response = client.options(
        "/",
        headers={
            "Origin": unknown_origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    # FastAPI CORSMiddleware blocks unknown origins with 400
    assert response.status_code == 400

    # Should NOT include Access-Control-Allow-Origin for unknown origin
    allow_origin = response.headers.get("access-control-allow-origin")
    if allow_origin:
        # If header exists, it must not be the unknown origin or wildcard
        assert allow_origin != unknown_origin
        assert allow_origin != "*"


def test_cors_allows_credentials(client: TestClient) -> None:
    """
    Test that CORS allows credentials (cookies, authorization headers).

    Required for JWT authentication with cookies.
    """
    configured_origin = "https://app.example.com"

    response = client.options(
        "/",
        headers={
            "Origin": configured_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_allows_multiple_configured_origins(client: TestClient) -> None:
    """
    Test that multiple origins can be configured (dev, staging, production).

    Each environment should support its own origin.
    """
    test_origins = [
        "http://localhost:3000",  # Development
        "https://staging.ans.postxsociety.cloud",  # Staging
        "https://ans.postxsociety.cloud",  # Production
    ]

    for origin in test_origins:
        response = client.options(
            "/",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )

        # Each configured origin should be allowed
        assert (
            response.headers.get("access-control-allow-origin") == origin
        ), f"Origin {origin} should be allowed"


def test_cors_preflight_allows_common_methods(client: TestClient) -> None:
    """
    Test that CORS preflight allows common HTTP methods.

    Required methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
    """
    configured_origin = "https://app.example.com"

    response = client.options(
        "/",
        headers={
            "Origin": configured_origin,
            "Access-Control-Request-Method": "DELETE",
        },
    )

    assert response.status_code == 200

    allowed_methods = response.headers.get("access-control-allow-methods", "")

    # Should allow common REST methods
    for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]:
        assert method in allowed_methods, f"Method {method} should be allowed"


def test_cors_preflight_allows_common_headers(client: TestClient) -> None:
    """
    Test that CORS preflight allows common headers.

    Required headers: Authorization, Content-Type, etc.
    """
    configured_origin = "https://app.example.com"

    response = client.options(
        "/",
        headers={
            "Origin": configured_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200

    # Should allow the requested headers
    allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in allowed_headers
    assert "content-type" in allowed_headers


@pytest.mark.asyncio
async def test_cors_actual_request_includes_origin(client: TestClient) -> None:
    """
    Test that actual requests (not just preflight) include CORS headers.

    Not just OPTIONS requests, but also GET, POST, etc.
    """
    configured_origin = "https://app.example.com"

    response = client.get(
        "/",
        headers={"Origin": configured_origin},
    )

    # Actual request should also include CORS headers
    assert response.headers.get("access-control-allow-origin") == configured_origin
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_no_wildcard_when_credentials_enabled(client: TestClient) -> None:
    """
    Test security requirement: Cannot use wildcard "*" with credentials.

    Per CORS spec: If allow_credentials=True, allow_origins cannot be "*"
    This is a security requirement to prevent CSRF attacks.
    """
    response = client.options(
        "/",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    allow_origin = response.headers.get("access-control-allow-origin")
    allow_credentials = response.headers.get("access-control-allow-credentials")

    # If credentials are allowed, origin must NOT be wildcard
    if allow_credentials == "true":
        assert (
            allow_origin != "*"
        ), "Security violation: Cannot use wildcard origin with credentials enabled"
