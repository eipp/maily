import pytest
from unittest.mock import patch, MagicMock

# Mock process_campaign_task function
def mock_process_campaign_task(*args, **kwargs):
    return {
        "status": "success",
        "result": {
            "subject": "Test Subject",
            "body": "Test Body"
        },
        "metadata": {
            "model": "mock",
            "timestamp": "2024-02-24 12:00:00"
        }
    }

# Add remote attribute to the function
mock_process_campaign_task.remote = lambda *args, **kwargs: mock_process_campaign_task()

@pytest.fixture
def mock_ray():
    # Create a mock result that matches the expected format
    mock_result = {
        "status": "success",
        "result": {
            "subject": "Test Subject",
            "body": "Test Body"
        },
        "metadata": {
            "processed_at": "2024-02-24 12:00:00",
            "processor_id": "test_node",
            "task_type": "campaign_generation"
        }
    }

    # Create a MagicMock for process_campaign_task that handles both direct calls and remote calls
    mock_process_task = MagicMock(return_value=mock_result)
    mock_remote_result = MagicMock(return_value=mock_result)
    mock_process_task.remote = mock_remote_result

    with patch('main.ray') as mock_ray, \
         patch('main.process_campaign_task', mock_process_task):

        # Set up basic Ray functionality
        mock_ray.get.return_value = mock_result
        mock_ray.is_initialized.return_value = True
        mock_ray.get_runtime_context.return_value.node_id = "test_node"
        mock_ray.remote = MagicMock(return_value=mock_process_task)

        yield mock_ray

def test_model_error_handling():
    from main import ModelError, ModelInitializationError
    from fastapi import HTTPException

    # Test invalid model name
    with patch('main.MODEL_REGISTRY', {"mock": None}):
        response = client.post(
            "/configure_model",
            json={
                "model_name": "invalid_model",
                "api_key": "test-key"
            }
        )
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]

    # Test model initialization error
    with patch('main.get_model_adapter') as mock_get_adapter:
        mock_get_adapter.side_effect = ModelInitializationError("Init failed")
        response = client.post(
            "/configure_model",
            json={
                "model_name": "mock",
                "api_key": "test-key"
            }
        )
        assert response.status_code == 400
        assert "Init failed" in response.json()["detail"]
