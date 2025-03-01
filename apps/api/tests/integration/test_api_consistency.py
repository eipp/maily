"""Integration tests to highlight API consistency issues between implementations."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import both app versions for comparison
from main_fixed import app as fixed_app
from main import app as router_app

@pytest.fixture
def fixed_client():
    """Create a test client for the fixed app."""
    with TestClient(fixed_app) as client:
        yield client

@pytest.fixture
def router_client():
    """Create a test client for the router-based app."""
    with TestClient(router_app) as client:
        yield client

@pytest.fixture
def api_key_auth():
    """Return API key authentication headers."""
    return {"X-API-Key": "test-api-key"}

@pytest.fixture
def bearer_auth():
    """Return Bearer token authentication headers."""
    return {"Authorization": "Bearer test_token"}


# Authentication Consistency Tests
def test_auth_method_differences(fixed_client, router_client, api_key_auth, bearer_auth):
    """Test differences in authentication methods between implementations."""
    # The fixed app uses API key
    fixed_response = fixed_client.get("/metrics", headers=api_key_auth)
    assert fixed_response.status_code == 200

    # The router app uses Bearer token
    router_response = router_client.get("/campaigns", headers=bearer_auth)
    assert router_response.status_code == 200

    # API key fails on router app
    router_response_with_api_key = router_client.get("/campaigns", headers=api_key_auth)
    assert router_response_with_api_key.status_code in [401, 403]

    # Bearer token fails on fixed app
    fixed_response_with_bearer = fixed_client.get("/metrics", headers=bearer_auth)
    assert fixed_response_with_bearer.status_code == 401


# Endpoint Structure Consistency Tests
def test_campaign_endpoint_differences(fixed_client, router_client, api_key_auth, bearer_auth):
    """Test differences in campaign endpoint structure."""
    # In fixed app: /create_campaign
    campaign_data_fixed = {
        "task": "Create a promotional email",
        "model_name": "gpt-4",
        "audience": {
            "segments": ["customers"],
            "exclusions": []
        }
    }

    fixed_response = fixed_client.post(
        "/create_campaign",
        headers=api_key_auth,
        json=campaign_data_fixed
    )
    assert fixed_response.status_code == 200

    # In router app: /campaigns/
    campaign_data_router = {
        "name": "Test Campaign",
        "subject": "Test Subject",
        "content": "Hello {{name}}, this is a test email.",
        "schedule_time": None
    }

    router_response = router_client.post(
        "/campaigns/",
        headers=bearer_auth,
        json=campaign_data_router
    )
    assert router_response.status_code == 201


# Data Model Consistency Tests
def test_campaign_data_model_differences(fixed_client, router_client, api_key_auth, bearer_auth):
    """Test differences in campaign data models."""
    # Fixed app campaign model
    campaign_data_fixed = {
        "task": "Create a promotional email",
        "model_name": "gpt-4",
    }

    fixed_response = fixed_client.post(
        "/create_campaign",
        headers=api_key_auth,
        json=campaign_data_fixed
    )
    assert fixed_response.status_code == 200
    fixed_result = fixed_response.json()

    # Verify fixed app model fields
    assert "campaign_id" in fixed_result
    assert "status" in fixed_result
    assert fixed_result["status"] == "draft"

    # Router app campaign model
    campaign_data_router = {
        "name": "Test Campaign",
        "subject": "Test Subject",
        "content": "Hello {{name}}, this is a test email."
    }

    router_response = router_client.post(
        "/campaigns/",
        headers=bearer_auth,
        json=campaign_data_router
    )
    assert router_response.status_code == 201
    router_result = router_response.json()

    # Verify router app model fields
    assert "id" in router_result  # Uses 'id' not 'campaign_id'
    assert "name" in router_result  # Has additional fields
    assert "subject" in router_result
    assert "content" in router_result


# Response Consistency Tests
def test_response_structure_differences(fixed_client, router_client, api_key_auth, bearer_auth):
    """Test differences in response structures."""
    # Fixed app response
    campaign_data_fixed = {
        "task": "Create a promotional email",
        "model_name": "gpt-4"
    }

    fixed_response = fixed_client.post(
        "/create_campaign",
        headers=api_key_auth,
        json=campaign_data_fixed
    )
    assert fixed_response.status_code == 200
    fixed_result = fixed_response.json()

    # Router app response
    campaign_data_router = {
        "name": "Test Campaign",
        "subject": "Test Subject",
        "content": "Hello {{name}}, this is a test email."
    }

    router_response = router_client.post(
        "/campaigns/",
        headers=bearer_auth,
        json=campaign_data_router
    )
    assert router_response.status_code == 201
    router_result = router_response.json()

    # Compare response structures
    fixed_keys = set(fixed_result.keys())
    router_keys = set(router_result.keys())

    # Highlight differences
    only_in_fixed = fixed_keys - router_keys
    only_in_router = router_keys - fixed_keys

    assert len(only_in_fixed) > 0, "Expected differences in fixed app response"
    assert len(only_in_router) > 0, "Expected differences in router app response"

    # Preview URL is in fixed but not router
    assert "preview_url" in only_in_fixed

    # Created_at is in router but not fixed
    assert "created_at" in only_in_router


# Feature Support Differences
def test_feature_support_differences(fixed_client, router_client, api_key_auth, bearer_auth):
    """Test differences in supported features."""
    # Fixed app has no analytics endpoint
    fixed_analytics_response = fixed_client.get(
        "/campaigns/1/analytics",
        headers=api_key_auth
    )
    assert fixed_analytics_response.status_code == 404

    # Router app does support analytics
    router_analytics_response = router_client.get(
        "/campaigns/1/analytics",
        headers=bearer_auth
    )
    assert router_analytics_response.status_code in [200, 404]  # 404 if campaign doesn't exist

    # Router supports advanced generation
    router_generate_response = router_client.post(
        "/campaigns/generate",
        headers=bearer_auth,
        json={
            "objective": "Product announcement",
            "audience": "Existing customers",
            "brand_voice": "professional",
            "key_points": ["Feature A", "Feature B"]
        }
    )
    assert router_generate_response.status_code in [200, 500]  # 500 if service unavailable
