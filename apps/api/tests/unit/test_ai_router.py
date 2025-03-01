"""
Unit tests for AI cached router endpoints.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from apps.api.routers.ai_cached import router
from apps.api.services.ai_service import AIService
from apps.api.schemas.ai import AIModelRequest, AIModelResponse


@pytest.fixture
def app():
    """Create a test FastAPI app with the AI cached router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return TestClient(app)


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    service = MagicMock(spec=AIService)

    # Mock generate_response
    service.generate_response = AsyncMock(return_value=AIModelResponse(
        content="Test response",
        model="test-model",
        usage={"total_tokens": 10},
        finish_reason="stop",
        cached=False
    ))

    # Mock get_model_list
    service.get_model_list = AsyncMock(return_value=[
        {
            "id": "gpt-3.5-turbo",
            "name": "GPT-3.5 Turbo",
            "provider": "openai",
            "max_tokens": 4096,
            "supports_streaming": True
        }
    ])

    # Mock get_cache_stats
    service.get_cache_stats = AsyncMock(return_value={
        "size": 10,
        "max_size": 1000,
        "ttl_seconds": 3600,
        "hits": 50,
        "misses": 20,
        "hit_rate_percent": 71.43,
        "total_requests": 70
    })

    # Mock invalidate_cache
    service.invalidate_cache = AsyncMock(return_value=5)

    return service


@pytest.fixture
def mock_auth():
    """Mock the authentication dependency."""
    return MagicMock(return_value={"id": "test-user", "email": "test@example.com"})


class TestAICachedRouter:
    """Tests for AI cached router endpoints."""

    @patch("apps.api.routers.ai_cached.get_ai_service")
    @patch("apps.api.routers.ai_cached.get_current_user")
    def test_generate_response(self, mock_get_current_user, mock_get_ai_service, client, mock_ai_service, mock_auth):
        """Test the generate response endpoint."""
        # Setup mocks
        mock_get_ai_service.return_value = mock_ai_service
        mock_get_current_user.return_value = mock_auth.return_value

        # Make request
        response = client.post(
            "/ai/cached/generate",
            json={
                "prompt": "Test prompt",
                "model_name": "test-model",
                "temperature": 0.0,
                "max_tokens": 100
            }
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test response"
        assert data["model"] == "test-model"
        assert data["usage"] == {"total_tokens": 10}
        assert data["finish_reason"] == "stop"
        assert data["cached"] is False

        # Check service was called
        mock_ai_service.generate_response.assert_called_once()
        request = mock_ai_service.generate_response.call_args[0][0]
        assert request.prompt == "Test prompt"
        assert request.model_name == "test-model"
        assert request.temperature == 0.0
        assert request.max_tokens == 100

    @patch("apps.api.routers.ai_cached.get_ai_service")
    @patch("apps.api.routers.ai_cached.get_current_user")
    def test_get_models(self, mock_get_current_user, mock_get_ai_service, client, mock_ai_service, mock_auth):
        """Test the get models endpoint."""
        # Setup mocks
        mock_get_ai_service.return_value = mock_ai_service
        mock_get_current_user.return_value = mock_auth.return_value

        # Make request
        response = client.get("/ai/cached/models")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "gpt-3.5-turbo"
        assert data[0]["name"] == "GPT-3.5 Turbo"

        # Check service was called
        mock_ai_service.get_model_list.assert_called_once()

    @patch("apps.api.routers.ai_cached.get_ai_service")
    @patch("apps.api.routers.ai_cached.get_current_user")
    def test_get_cache_stats(self, mock_get_current_user, mock_get_ai_service, client, mock_ai_service, mock_auth):
        """Test the get cache stats endpoint."""
        # Setup mocks
        mock_get_ai_service.return_value = mock_ai_service
        mock_get_current_user.return_value = mock_auth.return_value

        # Make request
        response = client.get("/ai/cached/cache/stats")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["size"] == 10
        assert data["max_size"] == 1000
        assert data["ttl_seconds"] == 3600
        assert data["hits"] == 50
        assert data["misses"] == 20
        assert data["hit_rate_percent"] == 71.43
        assert data["total_requests"] == 70

        # Check service was called
        mock_ai_service.get_cache_stats.assert_called_once()

    @patch("apps.api.routers.ai_cached.get_ai_service")
    @patch("apps.api.routers.ai_cached.get_current_user")
    def test_invalidate_cache(self, mock_get_current_user, mock_get_ai_service, client, mock_ai_service, mock_auth):
        """Test the invalidate cache endpoint."""
        # Setup mocks
        mock_get_ai_service.return_value = mock_ai_service
        mock_get_current_user.return_value = mock_auth.return_value

        # Make request without model name
        response = client.post("/ai/cached/cache/invalidate")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["invalidated_entries"] == 5

        # Check service was called
        mock_ai_service.invalidate_cache.assert_called_once_with(None)

        # Reset mock
        mock_ai_service.invalidate_cache.reset_mock()

        # Make request with model name
        response = client.post("/ai/cached/cache/invalidate?model_name=gpt-4")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["invalidated_entries"] == 5

        # Check service was called with model name
        mock_ai_service.invalidate_cache.assert_called_once_with("gpt-4")
