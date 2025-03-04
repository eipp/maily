"""
Tests for predictive analytics integration.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import json
import time

from ..main import app
from ..services.predictive_analytics_service import PredictiveAnalyticsService


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_redis_cache():
    """Mock Redis cache."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def mock_analytics_service(mock_redis_cache):
    """Mock predictive analytics service."""
    service = PredictiveAnalyticsService(mock_redis_cache)
    
    # Mock the get_campaign_recommendations method
    async def mock_get_recommendations(*args, **kwargs):
        return [
            {
                "id": "rec_test1",
                "type": "subject_optimization",
                "message": "Your subject line could use improvement",
                "suggestion": "Try including emojis in your subject line",
                "priority": 5,
                "confidence": 0.85,
                "confidenceLevel": "high",
                "confidenceExplanation": "Based on historical data with 85% statistical confidence.",
                "tags": ["subject", "optimization"]
            },
            {
                "id": "rec_test2",
                "type": "send_time_optimization",
                "message": "Consider sending at a different time",
                "suggestion": "Sending around 10am has shown better results",
                "priority": 4,
                "confidence": 0.75,
                "confidenceLevel": "high",
                "confidenceExplanation": "Based on 500 historical data points with 75% statistical confidence.",
                "tags": ["timing", "optimization"]
            }
        ]
    
    service.get_campaign_recommendations = AsyncMock(side_effect=mock_get_recommendations)
    
    # Mock the track_recommendation_interaction method
    service.track_recommendation_interaction = AsyncMock(return_value=True)
    
    return service


@patch("apps.api.services.predictive_analytics_service.get_predictive_analytics_service")
def test_get_campaign_recommendations(mock_get_service, client, mock_analytics_service):
    """Test get recommendations endpoint."""
    # Setup mock
    mock_get_service.return_value = mock_analytics_service
    
    # Test the endpoint
    response = client.get(
        "/analytics/recommendations/campaigns/1",
        params={"include_confidence": "true"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 2
    assert data["data"][0]["id"] == "rec_test1"
    assert data["data"][0]["confidenceLevel"] == "high"
    assert "suggestion" in data["data"][0]
    assert "confidenceExplanation" in data["data"][0]


@patch("apps.api.services.predictive_analytics_service.get_predictive_analytics_service")
def test_track_recommendation_interaction(mock_get_service, client, mock_analytics_service):
    """Test recommendation interaction tracking."""
    # Setup mock
    mock_get_service.return_value = mock_analytics_service
    
    # Test the endpoint
    response = client.post(
        "/analytics/recommendations/track",
        json={
            "recommendation_id": "rec_test1",
            "action": "click",
            "campaign_id": 1,
            "feedback": {
                "rating": 4,
                "applied": True,
                "useful": True
            }
        }
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == True
    
    # Verify service was called with correct parameters
    call_args = mock_analytics_service.track_recommendation_interaction.call_args[1]
    assert call_args["recommendation_id"] == "rec_test1"
    assert call_args["action"] == "click"
    assert call_args["campaign_id"] == 1
    assert call_args["feedback"]["rating"] == 4


@patch("apps.api.services.predictive_analytics_service.get_predictive_analytics_service")
def test_multiple_campaign_recommendations(mock_get_service, client, mock_analytics_service):
    """Test get recommendations for multiple campaigns."""
    # Setup mock
    mock_get_service.return_value = mock_analytics_service
    
    # Test the endpoint
    response = client.get(
        "/analytics/recommendations/campaigns",
        params={
            "campaign_ids": "1,2,3",
            "include_confidence": "true",
            "tags": "subject,timing"
        }
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 2
    
    # Verify service was called with correct parameters
    call_args = mock_analytics_service.get_campaign_recommendations.call_args[1]
    assert call_args["campaign_ids"] == [1, 2, 3]
    assert call_args["tags"] == ["subject", "timing"]
    assert call_args["include_confidence_scores"] == True