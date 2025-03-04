"""
Tests for Vector Embedding integration

This module contains tests for the vector embedding functionality
used in the AI Mesh Network for semantic memory search.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from ..implementations.memory.vector_embeddings import VectorEmbeddingService, get_vector_embedding_service
from ..utils.redis_client import RedisClient
from ..utils.llm_client import LLMClient

# Test data
TEST_NETWORK_ID = "test_network_12345678"
TEST_MEMORY_ID = "memory_12345678"
TEST_CONTENT = "This is a test memory about vector embeddings and semantic search capabilities."

# Sample embedding vectors (low dimension for testing)
SAMPLE_EMBEDDING_1 = [0.1, 0.2, 0.3, 0.4, 0.5]
SAMPLE_EMBEDDING_2 = [0.2, 0.3, 0.4, 0.5, 0.6]
SAMPLE_EMBEDDING_3 = [0.7, 0.8, 0.1, 0.2, 0.3]

@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    redis_client = AsyncMock(spec=RedisClient)
    
    # Mock data storage
    data_store = {}
    hash_store = {}
    
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
    
    async def mock_hset(key, mapping):
        if key not in hash_store:
            hash_store[key] = {}
        hash_store[key].update(mapping)
        return True
    
    async def mock_hkeys(key):
        if key not in hash_store:
            return []
        return list(hash_store[key].keys())
    
    async def mock_hdel(key, field):
        if key in hash_store and field in hash_store[key]:
            del hash_store[key][field]
            return 1
        return 0
    
    # Assign mocked methods
    redis_client.get = mock_get
    redis_client.set = mock_set
    redis_client.delete = mock_delete
    redis_client.hset = mock_hset
    redis_client.hkeys = mock_hkeys
    redis_client.hdel = mock_hdel
    
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
        
        # Execute runs all commands and returns results
        async def pipe_execute():
            results = []
            for cmd in commands:
                if cmd[0] == "get":
                    results.append(data_store.get(cmd[1]))
                elif cmd[0] == "set":
                    data_store[cmd[1]] = cmd[2]
                    results.append(True)
            return results
        
        # Assign methods
        pipeline.get = pipe_get
        pipeline.set = pipe_set
        pipeline.execute = pipe_execute
        
        return pipeline
    
    redis_client.pipeline = mock_pipeline
    
    return redis_client

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    llm_client = AsyncMock(spec=LLMClient)
    
    # Mock get_embedding method
    async def mock_get_embedding(text, model="text-embedding-3-small"):
        # Generate deterministic but different embeddings for different texts
        if "vector" in text.lower() and "embedding" in text.lower():
            embedding = SAMPLE_EMBEDDING_1
        elif "semantic" in text.lower() and "search" in text.lower():
            embedding = SAMPLE_EMBEDDING_2
        else:
            embedding = SAMPLE_EMBEDDING_3
            
        return {
            "embedding": embedding,
            "model": model,
            "provider": "openai",
            "usage": {"prompt_tokens": 10, "total_tokens": 10}
        }
    
    # Assign mocked methods
    llm_client.get_embedding = mock_get_embedding
    
    return llm_client

@pytest.fixture
def vector_service(mock_redis_client, mock_llm_client):
    """Create a VectorEmbeddingService instance with mocked dependencies"""
    service = VectorEmbeddingService()
    service.redis = mock_redis_client
    service.llm_client = mock_llm_client
    
    # Override embedding_dimension for testing
    service.embedding_dimension = 5
    
    return service

# Tests
@pytest.mark.asyncio
async def test_generate_embedding(vector_service):
    """Test generating embedding vector for text"""
    # Generate embedding
    embedding = await vector_service.generate_embedding(TEST_CONTENT)
    
    # Verify
    assert embedding == SAMPLE_EMBEDDING_1
    assert len(embedding) == 5

@pytest.mark.asyncio
async def test_index_memory_item(vector_service):
    """Test indexing a memory item with vector embedding"""
    # Index memory item
    result = await vector_service.index_memory_item(
        network_id=TEST_NETWORK_ID,
        memory_id=TEST_MEMORY_ID,
        content=TEST_CONTENT
    )
    
    # Verify
    assert result is True
    
    # Check that embedding was stored in Redis
    vector_key = f"ai_mesh:vector_index:{TEST_NETWORK_ID}:{TEST_MEMORY_ID}"
    stored_embedding = await vector_service.redis.get(vector_key)
    
    assert stored_embedding is not None
    assert json.loads(stored_embedding) == SAMPLE_EMBEDDING_1
    
    # Check mapping was updated
    mapping_key = f"ai_mesh:vector_mapping:{TEST_NETWORK_ID}"
    memory_ids = await vector_service.redis.hkeys(mapping_key)
    
    assert TEST_MEMORY_ID in memory_ids

@pytest.mark.asyncio
async def test_remove_memory_embedding(vector_service):
    """Test removing a memory embedding"""
    # First index memory item
    await vector_service.index_memory_item(
        network_id=TEST_NETWORK_ID,
        memory_id=TEST_MEMORY_ID,
        content=TEST_CONTENT
    )
    
    # Then remove it
    result = await vector_service.remove_memory_embedding(
        network_id=TEST_NETWORK_ID,
        memory_id=TEST_MEMORY_ID
    )
    
    # Verify
    assert result is True
    
    # Check that embedding was removed from Redis
    vector_key = f"ai_mesh:vector_index:{TEST_NETWORK_ID}:{TEST_MEMORY_ID}"
    stored_embedding = await vector_service.redis.get(vector_key)
    
    assert stored_embedding is None
    
    # Check mapping was updated
    mapping_key = f"ai_mesh:vector_mapping:{TEST_NETWORK_ID}"
    memory_ids = await vector_service.redis.hkeys(mapping_key)
    
    assert TEST_MEMORY_ID not in memory_ids

@pytest.mark.asyncio
async def test_cosine_similarity(vector_service):
    """Test calculating cosine similarity between vectors"""
    # Calculate similarity between similar vectors
    similarity_1_2 = vector_service._cosine_similarity(SAMPLE_EMBEDDING_1, SAMPLE_EMBEDDING_2)
    
    # Calculate similarity between dissimilar vectors
    similarity_1_3 = vector_service._cosine_similarity(SAMPLE_EMBEDDING_1, SAMPLE_EMBEDDING_3)
    
    # Verify
    assert 0.0 <= similarity_1_2 <= 1.0
    assert 0.0 <= similarity_1_3 <= 1.0
    assert similarity_1_2 > similarity_1_3  # Similar vectors should have higher similarity

@pytest.mark.asyncio
async def test_search_by_vector_similarity(vector_service):
    """Test searching memories by vector similarity"""
    # Index test memories
    await vector_service.index_memory_item(
        network_id=TEST_NETWORK_ID,
        memory_id="memory_1",
        content="This is a test memory about vector embeddings."
    )
    
    await vector_service.index_memory_item(
        network_id=TEST_NETWORK_ID,
        memory_id="memory_2",
        content="This is a test memory about semantic search."
    )
    
    await vector_service.index_memory_item(
        network_id=TEST_NETWORK_ID,
        memory_id="memory_3",
        content="This is an unrelated test memory."
    )
    
    # Search for memories similar to a query about embeddings
    similar_memories = await vector_service.search_by_vector_similarity(
        network_id=TEST_NETWORK_ID,
        query="Tell me about vector embeddings",
        limit=10
    )
    
    # Verify
    assert len(similar_memories) > 0
    
    # Memory 1 should be at the top (most similar)
    assert similar_memories[0]["memory_id"] == "memory_1"
    
    # Each memory should have a similarity score
    for memory in similar_memories:
        assert "similarity" in memory
        assert 0.0 <= memory["similarity"] <= 1.0

@pytest.mark.asyncio
async def test_enhanced_memory_search(vector_service):
    """Test the enhanced memory search with vector embeddings"""
    # Set up test data in Redis
    memory_1 = {
        "id": "memory_1",
        "network_id": TEST_NETWORK_ID,
        "type": "fact",
        "content": "This is a test memory about vector embeddings.",
        "confidence": 0.9,
        "created_at": "2023-01-01T00:00:00Z",
        "metadata": {}
    }
    
    memory_2 = {
        "id": "memory_2",
        "network_id": TEST_NETWORK_ID,
        "type": "fact",
        "content": "This is a test memory about semantic search.",
        "confidence": 0.8,
        "created_at": "2023-01-02T00:00:00Z",
        "metadata": {}
    }
    
    memory_3 = {
        "id": "memory_3",
        "network_id": TEST_NETWORK_ID,
        "type": "context",
        "content": "This is an unrelated test memory.",
        "confidence": 0.7,
        "created_at": "2023-01-03T00:00:00Z",
        "metadata": {}
    }
    
    # Store test memories in Redis
    await vector_service.redis.set(f"ai_mesh:memory:memory_1", json.dumps(memory_1))
    await vector_service.redis.set(f"ai_mesh:memory:memory_2", json.dumps(memory_2))
    await vector_service.redis.set(f"ai_mesh:memory:memory_3", json.dumps(memory_3))
    
    # Index test memories
    await vector_service.index_memory_item(
        network_id=TEST_NETWORK_ID,
        memory_id="memory_1",
        content=memory_1["content"]
    )
    
    await vector_service.index_memory_item(
        network_id=TEST_NETWORK_ID,
        memory_id="memory_2",
        content=memory_2["content"]
    )
    
    await vector_service.index_memory_item(
        network_id=TEST_NETWORK_ID,
        memory_id="memory_3",
        content=memory_3["content"]
    )
    
    # Search for memories with type filter
    search_results = await vector_service.enhanced_memory_search(
        network_id=TEST_NETWORK_ID,
        query="Vector embeddings",
        memory_type="fact",
        limit=10
    )
    
    # Verify
    assert len(search_results) > 0
    
    # All results should be of type "fact"
    for memory in search_results:
        assert memory["type"] == "fact"
    
    # Memory 1 should be at the top (most similar)
    assert search_results[0]["id"] == "memory_1"
    
    # Each memory should have a similarity score
    for memory in search_results:
        assert "similarity_score" in memory
        assert 0.0 <= memory["similarity_score"] <= 1.0

@pytest.mark.asyncio
async def test_singleton_instance():
    """Test that get_vector_embedding_service returns a singleton instance"""
    # Get instance twice
    service1 = get_vector_embedding_service()
    service2 = get_vector_embedding_service()
    
    # Verify
    assert service1 is service2