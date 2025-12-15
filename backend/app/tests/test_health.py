"""
Tests for health check endpoint

Following TDD: These tests are written FIRST, before implementation
"""
import pytest
from fastapi.testclient import TestClient


def test_health_check_returns_200(client: TestClient) -> None:
    """Test that health endpoint returns 200 OK"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_check_returns_json(client: TestClient) -> None:
    """Test that health endpoint returns JSON"""
    response = client.get("/api/v1/health")
    assert "application/json" in response.headers["content-type"]


def test_health_check_contains_status(client: TestClient) -> None:
    """Test that health response contains status field"""
    response = client.get("/api/v1/health")
    data = response.json()

    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]


def test_health_check_contains_service_name(client: TestClient) -> None:
    """Test that health response includes service name"""
    response = client.get("/api/v1/health")
    data = response.json()

    assert "service" in data
    assert data["service"] == "ans-backend"


def test_health_check_contains_version(client: TestClient) -> None:
    """Test that health response includes version"""
    response = client.get("/api/v1/health")
    data = response.json()

    assert "version" in data
    assert isinstance(data["version"], str)
