import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from models.campaign import Campaign, CampaignInput

client = TestClient(app)

@pytest.fixture
def mock_campaign_data():
    return {
        "name": "Test Campaign",
        "target_audience": "Software developers",
        "product_description": "AI-powered email marketing tool",
        "tone": "Professional",
        "key_points": ["Easy to use", "AI-powered", "Affordable"]
    }

@pytest.fixture
def mock_ai_response():
    return {
        "status": "success",
        "result": {
            "subject": "Revolutionize Your Email Marketing with AI",
            "body": "Dear {name},\n\nDiscover how our AI-powered tool can transform your email marketing...",
            "preview_text": "Boost your email engagement with AI"
        },
        "metadata": {
            "model": "gpt-4",
            "timestamp": "2024-02-24 12:00:00"
        }
    }

def test_create_campaign(mock_campaign_data, mock_ai_response):
    # Mock the AI service call
    with patch('services.ai.generate_campaign') as mock_generate:
        mock_generate.return_value = mock_ai_response

        response = client.post(
            "/api/campaigns",
            json=mock_campaign_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == mock_campaign_data["name"]
        assert data["subject"] == mock_ai_response["result"]["subject"]
        assert data["body"] == mock_ai_response["result"]["body"]
        assert "id" in data

def test_create_campaign_validation():
    # Test with missing required fields
    response = client.post(
        "/api/campaigns",
        json={"name": "Test"}
    )
    assert response.status_code == 422

def test_create_campaign_ai_error():
    with patch('services.ai.generate_campaign') as mock_generate:
        mock_generate.side_effect = Exception("AI service error")

        response = client.post(
            "/api/campaigns",
            json=mock_campaign_data
        )

        assert response.status_code == 500
        assert "error" in response.json()

def test_get_campaign():
    # Mock database call
    mock_campaign = Campaign(
        id=1,
        name="Test Campaign",
        subject="Test Subject",
        body="Test Body",
        status="draft"
    )

    with patch('repositories.campaign.get_campaign_by_id') as mock_get:
        mock_get.return_value = mock_campaign

        response = client.get("/api/campaigns/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_campaign.id
        assert data["name"] == mock_campaign.name

def test_get_nonexistent_campaign():
    with patch('repositories.campaign.get_campaign_by_id') as mock_get:
        mock_get.return_value = None

        response = client.get("/api/campaigns/999")

        assert response.status_code == 404
