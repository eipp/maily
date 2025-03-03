"""
Tests for AI Mesh Network

This module contains tests for the AI Mesh Network feature.
"""

import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ai_service.services.agent_coordinator import AgentCoordinator, get_agent_coordinator
from ai_service.utils.redis_client import RedisClient
from ai_service.utils.llm_client import LLMClient

# Test data
TEST_NETWORK_ID = f"network_{uuid.uuid4().hex[:8]}"
TEST_AGENT_ID = f"agent_{uuid.uuid4().hex[:8]}"
TEST_TASK_ID = f"task_{uuid.uuid4().hex[:8]}"
TEST_MEMORY_ID = f"memory_{uuid.uuid4().hex[:8]}"

TEST_NETWORK = {
    "id": TEST_NETWORK_ID,
    "name": "Test Network",
    "description": "Test network for unit tests",
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat(),
    "status": "active",
    "max_iterations": 5,
    "timeout_seconds": 60,
    "shared_context": {},
    "agents": [TEST_AGENT_ID],
    "tasks": [],
    "memories": []
}

TEST_AGENT = {
    "id": TEST_AGENT_ID,
    "network_id": TEST_NETWORK_ID,
    "name": "Test Agent",
    "type": "test",
    "model": "claude-3-7-sonnet",
    "description": "Test agent for unit tests",
    "parameters": {"temperature": 0.7, "max_tokens": 1000},
    "capabilities": ["test_capability"],
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat(),
    "status": "idle",
    "confidence": 1.0,
    "last_action": None,
    "assigned_tasks": [],
    "connections": []
}

TEST_TASK = {
    "id": TEST_TASK_ID,
    "network_id": TEST_NETWORK_ID,
    "description": "Test task",
    "context": {"test_key": "test_value"},
    "priority": 1,
    "deadline": None,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat(),
    "status": "pending",
    "assigned_to": None,
    "iterations": 0,
    "max_iterations": 5,
    "result": None,
    "subtasks": [],
    "dependencies": [],
    "history": []
}

TEST_MEMORY = {
    "id": TEST_MEMORY_ID,
    "network_id": TEST_NETWORK_ID,
    "type": "fact",
    "content": "This is a test memory",
    "confidence": 1.0,
    "created_at": datetime.utcnow().isoformat(),
    "metadata": {}
}

# Fixtures
@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    redis_client = AsyncMock(spec=RedisClient)
    
    # Mock data storage
    data_store = {}
    
    # Mock Redis methods
    async def mock_get(key):
        return data_store.get(key)
    
    async def mock_set(key, value, ex=None):
        data_store[key] = value
        return True
    
    async def mock_delete(key):
        if key in data_store:
            del data_store[key]
            return True
        return False
    
    async def mock_keys(pattern):
        # Simple pattern matching for testing
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            return [k for k in data_store.keys() if k.startswith(prefix)]
        return []
    
    async def mock_ping():
        return True
    
    # Assign mocked methods
    redis_client.get = mock_get
    redis_client.set = mock_set
    redis_client.delete = mock_delete
    redis_client.keys = mock_keys
    redis_client.ping = mock_ping
    
    return redis_client

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    llm_client = AsyncMock(spec=LLMClient)
    
    # Mock generate_text method
    async def mock_generate_text(prompt, model="claude-3-7-sonnet", temperature=0.7, max_tokens=4000, system_prompt=None):
        # For coordinator prompts
        if "coordinator agent" in prompt.lower():
            return {
                "content": json.dumps({
                    "task_complete": False,
                    "reasoning": "This is a test reasoning",
                    "subtasks": [
                        {
                            "agent_id": TEST_AGENT_ID,
                            "description": "Test subtask"
                        }
                    ],
                    "new_memories": [
                        {
                            "type": "fact",
                            "content": "Test memory content",
                            "confidence": 0.9
                        }
                    ]
                }),
                "model": model,
                "provider": "anthropic",
                "usage": {"prompt_tokens": 100, "completion_tokens": 50}
            }
        
        # For agent prompts
        elif "specialized" in prompt.lower():
            return {
                "content": json.dumps({
                    "reasoning": "Test agent reasoning",
                    "result": "Test agent result",
                    "confidence": 0.8,
                    "suggested_memories": [
                        {
                            "type": "fact",
                            "content": "Test suggested memory",
                            "confidence": 0.7
                        }
                    ]
                }),
                "model": model,
                "provider": "anthropic",
                "usage": {"prompt_tokens": 80, "completion_tokens": 40}
            }
        
        # For final result prompts
        elif "synthesize" in prompt.lower():
            return {
                "content": json.dumps({
                    "content": "Test final result",
                    "confidence": 0.9,
                    "explanation": "Test explanation"
                }),
                "model": model,
                "provider": "anthropic",
                "usage": {"prompt_tokens": 120, "completion_tokens": 60}
            }
        
        # Default response
        return {
            "content": "Test response",
            "model": model,
            "provider": "anthropic",
            "usage": {"prompt_tokens": 50, "completion_tokens": 25}
        }
    
    # Mock check_health method
    async def mock_check_health():
        return {
            "status": "healthy",
            "providers": {
                "anthropic": {"status": "healthy", "status_code": 200},
                "openai": {"status": "healthy", "status_code": 200},
                "google": {"status": "healthy", "status_code": 200}
            },
            "timestamp": datetime.utcnow().timestamp()
        }
    
    # Assign mocked methods
    llm_client.generate_text = mock_generate_text
    llm_client.check_health = mock_check_health
    
    return llm_client

@pytest.fixture
def agent_coordinator(mock_redis_client, mock_llm_client):
    """Create an AgentCoordinator instance with mocked dependencies"""
    coordinator = AgentCoordinator()
    coordinator.redis = mock_redis_client
    coordinator.llm_client = mock_llm_client
    return coordinator

# Tests
@pytest.mark.asyncio
async def test_create_network(agent_coordinator):
    """Test creating a new AI Mesh Network"""
    # Arrange
    name = "Test Network"
    description = "Test network for unit tests"
    
    # Act
    network_id = await agent_coordinator.create_network(name, description)
    
    # Assert
    assert network_id is not None
    assert network_id.startswith("network_")
    
    # Verify network was stored in Redis
    network_key = f"ai_mesh:network:{network_id}"
    network_data = await agent_coordinator.redis.get(network_key)
    assert network_data is not None
    
    network = json.loads(network_data)
    assert network["name"] == name
    assert network["description"] == description
    assert len(network["agents"]) == 5  # Default agents

@pytest.mark.asyncio
async def test_get_network(agent_coordinator):
    """Test getting an AI Mesh Network"""
    # Arrange
    network_key = f"ai_mesh:network:{TEST_NETWORK_ID}"
    await agent_coordinator.redis.set(network_key, json.dumps(TEST_NETWORK))
    
    agent_key = f"ai_mesh:agent:{TEST_AGENT_ID}"
    await agent_coordinator.redis.set(agent_key, json.dumps(TEST_AGENT))
    
    # Act
    network = await agent_coordinator.get_network(TEST_NETWORK_ID)
    
    # Assert
    assert network is not None
    assert network["id"] == TEST_NETWORK_ID
    assert network["name"] == TEST_NETWORK["name"]
    assert len(network["agents"]) == 1
    assert network["agents"][0]["id"] == TEST_AGENT_ID

@pytest.mark.asyncio
async def test_delete_network(agent_coordinator):
    """Test deleting an AI Mesh Network"""
    # Arrange
    network_key = f"ai_mesh:network:{TEST_NETWORK_ID}"
    await agent_coordinator.redis.set(network_key, json.dumps(TEST_NETWORK))
    
    agent_key = f"ai_mesh:agent:{TEST_AGENT_ID}"
    await agent_coordinator.redis.set(agent_key, json.dumps(TEST_AGENT))
    
    # Act
    success = await agent_coordinator.delete_network(TEST_NETWORK_ID)
    
    # Assert
    assert success is True
    
    # Verify network and agent were deleted from Redis
    network_data = await agent_coordinator.redis.get(network_key)
    assert network_data is None
    
    agent_data = await agent_coordinator.redis.get(agent_key)
    assert agent_data is None

@pytest.mark.asyncio
async def test_submit_task(agent_coordinator):
    """Test submitting a task to an AI Mesh Network"""
    # Arrange
    network_key = f"ai_mesh:network:{TEST_NETWORK_ID}"
    await agent_coordinator.redis.set(network_key, json.dumps(TEST_NETWORK))
    
    task_description = "Test task"
    task_context = {"test_key": "test_value"}
    
    # Act
    task_id = await agent_coordinator.submit_task(
        network_id=TEST_NETWORK_ID,
        task=task_description,
        context=task_context
    )
    
    # Assert
    assert task_id is not None
    assert task_id.startswith("task_")
    
    # Verify task was stored in Redis
    task_key = f"ai_mesh:task:{task_id}"
    task_data = await agent_coordinator.redis.get(task_key)
    assert task_data is not None
    
    task = json.loads(task_data)
    assert task["description"] == task_description
    assert task["context"] == task_context
    assert task["status"] == "pending"
    
    # Verify task was added to network
    updated_network_data = await agent_coordinator.redis.get(network_key)
    updated_network = json.loads(updated_network_data)
    assert task_id in updated_network["tasks"]

@pytest.mark.asyncio
async def test_process_task(agent_coordinator):
    """Test processing a task in the AI Mesh Network"""
    # Arrange
    network_key = f"ai_mesh:network:{TEST_NETWORK_ID}"
    await agent_coordinator.redis.set(network_key, json.dumps(TEST_NETWORK))
    
    task_key = f"ai_mesh:task:{TEST_TASK_ID}"
    await agent_coordinator.redis.set(task_key, json.dumps(TEST_TASK))
    
    # Create coordinator agent
    coordinator_agent = {
        "id": f"agent_{uuid.uuid4().hex[:8]}",
        "network_id": TEST_NETWORK_ID,
        "name": "Coordinator",
        "type": "coordinator",
        "model": "claude-3-7-sonnet",
        "description": "Coordinates tasks",
        "parameters": {"temperature": 0.2, "max_tokens": 4000},
        "capabilities": ["task_delegation", "task_coordination", "task_synthesis"],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "status": "idle",
        "confidence": 1.0,
        "last_action": None,
        "assigned_tasks": [],
        "connections": []
    }
    
    coordinator_key = f"ai_mesh:agent:{coordinator_agent['id']}"
    await agent_coordinator.redis.set(coordinator_key, json.dumps(coordinator_agent))
    
    # Update network with coordinator agent
    updated_network = dict(TEST_NETWORK)
    updated_network["agents"].append(coordinator_agent["id"])
    await agent_coordinator.redis.set(network_key, json.dumps(updated_network))
    
    # Act
    await agent_coordinator.process_task(TEST_NETWORK_ID, TEST_TASK_ID)
    
    # Assert
    # Verify task was updated
    updated_task_data = await agent_coordinator.redis.get(task_key)
    updated_task = json.loads(updated_task_data)
    
    assert updated_task["status"] == "completed"
    assert updated_task["result"] is not None
    assert len(updated_task["history"]) > 0

@pytest.mark.asyncio
async def test_add_memory(agent_coordinator):
    """Test adding a memory item to the shared memory"""
    # Arrange
    network_key = f"ai_mesh:network:{TEST_NETWORK_ID}"
    await agent_coordinator.redis.set(network_key, json.dumps(TEST_NETWORK))
    
    content = "Test memory content"
    memory_type = "fact"
    confidence = 0.9
    
    # Act
    memory_id = await agent_coordinator.add_memory(
        network_id=TEST_NETWORK_ID,
        content=content,
        memory_type=memory_type,
        confidence=confidence
    )
    
    # Assert
    assert memory_id is not None
    assert memory_id.startswith("memory_")
    
    # Verify memory was stored in Redis
    memory_key = f"ai_mesh:memory:{memory_id}"
    memory_data = await agent_coordinator.redis.get(memory_key)
    assert memory_data is not None
    
    memory = json.loads(memory_data)
    assert memory["content"] == content
    assert memory["type"] == memory_type
    assert memory["confidence"] == confidence
    
    # Verify memory was added to network
    updated_network_data = await agent_coordinator.redis.get(network_key)
    updated_network = json.loads(updated_network_data)
    assert memory_id in updated_network["memories"]

@pytest.mark.asyncio
async def test_get_network_memory(agent_coordinator):
    """Test getting shared memory for a network"""
    # Arrange
    network_key = f"ai_mesh:network:{TEST_NETWORK_ID}"
    network = dict(TEST_NETWORK)
    network["memories"] = [TEST_MEMORY_ID]
    await agent_coordinator.redis.set(network_key, json.dumps(network))
    
    memory_key = f"ai_mesh:memory:{TEST_MEMORY_ID}"
    await agent_coordinator.redis.set(memory_key, json.dumps(TEST_MEMORY))
    
    # Act
    memories = await agent_coordinator.get_network_memory(TEST_NETWORK_ID)
    
    # Assert
    assert len(memories) == 1
    assert memories[0]["id"] == TEST_MEMORY_ID
    assert memories[0]["content"] == TEST_MEMORY["content"]
    assert memories[0]["type"] == TEST_MEMORY["type"]

@pytest.mark.asyncio
async def test_check_health(agent_coordinator):
    """Test checking health of the AI Mesh Network service"""
    # Act
    health = await agent_coordinator.check_health()
    
    # Assert
    assert health["status"] == "healthy"
    assert health["redis_connection"] is True
    assert health["llm_client"]["status"] == "healthy"
    assert "active_networks_count" in health
    assert "active_tasks_count" in health
    assert "timestamp" in health

@pytest.mark.asyncio
async def test_singleton_instance():
    """Test that get_agent_coordinator returns a singleton instance"""
    # Act
    coordinator1 = get_agent_coordinator()
    coordinator2 = get_agent_coordinator()
    
    # Assert
    assert coordinator1 is coordinator2
