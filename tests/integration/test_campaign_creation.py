import pytest
from fastapi.testclient import TestClient

from ...main import app


def test_create_campaign_success(test_client: TestClient, test_api_key: str):
    """Test successful campaign creation."""
    response = test_client.post(
        "/api/v1/create_campaign",
        headers={"X-API-Key": test_api_key},
        json={
            "task": "Create an email campaign about product launch",
            "model_name": "mock",
            "cache_ttl": 3600,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "result" in data
    assert "metadata" in data


def test_create_campaign_invalid_model(test_client: TestClient, test_api_key: str):
    """Test campaign creation with invalid model."""
    response = test_client.post(
        "/api/v1/create_campaign",
        headers={"X-API-Key": test_api_key},
        json={
            "task": "Create an email campaign",
            "model_name": "invalid_model",
            "cache_ttl": 3600,
        },
    )
    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]


def test_create_campaign_unauthorized(test_client: TestClient):
    """Test campaign creation without API key."""
    response = test_client.post(
        "/api/v1/create_campaign",
        json={"task": "Create an email campaign", "model_name": "mock"},
    )
    assert response.status_code == 401
