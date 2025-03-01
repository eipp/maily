"""Integration tests for campaign workflow with main_fixed.py."""

import pytest
from fastapi.testclient import TestClient

from main_fixed import app


def test_campaign_workflow(test_client, test_api_key):
    """Test the simplified campaign workflow."""
    # 1. Create campaign
    campaign_data = {
        "task": "Create a promotional email",
        "model_name": "gpt-4",
        "audience": {
            "segments": ["customers"],
            "exclusions": []
        }
    }
    response = test_client.post(
        "/create_campaign",
        headers={"X-API-Key": test_api_key},
        json=campaign_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "draft"
    assert "campaign_id" in data

    # 2. Configure model
    model_config = {
        "model_name": "gpt-4",
        "api_key": "sk-test-key",
        "temperature": 0.8,
        "max_tokens": 2000
    }

    response = test_client.post(
        "/configure_model",
        headers={"X-API-Key": test_api_key},
        json=model_config
    )
    assert response.status_code == 200
    config_data = response.json()
    assert "config_id" in config_data
    assert config_data["model_name"] == model_config["model_name"]
