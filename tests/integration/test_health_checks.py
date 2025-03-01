import pytest
from fastapi.testclient import TestClient

from ...main import app


def test_health_check(test_client: TestClient):
    """Test basic health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_readiness_check(test_client: TestClient, test_db, test_redis):
    """Test readiness check endpoint."""
    response = test_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "database" in data["checks"]
    assert "redis" in data["checks"]

    # Verify database check
    assert data["checks"]["database"]["status"] in ["healthy", "unhealthy"]

    # Verify Redis check
    assert data["checks"]["redis"]["status"] in ["healthy", "unhealthy"]


def test_liveness_check(test_client: TestClient):
    """Test liveness check endpoint."""
    response = test_client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "uptime" in data
    assert isinstance(data["uptime"], float)


def test_metrics_endpoint(test_client: TestClient, test_api_key: str):
    """Test metrics endpoint."""
    response = test_client.get("/metrics", headers={"X-API-Key": test_api_key})
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "model_inference_duration_seconds" in response.text
    assert "cache_hits_total" in response.text
