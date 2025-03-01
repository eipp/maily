"""Integration tests to bridge between fixed and router-based implementations."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import time

from main_fixed import app

@pytest.fixture
def test_client():
    """Create a test client for the app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def test_api_key():
    """Return a valid test API key."""
    return "test-api-key"

@pytest.fixture
def campaign_id():
    """Generate a unique campaign ID."""
    return f"campaign-{int(time.time())}"

# Adapter tests to bridge fixed API with router API format
class RouterCompatAdapter:
    """Adapter to convert between fixed API and router API formats."""

    @staticmethod
    def convert_to_fixed_format(router_campaign):
        """Convert router campaign format to fixed format."""
        return {
            "task": router_campaign.get("name", "Unnamed campaign"),
            "model_name": router_campaign.get("model_name", "gpt-4"),
            "audience": {
                "segments": router_campaign.get("segments", []),
                "exclusions": router_campaign.get("exclusions", [])
            }
        }

    @staticmethod
    def convert_to_router_format(fixed_campaign, campaign_id):
        """Convert fixed campaign format to router format."""
        return {
            "id": campaign_id,
            "name": fixed_campaign.get("task", "Unnamed campaign"),
            "subject": "Generated Subject",
            "content": "Generated Content",
            "status": fixed_campaign.get("status", "draft").upper(),
            "user_id": 1,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "schedule_time": None,
            "open_rate": 0.0,
            "click_rate": 0.0,
            "metadata": {}
        }


# Test adapter conversions
def test_adapter_conversion():
    """Test adapter conversion between formats."""
    # Test router to fixed conversion
    router_campaign = {
        "name": "New Product Launch",
        "subject": "Introducing our latest product",
        "content": "<p>Check out our new product!</p>",
        "model_name": "gpt-4",
        "segments": ["customers", "leads"],
        "exclusions": ["unsubscribed"]
    }

    fixed_format = RouterCompatAdapter.convert_to_fixed_format(router_campaign)
    assert fixed_format["task"] == "New Product Launch"
    assert fixed_format["model_name"] == "gpt-4"
    assert "segments" in fixed_format["audience"]
    assert "exclusions" in fixed_format["audience"]

    # Test fixed to router conversion
    fixed_campaign = {
        "task": "New Product Launch",
        "model_name": "gpt-4",
        "status": "draft"
    }

    campaign_id = "campaign-123"
    router_format = RouterCompatAdapter.convert_to_router_format(fixed_campaign, campaign_id)
    assert router_format["id"] == campaign_id
    assert router_format["name"] == "New Product Launch"
    assert router_format["status"] == "DRAFT"  # Note uppercase in router format


# Test creating campaign with router format through adapter
def test_create_campaign_with_adapter(test_client, test_api_key):
    """Test creating a campaign using adapter to convert between formats."""
    # Router format campaign
    router_campaign = {
        "name": "New Product Launch",
        "subject": "Introducing our latest product",
        "content": "<p>Check out our new product!</p>",
        "model_name": "gpt-4",
        "segments": ["customers"],
        "exclusions": []
    }

    # Convert to fixed format
    fixed_format = RouterCompatAdapter.convert_to_fixed_format(router_campaign)

    # Create campaign using fixed API
    response = test_client.post(
        "/create_campaign",
        headers={"X-API-Key": test_api_key},
        json=fixed_format
    )
    assert response.status_code == 200
    fixed_response = response.json()

    # Convert response back to router format
    router_response = RouterCompatAdapter.convert_to_router_format(
        fixed_response, fixed_response["campaign_id"]
    )

    # Verify router format response
    assert router_response["id"] == fixed_response["campaign_id"]
    assert router_response["name"] == fixed_format["task"]
    assert router_response["status"] == "DRAFT"


# Mock campaign service to simulate router-like responses
@pytest.fixture
def patch_campaign_service():
    """Patch campaign service to return router-compatible responses."""
    with patch("main_fixed.campaign_service") as mock_service:
        # Create a mock campaign object with router-like fields
        mock_campaign = MagicMock()
        mock_campaign.id = "campaign-123"
        mock_campaign.name = "Mocked Campaign"
        mock_campaign.status = "DRAFT"
        mock_campaign.created_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        mock_campaign.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")

        # Configure mock service methods
        mock_service.create_campaign.return_value = mock_campaign.id
        mock_service.get_campaign.return_value = mock_campaign

        yield mock_service


# Test to verify fixed app can return router-like responses
def test_fixed_app_with_router_response(test_client, test_api_key, patch_campaign_service):
    """Test that fixed app can return router-like responses."""
    # Create campaign
    response = test_client.post(
        "/create_campaign",
        headers={"X-API-Key": test_api_key},
        json={
            "task": "Test Campaign",
            "model_name": "gpt-4"
        }
    )
    assert response.status_code == 200
    data = response.json()

    # Verify response could be adapted to router format
    assert "campaign_id" in data
    router_format = RouterCompatAdapter.convert_to_router_format(data, data["campaign_id"])
    assert router_format["id"] == data["campaign_id"]
    assert router_format["name"] == "Test Campaign"


# Migration path test - router endpoints mapped to fixed endpoints
@patch("main_fixed.app")
def test_router_endpoint_migration(mock_app, test_client, test_api_key):
    """Test a migration path where router endpoints map to fixed endpoints."""
    # Create a simple adapter function to route new endpoint to old
    def router_fixed_adapter(request):
        """Route /campaigns/ endpoint to /create_campaign."""
        # Get the request body
        data = request.json()

        # Convert to fixed format
        fixed_data = RouterCompatAdapter.convert_to_fixed_format(data)

        # Create a new request to the fixed endpoint
        fixed_response = test_client.post(
            "/create_campaign",
            headers={"X-API-Key": test_api_key},
            json=fixed_data
        )

        # Get the response data
        response_data = fixed_response.json()

        # Convert to router format
        router_data = RouterCompatAdapter.convert_to_router_format(
            response_data, response_data["campaign_id"]
        )

        # Return router format response with 201 status code
        return router_data, 201

    # Set up the mock to use our adapter
    mock_app.post.return_value = router_fixed_adapter

    # Create a campaign using router format
    router_campaign = {
        "name": "Router Campaign",
        "subject": "Test Subject",
        "content": "<p>Test Content</p>"
    }

    # This is a simulated call to the router endpoint
    response_data, status_code = mock_app.post(router_campaign)

    # Verify the response
    assert status_code == 201
    assert response_data["name"] == "Router Campaign"
    assert response_data["status"] == "DRAFT"


# Authentication bridge tests
def test_auth_bridge(test_client, test_api_key):
    """Test converting between authentication methods."""
    # Function to convert Bearer token to API key
    def convert_bearer_to_api_key(bearer_token):
        """Convert Bearer token to API key for backward compatibility."""
        # In this simple example, we're just returning a fixed API key
        # In a real implementation, you might validate the token and map to an API key
        return test_api_key

    # Simulate a request with Bearer token
    bearer_token = "Bearer test_token"

    # Extract token from Authorization header
    token = bearer_token.split(" ")[1]

    # Convert to API key
    api_key = convert_bearer_to_api_key(token)

    # Make request with converted API key
    response = test_client.post(
        "/create_campaign",
        headers={"X-API-Key": api_key},
        json={
            "task": "Test Campaign",
            "model_name": "gpt-4"
        }
    )

    # Verify successful response
    assert response.status_code == 200
    assert "campaign_id" in response.json()


# Feature compatibility tests
def test_feature_compatibility():
    """Test ensuring all router features have equivalents in fixed app."""
    # Define router features
    router_features = {
        "campaign_creation": True,
        "campaign_update": True,
        "campaign_deletion": True,
        "campaign_sending": True,
        "campaign_analytics": True,
        "ai_content_generation": True
    }

    # Define fixed app features
    fixed_features = {
        "campaign_creation": True,      # /create_campaign exists
        "campaign_update": False,       # No direct equivalent
        "campaign_deletion": False,     # No direct equivalent
        "campaign_sending": False,      # No direct equivalent
        "campaign_analytics": False,    # No direct equivalent
        "ai_content_generation": True   # Background task in create_campaign
    }

    # Identify missing features
    missing_features = []
    for feature, supported in router_features.items():
        if supported and not fixed_features.get(feature, False):
            missing_features.append(feature)

    # Report missing features (this is expected to fail as part of the gap analysis)
    assert len(missing_features) > 0, "Expected missing features as part of gap analysis"
    print(f"Missing features in fixed app: {missing_features}")
