"""Test the health endpoints of the API."""

import pytest
from fastapi.testclient import TestClient


def test_health_check(test_client):
    """Test the basic health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
    assert "ai_service" in data["components"]
    assert "uptime" in data


def test_readiness_check(test_client):
    """Test the readiness check endpoint."""
    response = test_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]
    assert data["checks"]["database"]["status"] in ["healthy", "unhealthy"]
    assert data["checks"]["redis"]["status"] in ["healthy", "unhealthy"]


def test_liveness_check(test_client):
    """Test the liveness check endpoint."""
    response = test_client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "uptime" in data
    assert isinstance(data["uptime"], (int, float))
    assert "timestamp" in data


def test_metrics_endpoint(test_client, test_api_key):
    """Test the metrics endpoint."""
    response = test_client.get("/metrics", headers={"X-API-Key": test_api_key})
    assert response.status_code == 200
    data = response.json()
    assert "http_requests_total" in data
    assert "model_inference_duration_seconds" in data
    assert "cache_hits_total" in data
    assert "timestamp" in data


def test_invalid_api_key(test_client):
    """Test that an invalid API key returns a 401 response."""
    response = test_client.get("/metrics", headers={"X-API-Key": "invalid-key"})
    assert response.status_code == 401
    assert response.json()["error"] == "http_error"
