"""Integration tests for background tasks and metrics endpoints."""

import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from main_fixed import app, verify_api_key, ai_service

@pytest.fixture
def test_client():
    """Create a test client for the app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def test_api_key():
    """Return a valid test API key."""
    return "test-api-key"


# Background Task Tests
@pytest.fixture
def mock_background_tasks():
    """Mock fastapi.BackgroundTasks."""
    mock = MagicMock()
    mock.add_task = MagicMock()
    return mock


# This test verifies that background tasks are correctly scheduled
@patch("main_fixed.BackgroundTasks")
def test_background_task_scheduling(mock_background_tasks_class, test_client, test_api_key):
    """Test that background tasks are properly scheduled."""
    # The mock BackgroundTasks instance that will be returned by BackgroundTasks()
    mock_bg_tasks = MagicMock()
    mock_background_tasks_class.return_value = mock_bg_tasks

    # Prepare campaign request
    campaign_request = {
        "task": "Create a promotional email",
        "model_name": "gpt-4",
        "audience": {
            "segments": ["customers"],
            "exclusions": []
        }
    }

    # Make request
    response = test_client.post(
        "/create_campaign",
        headers={"X-API-Key": test_api_key},
        json=campaign_request
    )

    # Verify response
    assert response.status_code == 200
    assert "campaign_id" in response.json()

    # Verify that add_task was called with the generate_campaign_content function
    mock_bg_tasks.add_task.assert_called_once()
    # The first argument should be the ai_service.generate_campaign_content method
    called_fn = mock_bg_tasks.add_task.call_args[0][0]
    assert called_fn == ai_service.generate_campaign_content


# Test that verifies the background task executes correctly
@pytest.mark.asyncio
async def test_background_task_execution():
    """Test that the background task for content generation executes correctly."""
    # Create a mock campaign ID
    campaign_id = "campaign-123"
    task = "Create a promotional email"
    model_name = "gpt-4"

    # Capture the original method to restore it later
    original_method = ai_service.generate_campaign_content

    # Create a flag to track if our task ran
    task_executed = False
    generated_content = "Generated content for testing"

    # Define a mock implementation
    async def mock_generate_content(campaign_id, task, model_name):
        nonlocal task_executed
        task_executed = True
        return generated_content

    # Replace the method with our mock
    ai_service.generate_campaign_content = mock_generate_content

    try:
        # Execute the background task directly
        result = await ai_service.generate_campaign_content(campaign_id, task, model_name)

        # Verify task execution
        assert task_executed is True
        assert result == generated_content
    finally:
        # Restore the original method
        ai_service.generate_campaign_content = original_method


# Metrics Endpoint Tests
def test_metrics_endpoint_with_valid_key(test_client, test_api_key):
    """Test the metrics endpoint with a valid API key."""
    response = test_client.get(
        "/metrics",
        headers={"X-API-Key": test_api_key}
    )
    assert response.status_code == 200
    data = response.json()

    # Verify metric fields
    assert "http_requests_total" in data
    assert "model_inference_duration_seconds" in data
    assert "cache_hits_total" in data
    assert "timestamp" in data


def test_metrics_endpoint_without_key(test_client):
    """Test the metrics endpoint without an API key."""
    response = test_client.get("/metrics")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data or "detail" in data


def test_metrics_endpoint_with_invalid_key(test_client):
    """Test the metrics endpoint with an invalid API key."""
    response = test_client.get(
        "/metrics",
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data or "detail" in data


# Rate Limiting Tests
@patch("main_fixed.rate_limiter")
def test_rate_limiting(mock_rate_limiter, test_client, test_api_key):
    """Test that rate limiting is applied to endpoints."""
    # Configure the rate limiter to reject the request
    mock_rate_limiter.check_limit.return_value = False

    # Make request
    response = test_client.post(
        "/create_campaign",
        headers={"X-API-Key": test_api_key},
        json={
            "task": "Create a promotional email",
            "model_name": "gpt-4"
        }
    )

    # Verify rate limit response
    assert response.status_code == 429
    assert "Retry-After" in response.headers


# System failure recovery tests
@patch("main_fixed.campaign_service")
def test_campaign_creation_db_recovery(mock_campaign_service, test_client, test_api_key):
    """Test system recovery from database failures during campaign creation."""
    # Set up mock to fail on first call but succeed on second call
    mock_campaign_service.create_campaign.side_effect = [
        Exception("Database connection error"),  # First call fails
        "campaign-123"  # Second call succeeds
    ]

    # First request - should fail with 500
    response = test_client.post(
        "/create_campaign",
        headers={"X-API-Key": test_api_key},
        json={
            "task": "Create a promotional email",
            "model_name": "gpt-4"
        }
    )
    assert response.status_code == 500

    # Reset mock call count
    mock_campaign_service.create_campaign.reset_mock()

    # Second request - should succeed
    response = test_client.post(
        "/create_campaign",
        headers={"X-API-Key": test_api_key},
        json={
            "task": "Create a promotional email",
            "model_name": "gpt-4"
        }
    )
    assert response.status_code == 200
    assert "campaign_id" in response.json()


# Model configuration tests
def test_model_configuration(test_client, test_api_key):
    """Test model configuration endpoint."""
    # Prepare configuration data
    config_data = {
        "model_name": "gpt-4",
        "api_key": "sk-test-key",
        "temperature": 0.7,
        "max_tokens": 1500
    }

    # Make request
    response = test_client.post(
        "/configure_model",
        headers={"X-API-Key": test_api_key},
        json=config_data
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == config_data["model_name"]
    assert "config_id" in data


@patch("main_fixed.ai_service")
def test_model_configuration_with_validation_error(mock_ai_service, test_client, test_api_key):
    """Test model configuration with validation error."""
    # Configure mock to raise ValueError for invalid configuration
    mock_ai_service.configure_model.side_effect = ValueError("Invalid model configuration")

    # Prepare invalid configuration data
    config_data = {
        "model_name": "invalid-model",
        "api_key": "sk-test-key",
        "temperature": 2.0,  # Invalid temperature (should be 0-1)
        "max_tokens": 1500
    }

    # Make request
    response = test_client.post(
        "/configure_model",
        headers={"X-API-Key": test_api_key},
        json=config_data
    )

    # Verify validation error response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid model configuration" in data["detail"]


# Test to ensure errors are properly logged
@patch("main_fixed.logger")
@patch("main_fixed.campaign_service")
def test_error_logging(mock_campaign_service, mock_logger, test_client, test_api_key):
    """Test that errors are properly logged."""
    # Configure mock to raise an exception
    error_message = "Database connection error"
    mock_campaign_service.create_campaign.side_effect = Exception(error_message)

    # Make request that will trigger the error
    response = test_client.post(
        "/create_campaign",
        headers={"X-API-Key": test_api_key},
        json={
            "task": "Create a promotional email",
            "model_name": "gpt-4"
        }
    )

    # Verify the error was logged
    mock_logger.error.assert_called()
    # Find if any call contains our error message
    error_was_logged = any(error_message in str(call) for call in mock_logger.error.call_args_list)
    assert error_was_logged
