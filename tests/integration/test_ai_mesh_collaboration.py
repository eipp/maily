"""
Integration tests for AI Mesh Network agent collaboration

These tests verify that multiple agents can collaborate effectively
through the agent coordinator service.
"""

import pytest
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ai_service.services.agent_coordinator import AgentCoordinator, get_agent_coordinator
from ai_service.implementations.agents.base_agent import Agent
from ai_service.implementations.agents.coordinator_agent import CoordinatorAgent
from ai_service.implementations.agents.content_agent import ContentAgent
from ai_service.implementations.agents.analytics_agent import AnalyticsAgent
from ai_service.implementations.agents.personalization_agent import PersonalizationAgent
from ai_service.utils.redis_client import RedisClient
from ai_service.utils.llm_client import LLMClient

# Test data
TEST_NETWORK_ID = f"test_network_{uuid.uuid4().hex[:8]}"
TEST_COORDINATOR_ID = f"coordinator_{uuid.uuid4().hex[:8]}"
TEST_CONTENT_AGENT_ID = f"content_{uuid.uuid4().hex[:8]}"
TEST_ANALYTICS_AGENT_ID = f"analytics_{uuid.uuid4().hex[:8]}"
TEST_PERSONALIZATION_AGENT_ID = f"personalization_{uuid.uuid4().hex[:8]}"
TEST_TASK_ID = f"task_{uuid.uuid4().hex[:8]}"
TEST_MEMORY_ID = f"memory_{uuid.uuid4().hex[:8]}"

# Test fixtures for mock services
@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    redis_client = AsyncMock(spec=RedisClient)
    
    # Mock data storage
    data_store = {}
    pubsub_channels = {}
    
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
    
    async def mock_publish(channel, message):
        if channel not in pubsub_channels:
            pubsub_channels[channel] = []
        pubsub_channels[channel].append(message)
        return 1  # Number of clients that received the message
    
    # Assign mocked methods
    redis_client.get = mock_get
    redis_client.set = mock_set
    redis_client.delete = mock_delete
    redis_client.keys = mock_keys
    redis_client.publish = mock_publish
    
    # Create pipeline method
    def mock_pipeline():
        pipeline = AsyncMock()
        
        # Store commands to execute later
        commands = []
        
        # Methods add commands to the list
        async def pipe_get(key):
            commands.append(("get", key))
            return pipeline
        
        async def pipe_set(key, value, ex=None):
            commands.append(("set", key, value))
            return pipeline
        
        async def pipe_delete(key):
            commands.append(("delete", key))
            return pipeline
        
        # Execute runs all commands and returns results
        async def pipe_execute():
            results = []
            for cmd in commands:
                if cmd[0] == "get":
                    results.append(data_store.get(cmd[1]))
                elif cmd[0] == "set":
                    data_store[cmd[1]] = cmd[2]
                    results.append(True)
                elif cmd[0] == "delete":
                    if cmd[1] in data_store:
                        del data_store[cmd[1]]
                        results.append(True)
                    else:
                        results.append(False)
            return results
        
        # Assign methods
        pipeline.get = pipe_get
        pipeline.set = pipe_set
        pipeline.delete = pipe_delete
        pipeline.execute = pipe_execute
        
        return pipeline
    
    redis_client.pipeline = mock_pipeline
    
    return redis_client

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    llm_client = AsyncMock(spec=LLMClient)
    
    # Mock response data for different agent types
    coordinator_responses = {
        "task_delegation": {
            "content": json.dumps({
                "task_complete": False,
                "reasoning": "This task requires content creation and audience analysis.",
                "subtasks": [
                    {
                        "agent_id": TEST_CONTENT_AGENT_ID,
                        "description": "Create compelling email content focused on product features."
                    },
                    {
                        "agent_id": TEST_ANALYTICS_AGENT_ID,
                        "description": "Analyze previous engagement metrics to identify optimal send time."
                    },
                    {
                        "agent_id": TEST_PERSONALIZATION_AGENT_ID,
                        "description": "Suggest personalization elements based on audience segmentation."
                    }
                ],
                "new_memories": [
                    {
                        "type": "context",
                        "content": "This campaign targets product users who haven't upgraded in 6 months.",
                        "confidence": 0.9
                    }
                ]
            }),
            "model": "claude-3-7-sonnet",
            "provider": "anthropic",
            "usage": {"prompt_tokens": 250, "completion_tokens": 150}
        },
        "task_synthesis": {
            "content": json.dumps({
                "task_complete": True,
                "reasoning": "All subtasks have been completed successfully.",
                "result": {
                    "email_content": "Content from content agent",
                    "best_send_time": "Tuesday at 10am",
                    "personalization_elements": ["First name", "Product usage stats", "Custom offer"]
                },
                "new_memories": [
                    {
                        "type": "decision",
                        "content": "Email campaign has been optimized for Tuesday morning deployment.",
                        "confidence": 0.95
                    }
                ]
            }),
            "model": "claude-3-7-sonnet",
            "provider": "anthropic",
            "usage": {"prompt_tokens": 500, "completion_tokens": 200}
        }
    }
    
    content_agent_responses = {
        "content_generation": {
            "content": json.dumps({
                "reasoning": "Created content focusing on key product benefits and upgrade incentives.",
                "result": "Subject: Upgrade Your Experience Today\n\nHello {{first_name}},\n\nIt's been 6 months since you started using our product, and we have some exciting new features that could help you {{personalized_benefit}}. Our latest version includes {{feature_list}} that our users are loving.\n\nUpgrade today and get 20% off your next billing cycle!\n\nBest regards,\nThe Team",
                "confidence": 0.9,
                "suggested_memories": [
                    {
                        "type": "fact",
                        "content": "Email content focuses on upgrade benefits with 20% discount offer.",
                        "confidence": 0.95
                    }
                ]
            }),
            "model": "claude-3-7-sonnet",
            "provider": "anthropic",
            "usage": {"prompt_tokens": 200, "completion_tokens": 300}
        }
    }
    
    analytics_agent_responses = {
        "data_analysis": {
            "content": json.dumps({
                "reasoning": "Analyzed open and click rates across time periods for similar campaigns.",
                "result": {
                    "best_send_time": "Tuesday at 10:00 AM",
                    "historical_open_rate": "42%",
                    "expected_engagement_lift": "15%"
                },
                "confidence": 0.85,
                "suggested_memories": [
                    {
                        "type": "fact",
                        "content": "Tuesday at 10:00 AM shows 15% higher engagement for this audience segment.",
                        "confidence": 0.85
                    }
                ]
            }),
            "model": "claude-3-7-sonnet",
            "provider": "anthropic",
            "usage": {"prompt_tokens": 180, "completion_tokens": 150}
        }
    }
    
    personalization_agent_responses = {
        "audience_analysis": {
            "content": json.dumps({
                "reasoning": "Identified key personalization elements based on user segments and behavior.",
                "result": {
                    "personalization_elements": [
                        {"field": "first_name", "importance": "high"},
                        {"field": "last_active_feature", "importance": "high"},
                        {"field": "personalized_benefit", "importance": "critical", "mapping": {
                            "power_users": "save time with batch operations",
                            "occasional_users": "simplify your workflow",
                            "mobile_users": "stay productive on the go"
                        }}
                    ],
                    "segment_recommendations": {
                        "power_users": "Focus on advanced features",
                        "occasional_users": "Emphasize ease of use",
                        "mobile_users": "Highlight mobile improvements"
                    }
                },
                "confidence": 0.88,
                "suggested_memories": [
                    {
                        "type": "fact",
                        "content": "Personalized benefits by user segment increase conversion by approximately 24%.",
                        "confidence": 0.88
                    }
                ]
            }),
            "model": "claude-3-7-sonnet",
            "provider": "anthropic",
            "usage": {"prompt_tokens": 220, "completion_tokens": 280}
        }
    }
    
    # Mock generate_text method
    async def mock_generate_text(prompt, model="claude-3-7-sonnet", temperature=0.7, max_tokens=4000, system_prompt=None):
        # Determine which type of agent is making the request
        if "coordinator agent" in prompt.lower():
            if "synthesize" in prompt.lower() or "final result" in prompt.lower():
                return coordinator_responses["task_synthesis"]
            else:
                return coordinator_responses["task_delegation"]
        
        elif "content agent" in prompt.lower() or "email content" in prompt.lower():
            return content_agent_responses["content_generation"]
        
        elif "analytics agent" in prompt.lower() or "data analysis" in prompt.lower():
            return analytics_agent_responses["data_analysis"]
        
        elif "personalization agent" in prompt.lower() or "audience analysis" in prompt.lower():
            return personalization_agent_responses["audience_analysis"]
        
        # Default fallback response
        return {
            "content": "I'll help with that task.",
            "model": model,
            "provider": "anthropic",
            "usage": {"prompt_tokens": 50, "completion_tokens": 10}
        }
    
    # Assign mocked methods
    llm_client.generate_text = mock_generate_text
    
    return llm_client

@pytest.fixture
def agent_coordinator(mock_redis_client, mock_llm_client):
    """Create a AgentCoordinator instance with mocked dependencies"""
    with patch('ai_service.routers.websocket_router.broadcast_task_update', new_callable=AsyncMock) as mock_broadcast_task:
        with patch('ai_service.routers.websocket_router.broadcast_network_update', new_callable=AsyncMock) as mock_broadcast_network:
            coordinator = AgentCoordinator()
            coordinator.redis = mock_redis_client
            coordinator.llm_client = mock_llm_client
            
            # Set up test network and agents
            async def setup_test_environment():
                # Create test network
                network = {
                    "id": TEST_NETWORK_ID,
                    "name": "Test Collaboration Network",
                    "description": "Network for testing agent collaboration",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "status": "active",
                    "max_iterations": 5,
                    "timeout_seconds": 120,
                    "shared_context": {},
                    "agents": [
                        TEST_COORDINATOR_ID,
                        TEST_CONTENT_AGENT_ID,
                        TEST_ANALYTICS_AGENT_ID,
                        TEST_PERSONALIZATION_AGENT_ID
                    ],
                    "tasks": [],
                    "memories": []
                }
                
                # Create coordinator agent
                coordinator_agent = {
                    "id": TEST_COORDINATOR_ID,
                    "network_id": TEST_NETWORK_ID,
                    "name": "Coordinator",
                    "type": "coordinator",
                    "model": "claude-3-7-sonnet",
                    "description": "Coordinates tasks across specialized agents",
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
                
                # Create content agent
                content_agent = {
                    "id": TEST_CONTENT_AGENT_ID,
                    "network_id": TEST_NETWORK_ID,
                    "name": "Content Specialist",
                    "type": "content",
                    "model": "claude-3-7-sonnet",
                    "description": "Specializes in content creation",
                    "parameters": {"temperature": 0.7, "max_tokens": 4000},
                    "capabilities": ["content_generation", "content_editing"],
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "status": "idle",
                    "confidence": 1.0,
                    "last_action": None,
                    "assigned_tasks": [],
                    "connections": []
                }
                
                # Create analytics agent
                analytics_agent = {
                    "id": TEST_ANALYTICS_AGENT_ID,
                    "network_id": TEST_NETWORK_ID,
                    "name": "Analytics Specialist",
                    "type": "analytics",
                    "model": "claude-3-7-sonnet",
                    "description": "Specializes in data analysis",
                    "parameters": {"temperature": 0.3, "max_tokens": 4000},
                    "capabilities": ["data_analysis", "trend_identification"],
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "status": "idle",
                    "confidence": 1.0,
                    "last_action": None,
                    "assigned_tasks": [],
                    "connections": []
                }
                
                # Create personalization agent
                personalization_agent = {
                    "id": TEST_PERSONALIZATION_AGENT_ID,
                    "network_id": TEST_NETWORK_ID,
                    "name": "Personalization Specialist",
                    "type": "personalization",
                    "model": "claude-3-7-sonnet",
                    "description": "Specializes in audience targeting and personalization",
                    "parameters": {"temperature": 0.5, "max_tokens": 4000},
                    "capabilities": ["audience_analysis", "personalization"],
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "status": "idle",
                    "confidence": 1.0,
                    "last_action": None,
                    "assigned_tasks": [],
                    "connections": []
                }
                
                # Store in Redis
                network_key = f"ai_mesh:network:{TEST_NETWORK_ID}"
                coordinator_key = f"ai_mesh:agent:{TEST_COORDINATOR_ID}"
                content_agent_key = f"ai_mesh:agent:{TEST_CONTENT_AGENT_ID}"
                analytics_agent_key = f"ai_mesh:agent:{TEST_ANALYTICS_AGENT_ID}"
                personalization_agent_key = f"ai_mesh:agent:{TEST_PERSONALIZATION_AGENT_ID}"
                
                await coordinator.redis.set(network_key, json.dumps(network))
                await coordinator.redis.set(coordinator_key, json.dumps(coordinator_agent))
                await coordinator.redis.set(content_agent_key, json.dumps(content_agent))
                await coordinator.redis.set(analytics_agent_key, json.dumps(analytics_agent))
                await coordinator.redis.set(personalization_agent_key, json.dumps(personalization_agent))
            
            # Run setup
            asyncio.run(setup_test_environment())
            
            return coordinator

# Tests
@pytest.mark.asyncio
async def test_multi_agent_collaboration(agent_coordinator):
    """Test collaboration between multiple specialized agents"""
    # Submit a complex task that requires multiple agents
    task_description = "Create a personalized email campaign for users who haven't upgraded in the last 6 months."
    task_context = {
        "audience": "inactive_users",
        "campaign_type": "upgrade",
        "inactivity_threshold": "6 months",
        "previous_campaigns": [
            {"name": "Spring Upgrade", "open_rate": "32%", "conversion_rate": "8%"},
            {"name": "Feature Announcement", "open_rate": "41%", "conversion_rate": "12%"}
        ]
    }
    
    # Submit the task
    task_id = await agent_coordinator.submit_task(
        network_id=TEST_NETWORK_ID,
        task=task_description,
        context=task_context
    )
    
    # Verify task was created
    assert task_id is not None
    
    # Process the task
    await agent_coordinator.process_task(TEST_NETWORK_ID, task_id)
    
    # Get the task result
    task = await agent_coordinator.get_task(task_id)
    
    # Verify the task was completed
    assert task["status"] == "completed"
    assert task["result"] is not None
    
    # Verify all agents were involved (check history)
    agent_ids_in_history = set()
    for entry in task["history"]:
        if "agent_id" in entry:
            agent_ids_in_history.add(entry["agent_id"])
    
    assert TEST_COORDINATOR_ID in agent_ids_in_history
    assert TEST_CONTENT_AGENT_ID in agent_ids_in_history
    assert TEST_ANALYTICS_AGENT_ID in agent_ids_in_history
    assert TEST_PERSONALIZATION_AGENT_ID in agent_ids_in_history
    
    # Verify the expected results are present
    result = task["result"]
    assert "email_content" in result
    assert "best_send_time" in result
    assert "personalization_elements" in result

@pytest.mark.asyncio
async def test_memory_sharing_between_agents(agent_coordinator):
    """Test that agents can share memory and build on each other's work"""
    # Submit a task
    task_description = "Analyze and improve our email campaign strategy."
    task_context = {"current_open_rate": "28%", "goal": "increase engagement"}
    
    # Submit the task
    task_id = await agent_coordinator.submit_task(
        network_id=TEST_NETWORK_ID,
        task=task_description,
        context=task_context
    )
    
    # Process the task
    await agent_coordinator.process_task(TEST_NETWORK_ID, task_id)
    
    # Verify memories were created
    network_memories = await agent_coordinator.get_network_memory(TEST_NETWORK_ID)
    
    # Should have at least some memories from the agents
    assert len(network_memories) > 0
    
    # Verify memory types
    memory_types = {memory["type"] for memory in network_memories}
    assert "fact" in memory_types  # Should have at least some facts
    
    # Content of memories should be relevant to the task
    relevant_terms = ["email", "campaign", "engagement", "open rate", "send time", "personalization"]
    found_relevant_terms = []
    
    for memory in network_memories:
        content = memory["content"].lower()
        for term in relevant_terms:
            if term in content and term not in found_relevant_terms:
                found_relevant_terms.append(term)
    
    # Should find at least some of the relevant terms in memories
    assert len(found_relevant_terms) > 0

@pytest.mark.asyncio
async def test_real_time_updates_during_task_processing(agent_coordinator):
    """Test that real-time updates are broadcast during task processing"""
    # Get the mocked broadcast functions
    from ai_service.routers.websocket_router import broadcast_task_update, broadcast_network_update
    
    # Submit a task
    task_description = "Create an A/B test for our welcome email series."
    task_context = {"audience": "new_users", "goal": "increase activation"}
    
    # Submit the task
    task_id = await agent_coordinator.submit_task(
        network_id=TEST_NETWORK_ID,
        task=task_description,
        context=task_context
    )
    
    # Process the task
    await agent_coordinator.process_task(TEST_NETWORK_ID, task_id)
    
    # Verify that broadcast_task_update was called multiple times
    assert broadcast_task_update.call_count > 0
    
    # Check the types of updates that were broadcast
    update_types = set()
    for call in broadcast_task_update.call_args_list:
        args, kwargs = call
        update_types.add(kwargs["update_type"])
    
    # Should have multiple types of updates
    assert "task_started" in update_types
    assert "subtask_started" in update_types or "agent_status_change" in update_types
    assert "task_completed" in update_types or "subtask_completed" in update_types
    
    # Verify that broadcast_network_update was called
    assert broadcast_network_update.call_count > 0

@pytest.mark.asyncio
async def test_task_delegation_and_coordination(agent_coordinator):
    """Test that the coordinator properly delegates subtasks to specialized agents"""
    # Submit a task
    task_description = "Design a re-engagement campaign for churned customers."
    task_context = {
        "churn_definition": "inactive for 90+ days",
        "customer_segments": ["free_tier", "basic", "premium"],
        "available_incentives": ["discount", "feature_unlock", "extended_trial"]
    }
    
    # Submit the task
    task_id = await agent_coordinator.submit_task(
        network_id=TEST_NETWORK_ID,
        task=task_description,
        context=task_context
    )
    
    # Process the task
    await agent_coordinator.process_task(TEST_NETWORK_ID, task_id)
    
    # Get the task result
    task = await agent_coordinator.get_task(task_id)
    
    # Verify subtasks were created and assigned to appropriate agents
    subtasks_by_agent = {}
    for entry in task["history"]:
        if entry.get("type") == "subtask_assigned":
            agent_id = entry.get("agent_id")
            if agent_id not in subtasks_by_agent:
                subtasks_by_agent[agent_id] = []
            subtasks_by_agent[agent_id].append(entry.get("description"))
    
    # Each specialized agent should have at least one subtask
    assert TEST_CONTENT_AGENT_ID in subtasks_by_agent
    assert TEST_ANALYTICS_AGENT_ID in subtasks_by_agent
    assert TEST_PERSONALIZATION_AGENT_ID in subtasks_by_agent
    
    # Verify the coordinator synthesized the results
    synthesis_entries = [
        entry for entry in task["history"] 
        if entry.get("type") == "result" and entry.get("agent_id") == TEST_COORDINATOR_ID
    ]
    assert len(synthesis_entries) > 0