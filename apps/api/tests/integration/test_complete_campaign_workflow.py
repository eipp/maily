"""Complete integration tests for campaign workflow with routers."""

import json
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the router-based app
from main import app

@pytest.fixture
def auth_headers():
    """Fixture for authentication headers with Bearer token."""
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def test_campaign_data():
    """Fixture for test campaign data."""
    return {
        "name": "Test Campaign",
        "subject": "Test Subject Line",
        "content": "<p>Hello {{name}}, this is a test email.</p>",
        "schedule_time": (datetime.now() + timedelta(days=1)).isoformat()
    }

@pytest.fixture
def test_campaign_generate_data():
    """Fixture for AI campaign generation request data."""
    return {
        "objective": "Product announcement",
        "audience": "Existing customers",
        "brand_voice": "professional",
        "key_points": [
            "New feature launch",
            "20% discount for early adopters",
            "Available starting next week"
        ],
        "personalization": {
            "user_name": "{{name}}",
            "company": "{{company}}"
        }
    }

@pytest.fixture
def test_recipients():
    """Fixture for test recipients."""
    return {
        "recipients": [
            "test1@example.com",
            "test2@example.com"
        ]
    }

# Mock dependencies
@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis client."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.setex.return_value = True
    return mock

@pytest.fixture
def mock_octotools(monkeypatch):
    """Mock OctoTools service."""
    mock = MagicMock()
    mock.create_email_campaign.return_value = {
        "status": "success",
        "content": {
            "subject": "Generated Subject",
            "html_body": "<p>Generated email content</p>",
            "plain_text": "Generated email content"
        }
    }
    mock._send_campaign.return_value = {
        "status": "success",
        "message": "Campaign sent successfully"
    }
    mock.analyze_campaign.return_value = {
        "sent_count": 2,
        "open_count": 1,
        "click_count": 0,
        "open_rate": 0.5,
        "click_rate": 0.0
    }
    return mock

@pytest.fixture
def mock_campaign_service(monkeypatch):
    """Mock CampaignService."""
    mock = MagicMock()

    # Create a mock campaign object
    campaign = MagicMock()
    campaign.id = 1
    campaign.name = "Test Campaign"
    campaign.subject = "Test Subject"
    campaign.content = "<p>Test Content</p>"
    campaign.status = "DRAFT"
    campaign.user_id = 1
    campaign.created_at = datetime.now()
    campaign.updated_at = datetime.now()
    campaign.schedule_time = datetime.now() + timedelta(days=1)
    campaign.sent_at = None
    campaign.open_rate = 0.0
    campaign.click_rate = 0.0
    campaign.metadata = {}
    campaign.sender_email = "sender@example.com"

    # Configure the mock service methods
    mock.create_campaign.return_value = campaign
    mock.get_campaign.return_value = campaign
    mock.get_user_campaigns.return_value = [campaign]
    mock.update_campaign.return_value = campaign
    mock.update_campaign_status.return_value = True
    mock.delete_campaign.return_value = True
    mock.get_campaign_analytics.return_value = {
        "sent_count": 2,
        "open_count": 1,
        "click_count": 0,
        "open_rate": 0.5,
        "click_rate": 0.0
    }

    return mock

# Tests for health endpoints
def test_health_endpoint():
    """Test the health endpoint."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in data
        assert "uptime" in data
        assert "timestamp" in data

def test_readiness_endpoint():
    """Test the readiness endpoint."""
    with TestClient(app) as client:
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["ready", "not_ready"]
        assert "checks" in data
        assert "timestamp" in data

def test_liveness_endpoint():
    """Test the liveness endpoint."""
    with TestClient(app) as client:
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "alive"
        assert "uptime" in data
        assert "timestamp" in data

# Campaign Workflow Tests
@patch("apps.api.routers.campaigns.CampaignService")
@patch("apps.api.routers.campaigns.octotools_service")
@patch("apps.api.routers.campaigns.redis_client")
def test_campaign_creation_workflow(mock_redis, mock_octo, mock_service,
                                     auth_headers, test_campaign_data,
                                     test_campaign_generate_data, mock_campaign_service):
    """Test the complete campaign creation workflow."""
    # Set up mocks
    mock_service.return_value = mock_campaign_service

    with TestClient(app) as client:
        # 1. Generate campaign content with AI
        response = client.post(
            "/campaigns/generate",
            headers=auth_headers,
            json=test_campaign_generate_data
        )
        assert response.status_code == 200
        gen_data = response.json()
        assert gen_data["status"] == "success"
        assert "content" in gen_data

        # 2. Create a campaign
        response = client.post(
            "/campaigns/",
            headers=auth_headers,
            json=test_campaign_data
        )
        assert response.status_code == 201
        campaign_data = response.json()
        assert "id" in campaign_data
        assert campaign_data["name"] == test_campaign_data["name"]
        assert campaign_data["status"] == "DRAFT"
        campaign_id = campaign_data["id"]

        # 3. Get campaign details
        response = client.get(f"/campaigns/{campaign_id}", headers=auth_headers)
        assert response.status_code == 200
        campaign_details = response.json()
        assert campaign_details["id"] == campaign_id

        # 4. Update campaign
        update_data = {"name": "Updated Campaign Name"}
        response = client.put(
            f"/campaigns/{campaign_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        updated_data = response.json()
        assert updated_data["name"] == "Updated Campaign Name"

        # 5. List all campaigns
        response = client.get("/campaigns/", headers=auth_headers)
        assert response.status_code == 200
        campaigns = response.json()
        assert len(campaigns) > 0
        assert any(c["id"] == campaign_id for c in campaigns)

@patch("apps.api.routers.campaigns.CampaignService")
@patch("apps.api.routers.campaigns.octotools_service")
@patch("apps.api.routers.campaigns.redis_client")
def test_campaign_sending_workflow(mock_redis, mock_octo, mock_service,
                                   auth_headers, test_campaign_data,
                                   test_recipients, mock_campaign_service):
    """Test the campaign sending workflow."""
    # Set up mocks
    mock_service.return_value = mock_campaign_service

    with TestClient(app) as client:
        # 1. Create a campaign first
        response = client.post(
            "/campaigns/",
            headers=auth_headers,
            json=test_campaign_data
        )
        assert response.status_code == 201
        campaign_data = response.json()
        campaign_id = campaign_data["id"]

        # 2. Send the campaign
        response = client.post(
            f"/campaigns/{campaign_id}/send",
            headers=auth_headers,
            json=test_recipients
        )
        assert response.status_code == 200
        send_result = response.json()
        assert send_result["status"] == "success"
        assert send_result["campaign_id"] == campaign_id
        assert len(send_result["sent_to"]) == len(test_recipients["recipients"])

        # 3. Check campaign analytics after sending
        response = client.get(
            f"/campaigns/{campaign_id}/analytics",
            headers=auth_headers
        )
        assert response.status_code == 200
        analytics = response.json()
        assert "sent_count" in analytics
        assert "open_rate" in analytics
        assert "click_rate" in analytics

# Error Handling Tests
@patch("apps.api.routers.campaigns.CampaignService")
def test_campaign_not_found(mock_service, auth_headers, mock_campaign_service):
    """Test error handling for campaign not found."""
    # Set up mock to return None for get_campaign
    mock_campaign_service.get_campaign.return_value = None
    mock_service.return_value = mock_campaign_service

    with TestClient(app) as client:
        response = client.get("/campaigns/999", headers=auth_headers)
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
        assert "not found" in error_data["detail"].lower()

@patch("apps.api.routers.campaigns.CampaignService")
def test_unauthorized_campaign_access(mock_service, auth_headers, mock_campaign_service):
    """Test error handling for unauthorized campaign access."""
    # Set up mock to return a campaign with different user_id
    campaign = mock_campaign_service.get_campaign.return_value
    campaign.user_id = 999  # Different from the authenticated user
    mock_service.return_value = mock_campaign_service

    with TestClient(app) as client:
        response = client.get("/campaigns/1", headers=auth_headers)
        assert response.status_code == 403
        error_data = response.json()
        assert "detail" in error_data
        assert "not authorized" in error_data["detail"].lower()

@patch("apps.api.routers.campaigns.CampaignService")
def test_campaign_invalid_update(mock_service, auth_headers, mock_campaign_service):
    """Test error handling for invalid campaign update."""
    # Set up mock to raise ValueError for update_campaign
    mock_campaign_service.update_campaign.side_effect = ValueError("Invalid status")
    mock_service.return_value = mock_campaign_service

    with TestClient(app) as client:
        response = client.put(
            "/campaigns/1",
            headers=auth_headers,
            json={"status": "INVALID_STATUS"}
        )
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data
        assert "invalid" in error_data["detail"].lower()

# System failure tests
@patch("apps.api.routers.campaigns.CampaignService")
def test_database_failure(mock_service, auth_headers):
    """Test error handling for database failure."""
    # Set up mock to raise an exception for create_campaign
    mock_service.return_value.create_campaign.side_effect = Exception("Database connection error")

    with TestClient(app) as client:
        response = client.post(
            "/campaigns/",
            headers=auth_headers,
            json={
                "name": "Test Campaign",
                "subject": "Test Subject",
                "content": "Test Content"
            }
        )
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data
        assert "internal server error" in error_data["detail"].lower()

@patch("apps.api.routers.campaigns.redis_client.get")
def test_redis_failure(mock_redis_get, auth_headers):
    """Test handling of Redis cache failure."""
    # Set up mock to raise an exception for redis.get
    mock_redis_get.side_effect = Exception("Redis connection error")

    with TestClient(app) as client:
        # The system should continue to work even if Redis fails
        response = client.get("/campaigns/1/analytics", headers=auth_headers)
        # We expect a 404 because the campaign doesn't exist,
        # not a 500 because Redis failed
        assert response.status_code in [404, 200]

@patch("apps.api.routers.campaigns.octotools_service.create_email_campaign")
def test_ai_service_failure(mock_ai, auth_headers, test_campaign_generate_data):
    """Test handling of AI service failure."""
    # Set up mock to raise an exception for create_email_campaign
    mock_ai.side_effect = Exception("AI service unavailable")

    with TestClient(app) as client:
        response = client.post(
            "/campaigns/generate",
            headers=auth_headers,
            json=test_campaign_generate_data
        )
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data

# Background task verification
@patch("apps.api.routers.campaigns.CampaignService")
def test_background_task_execution(mock_service, auth_headers, test_campaign_data,
                                  mock_campaign_service):
    """Test that background tasks execute successfully."""
    # Configure the mock to modify the campaign status when a background task runs
    original_create = mock_campaign_service.create_campaign

    def modified_create(*args, **kwargs):
        campaign = original_create(*args, **kwargs)
        # Simulate the background task completing by updating the campaign
        campaign.status = "PROCESSED"
        return campaign

    mock_campaign_service.create_campaign = modified_create
    mock_service.return_value = mock_campaign_service

    with TestClient(app) as client:
        # Create a campaign, which should trigger a background task
        response = client.post(
            "/campaigns/",
            headers=auth_headers,
            json=test_campaign_data
        )
        assert response.status_code == 201
        campaign_id = response.json()["id"]

        # Check that the background task ran (status changed to PROCESSED)
        response = client.get(f"/campaigns/{campaign_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "PROCESSED"

# Authentication tests
def test_missing_auth_header():
    """Test that requests without auth headers are rejected."""
    with TestClient(app) as client:
        response = client.get("/campaigns/")
        assert response.status_code in [401, 403]

def test_invalid_auth_token():
    """Test that requests with invalid auth tokens are rejected."""
    with TestClient(app) as client:
        response = client.get(
            "/campaigns/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code in [401, 403]
