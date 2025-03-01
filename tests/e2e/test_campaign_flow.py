import time

import pytest
from fastapi.testclient import TestClient

from ...main import app


def test_complete_campaign_flow(
    test_client: TestClient, test_api_key: str, test_db, test_redis
):
    """Test complete campaign flow from creation to result retrieval."""

    # Configure model
    model_config = {"model_name": "mock", "api_key": "test-api-key"}
    response = test_client.post(
        "/api/v1/configure_model",
        headers={"X-API-Key": test_api_key},
        json=model_config,
    )
    assert response.status_code == 200

    # Create campaign
    campaign_request = {
        "task": "Create an email campaign about new feature launch",
        "model_name": "mock",
        "cache_ttl": 3600,
    }
    response = test_client.post(
        "/api/v1/create_campaign",
        headers={"X-API-Key": test_api_key},
        json=campaign_request,
    )
    assert response.status_code == 200
    campaign_data = response.json()
    assert campaign_data["status"] == "success"

    # Verify campaign is cached
    if test_redis:
        cache_key = f"campaign:{campaign_request['task']}"
        cached_result = test_redis.get(cache_key)
        assert cached_result is not None

    # Verify campaign is in database
    cur = test_db.cursor()
    cur.execute(
        "SELECT status FROM campaigns WHERE task = %s", (campaign_request["task"],)
    )
    result = cur.fetchone()
    assert result is not None
    assert result[0] == "completed"
    cur.close()


def test_campaign_error_recovery(test_client: TestClient, test_api_key: str):
    """Test campaign error handling and recovery."""

    # Try with invalid model
    response = test_client.post(
        "/api/v1/create_campaign",
        headers={"X-API-Key": test_api_key},
        json={"task": "Create an email campaign", "model_name": "invalid_model"},
    )
    assert response.status_code == 400

    # Retry with valid model
    response = test_client.post(
        "/api/v1/create_campaign",
        headers={"X-API-Key": test_api_key},
        json={"task": "Create an email campaign", "model_name": "mock"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
