import pytest
from fastapi.testclient import TestClient
from main import app, redis_client, get_db_connection, ModelError, ModelAdapter
from unittest.mock import Mock, patch
import json

client = TestClient(app)

# --- Fixtures ---

@pytest.fixture
def mock_redis():
    with patch('main.redis_client') as mock:
        yield mock

@pytest.fixture
def mock_db():
    with patch('main.get_db_connection') as mock:
        yield mock

@pytest.fixture
def mock_ray():
    with patch('main.ray') as mock:
        yield mock

@pytest.fixture
def mock_langfuse():
    with patch('main.langfuse') as mock:
        yield mock

# --- Model Adapter Tests ---

def test_openai_adapter_initialization():
    with patch('openai.OpenAI') as mock_openai:
        from main import OpenAIAdapter
        adapter = OpenAIAdapter("test-key")
        mock_openai.assert_called_once_with(api_key="test-key")

def test_openai_adapter_generation():
    with patch('openai.OpenAI') as mock_openai:
        from main import OpenAIAdapter
        mock_openai.return_value.chat.completions.create.return_value.choices[0].message.content = "test response"
        adapter = OpenAIAdapter("test-key")
        result = adapter.generate("test prompt")
        assert result == "test response"

def test_anthropic_adapter_initialization():
    with patch('anthropic.Anthropic') as mock_anthropic:
        from main import AnthropicAdapter
        adapter = AnthropicAdapter("test-key")
        mock_anthropic.assert_called_once_with(api_key="test-key")

def test_anthropic_adapter_generation():
    with patch('anthropic.Anthropic') as mock_anthropic:
        from main import AnthropicAdapter
        mock_anthropic.return_value.messages.create.return_value.content[0].text = "test response"
        adapter = AnthropicAdapter("test-key")
        result = adapter.generate("test prompt")
        assert result == "test response"

# --- Database Tests ---

def test_db_connection(mock_db):
    mock_db.return_value.cursor.return_value.execute.return_value = True
    conn = get_db_connection()
    assert conn is not None

def test_db_connection_error(mock_db):
    mock_db.side_effect = Exception("Connection failed")
    with pytest.raises(Exception):
        get_db_connection()

# --- API Tests ---

def test_health_check_all_healthy(mock_redis, mock_db, mock_ray):
    mock_redis.ping.return_value = True
    mock_db.return_value.cursor.return_value.execute.return_value = True
    mock_ray.is_initialized.return_value = True

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["services"]["redis"] == "healthy"
    assert data["services"]["postgres"] == "healthy"
    assert data["services"]["ray"] == "healthy"

def test_health_check_degraded(mock_redis, mock_db, mock_ray):
    mock_redis.ping.side_effect = Exception("Redis error")
    mock_db.return_value.cursor.return_value.execute.return_value = True
    mock_ray.is_initialized.return_value = True

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert "unhealthy" in data["services"]["redis"]["status"]

def test_create_campaign():
    response = client.post(
        "/create_campaign",
        json={
            "task": "Test campaign",
            "model_name": "mock",
            "cache_ttl": 3600
        },
        headers={"X-API-Key": "mock-api-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "campaign_id" in data
    assert data["status"] == "success"

def test_create_campaign_invalid_auth():
    response = client.post(
        "/create_campaign",
        json={"task": "Test campaign"},
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 401

def test_configure_model():
    response = client.post(
        "/configure_model",
        json={
            "model_name": "mock",
            "api_key": "test-key"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

# --- Cache Tests ---

def test_redis_caching(mock_redis):
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True

    # First call - cache miss
    response = client.post(
        "/create_campaign",
        json={
            "task": "Test campaign",
            "model_name": "mock",
            "cache_ttl": 3600
        },
        headers={"X-API-Key": "mock-api-key"}
    )
    assert response.status_code == 200
    mock_redis.get.assert_called_once()
    mock_redis.setex.assert_called_once()

    # Reset mocks
    mock_redis.get.reset_mock()
    mock_redis.setex.reset_mock()

    # Second call - cache hit
    mock_redis.get.return_value = json.dumps({"result": "cached_result"})
    response = client.post(
        "/create_campaign",
        json={
            "task": "Test campaign",
            "model_name": "mock",
            "cache_ttl": 3600
        },
        headers={"X-API-Key": "mock-api-key"}
    )
    assert response.status_code == 200
    mock_redis.get.assert_called_once()
    mock_redis.setex.assert_not_called()

# --- Error Handling Tests ---

def test_model_error_handling():
    response = client.post(
        "/configure_model",
        json={
            "model_name": "invalid_model",
            "api_key": "test-key"
        }
    )
    assert response.status_code == 400

def test_database_error_handling(mock_db):
    mock_db.side_effect = Exception("Database error")
    response = client.post(
        "/create_campaign",
        json={
            "task": "Test campaign",
            "model_name": "mock",
            "cache_ttl": 3600
        },
        headers={"X-API-Key": "mock-api-key"}
    )
    assert response.status_code == 500

# --- Performance Tests ---

@pytest.mark.performance
def test_api_response_time():
    import time
    start_time = time.time()
    response = client.get("/health")
    duration = time.time() - start_time
    assert duration < 0.2  # Less than 200ms
    assert response.status_code == 200

@pytest.mark.performance
def test_campaign_creation_performance():
    import time
    start_time = time.time()
    response = client.post(
        "/create_campaign",
        json={
            "task": "Performance test campaign",
            "model_name": "mock",
            "cache_ttl": 3600
        },
        headers={"X-API-Key": "mock-api-key"}
    )
    duration = time.time() - start_time
    assert duration < 1.0  # Less than 1 second
    assert response.status_code == 200

# --- Integration Tests ---

@pytest.mark.integration
def test_end_to_end_campaign_creation():
    # Configure model
    client.post(
        "/configure_model",
        json={
            "model_name": "mock",
            "api_key": "test-key"
        }
    )

    # Create campaign
    response = client.post(
        "/create_campaign",
        json={
            "task": "Integration test campaign",
            "model_name": "mock",
            "cache_ttl": 3600
        },
        headers={"X-API-Key": "mock-api-key"}
    )
    assert response.status_code == 200
    data = response.json()
    campaign_id = data["campaign_id"]

    # Verify campaign creation
    response = client.get(f"/campaigns/{campaign_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

# --- Agent Tests ---

def test_agent_creation(mock_langfuse):
    from main import create_content_agent
    agent = create_content_agent(user_id=1)
    assert agent.name == "ContentAgent"
    assert "expert in crafting compelling email content" in agent.system_message

def test_group_chat_creation(mock_langfuse):
    from main import create_group_chat
    chat_manager = create_group_chat(user_id=1, task="Test task")
    assert len(chat_manager.groupchat.agents) == 6  # All agents created
    assert "Collaborate to create an email campaign" in chat_manager.groupchat.system_message 