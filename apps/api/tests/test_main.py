import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from main import (
    DatabaseError,
    ModelAdapter,
    ModelError,
    app,
    get_db_connection,
    redis_client,
)

client = TestClient(app)

# --- Fixtures ---


@pytest.fixture
def mock_redis():
    with patch("main.redis_client") as mock:
        mock.get.return_value = None
        mock.setex.return_value = True
        yield mock


@pytest.fixture
def mock_db():
    with patch("main.get_db_connection") as mock:
        mock.return_value.cursor.return_value.execute.return_value = True
        yield mock


@pytest.fixture
def mock_ray():
    # Create a mock result that matches the expected format
    mock_result = {
        "status": "success",
        "result": {"subject": "Test Subject", "body": "Test Body"},
        "metadata": {
            "processed_at": "2024-02-24 12:00:00",
            "processor_id": "test_node",
            "task_type": "campaign_generation",
        },
    }

    with patch("main.ray") as mock_ray:
        # Create a mock remote decorator
        def mock_remote(func=None):
            if func is None:
                # Called as @ray.remote()
                return mock_remote

            # Create a wrapper function that has a remote method
            def wrapper(*args, **kwargs):
                return mock_result

            # Add remote method that returns the mock result
            wrapper.remote = MagicMock(return_value=mock_result)

            # Return the wrapper function
            return wrapper

        # Set up the mock_ray
        mock_ray.remote = mock_remote
        mock_ray.get.return_value = mock_result
        mock_ray.is_initialized.return_value = True
        mock_ray.get_runtime_context.return_value.node_id = "test_node"

        yield mock_ray


@pytest.fixture
def mock_langfuse():
    mock = MagicMock()
    mock.span.return_value.end.return_value = None
    with patch("main.langfuse", mock):
        yield mock


# --- Model Adapter Tests ---


def test_openai_adapter_initialization():
    with patch("openai.OpenAI") as mock_openai:
        from main import OpenAIAdapter

        adapter = OpenAIAdapter("test-key")
        mock_openai.assert_called_once_with(api_key="test-key")


def test_openai_adapter_generation():
    with patch("openai.OpenAI") as mock_openai:
        from main import OpenAIAdapter

        mock_openai.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = "test response"
        adapter = OpenAIAdapter("test-key")
        result = adapter.generate("test prompt")
        assert result == "test response"


def test_anthropic_adapter_initialization():
    with patch("anthropic.Anthropic") as mock_anthropic:
        from main import AnthropicAdapter

        adapter = AnthropicAdapter("test-key")
        mock_anthropic.assert_called_once_with(api_key="test-key")


def test_anthropic_adapter_generation():
    with patch("anthropic.Anthropic") as mock_anthropic:
        from main import AnthropicAdapter

        mock_anthropic.return_value.messages.create.return_value.content[0].text = (
            "test response"
        )
        adapter = AnthropicAdapter("test-key")
        result = adapter.generate("test prompt")
        assert result == "test response"


# --- Database Tests ---


def test_db_connection(mock_db):
    mock_db.return_value.cursor.return_value.execute.return_value = True
    conn = get_db_connection()
    assert conn is not None


def test_db_connection_error():
    with patch("psycopg2.connect") as mock_connect:
        mock_connect.side_effect = Exception("Connection failed")
        with pytest.raises(DatabaseError):
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
    # First, configure a model
    client.post("/configure_model", json={"model_name": "mock", "api_key": "test-key"})

    # Then create campaign
    response = client.post(
        "/create_campaign",
        json={"task": "Test campaign", "model_name": "mock", "cache_ttl": 3600},
        headers={"X-API-Key": "mock-api-key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "campaign_id" in data
    assert data["status"] == "success"


def test_create_campaign_invalid_auth():
    response = client.post(
        "/create_campaign",
        json={"task": "Test campaign"},
        headers={"X-API-Key": "invalid-key"},
    )
    assert response.status_code == 401


def test_configure_model():
    response = client.post(
        "/configure_model", json={"model_name": "mock", "api_key": "test-key"}
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
        json={"task": "Test campaign", "model_name": "mock", "cache_ttl": 3600},
        headers={"X-API-Key": "mock-api-key"},
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
        json={"task": "Test campaign", "model_name": "mock", "cache_ttl": 3600},
        headers={"X-API-Key": "mock-api-key"},
    )
    assert response.status_code == 200
    mock_redis.get.assert_called_once()
    mock_redis.setex.assert_not_called()


# --- Error Handling Tests ---


def test_model_error_handling():
    from main import ModelError, ModelInitializationError

    # Test invalid model name
    with patch("main.MODEL_REGISTRY", {"mock": None}):
        response = client.post(
            "/configure_model",
            json={"model_name": "invalid_model", "api_key": "test-key"},
        )
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]

    # Test model initialization error
    with patch("main.get_model_adapter") as mock_adapter:
        mock_adapter.side_effect = ModelInitializationError("Init failed")
        response = client.post(
            "/configure_model", json={"model_name": "mock", "api_key": "test-key"}
        )
        assert response.status_code == 400
        assert "Init failed" in response.json()["detail"]


def test_database_error_handling(mock_db):
    mock_db.side_effect = Exception("Database error")
    response = client.post(
        "/create_campaign",
        json={"task": "Test campaign", "model_name": "mock", "cache_ttl": 3600},
        headers={"X-API-Key": "mock-api-key"},
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
            "cache_ttl": 3600,
        },
        headers={"X-API-Key": "mock-api-key"},
    )
    duration = time.time() - start_time
    assert duration < 1.0  # Less than 1 second
    assert response.status_code == 200


# --- Integration Tests ---


@pytest.mark.integration
def test_end_to_end_campaign_creation():
    # Configure model
    client.post("/configure_model", json={"model_name": "mock", "api_key": "test-key"})

    # Create campaign
    response = client.post(
        "/create_campaign",
        json={
            "task": "Integration test campaign",
            "model_name": "mock",
            "cache_ttl": 3600,
        },
        headers={"X-API-Key": "mock-api-key"},
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


def test_all_agent_types(mock_langfuse):
    from main import (
        create_analytics_agent,
        create_content_agent,
        create_delivery_agent,
        create_design_agent,
        create_governance_agent,
        create_personalization_agent,
    )

    # Test each agent type
    agents = [
        (
            create_content_agent(1),
            "ContentAgent",
            "expert in crafting compelling email content",
        ),
        (create_design_agent(1), "DesignAgent", "expert in email design"),
        (create_analytics_agent(1), "AnalyticsAgent", "expert in campaign analytics"),
        (
            create_personalization_agent(1),
            "PersonalizationAgent",
            "expert in personalization",
        ),
        (create_delivery_agent(1), "DeliveryAgent", "expert in email delivery"),
        (create_governance_agent(1), "GovernanceAgent", "expert in compliance"),
    ]

    for agent, expected_name, expected_message in agents:
        assert agent.name == expected_name
        assert expected_message in agent.system_message


def test_agent_creation_error_handling(mock_langfuse):
    from main import create_agent

    # Test with invalid user_id
    agent = create_agent("TestAgent", "Test message", -1)
    assert agent.llm_config["config_list"][0]["model"] == "mock"

    # Test with failing langfuse
    mock_langfuse.side_effect = Exception("Langfuse error")
    agent = create_agent("TestAgent", "Test message", 1)
    assert agent.llm_config["config_list"][0]["model"] == "mock"


def test_langfuse_llm_initialization(mock_langfuse, mock_db):
    from main import LangfuseLLM

    # Test successful initialization
    llm = LangfuseLLM(mock_langfuse, user_id=1)
    assert llm.langfuse == mock_langfuse
    assert llm.user_id == 1

    # Test config list retrieval with DB error
    mock_db.side_effect = Exception("DB error")
    llm = LangfuseLLM(mock_langfuse, user_id=1)
    config = llm.config_list
    assert config[0]["model"] == "mock"
    assert config[0]["api_key"] == "test-api-key"


def test_langfuse_llm_generation(mock_langfuse):
    from main import LangfuseLLM

    llm = LangfuseLLM(mock_langfuse, user_id=1)

    # Test successful generation
    result = llm.create(messages=[{"role": "user", "content": "test prompt"}])
    assert "choices" in result
    assert result["choices"][0]["message"]["role"] == "assistant"

    # Test generation with retry
    mock_langfuse.span.side_effect = None  # Reset side effect
    mock_langfuse.span.return_value.end.side_effect = [Exception("First error"), None]
    result = llm.create(prompt="test prompt")
    assert "choices" in result
    assert result["choices"][0]["message"]["role"] == "assistant"


def test_group_chat_creation(mock_langfuse):
    from main import create_group_chat

    chat_manager = create_group_chat(user_id=1, task="Test task")

    # Test agent creation
    assert len(chat_manager.groupchat.agents) == 6  # All agents created
    agent_names = {agent.name for agent in chat_manager.groupchat.agents}
    expected_names = {
        "ContentAgent",
        "DesignAgent",
        "AnalyticsAgent",
        "PersonalizationAgent",
        "DeliveryAgent",
        "GovernanceAgent",
    }
    assert agent_names == expected_names

    # Test system message
    system_messages = [
        msg for msg in chat_manager.groupchat.messages if msg["role"] == "system"
    ]
    assert len(system_messages) == 1
    assert "Collaborate to create an email campaign" in system_messages[0]["content"]

    # Test chat configuration
    assert chat_manager.groupchat.max_round == 12
    assert chat_manager.groupchat.speaker_selection_method == "round_robin"
    assert not chat_manager.groupchat.allow_repeat_speaker


def test_group_chat_error_handling(mock_langfuse):
    from main import create_content_agent, create_group_chat

    # Mock create_content_agent to raise an exception
    with patch("main.create_content_agent") as mock_create_agent:
        mock_create_agent.side_effect = Exception("Agent creation error")
        with pytest.raises(HTTPException) as exc_info:
            create_group_chat(user_id=1, task="Test task")
        assert exc_info.value.status_code == 500
        assert "Failed to initialize agent group chat" in str(exc_info.value.detail)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert "timestamp" in data
    assert data["services"]["redis"] == "healthy"
    assert data["services"]["postgres"] == "healthy"
    assert data["services"]["ray"] == "healthy"
