"""
Vector Embedding Integration for AI Mesh Network

This module enhances the memory indexing system with proper vector embeddings
for improved semantic search capabilities and relevance matching.
"""

import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set, Union
import asyncio
from datetime import datetime

from packages.database.src.redis import redis_client, get, set, delete
from ...utils.llm_client import get_llm_client

logger = logging.getLogger("ai_service.implementations.memory.vector_embeddings")

# Redis key prefixes
MEMORY_KEY_PREFIX = "ai_mesh:memory:"
VECTOR_INDEX_PREFIX = "ai_mesh:vector_index:"
VECTOR_MAPPING_PREFIX = "ai_mesh:vector_mapping:"

class VectorEmbeddingService:
    """
    Vector embedding service for semantic memory search
    
    This service generates and manages vector embeddings for memory items,
    enabling semantic search capabilities beyond simple keyword matching.
    """
    
    def __init__(self):
        """Initialize the vector embedding service"""
        self.redis = redis_client  # Use the standardized Redis client
        self.llm_client = get_llm_client()
        self.embedding_dimension = 1536  # Default dimension for embeddings
        self.embedding_batch_size = 16  # Process this many embeddings at once
        self.similarity_threshold = 0.75  # Default similarity threshold
        
        # Cache for frequently used embeddings
        self.embedding_cache = {}
        self.max_cache_size = 1000
        
        # Models available for embeddings
        self.embedding_models = {
            "default": "text-embedding-3-small",
            "high_quality": "text-embedding-3-large",
            "fallback": "text-embedding-ada-002"
        }
    
    async def generate_embedding(
        self, 
        text: str, 
        model: str = "default"
    ) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: The text to generate embedding for
            model: Embedding model to use (default, high_quality, or fallback)
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Check if in cache
            cache_key = f"{model}:{text}"
            if cache_key in self.embedding_cache:
                return self.embedding_cache[cache_key]
                
            # Get actual model name
            model_name = self.embedding_models.get(model, self.embedding_models["default"])
            
            # Generate embedding using LLM client
            embedding_result = await self.llm_client.get_embedding(
                text=text,
                model=model_name
            )
            
            # Extract embedding vector
            embedding = embedding_result.get("embedding", [])
            
            # Cache the result
            if len(self.embedding_cache) >= self.max_cache_size:
                # Remove a random item to keep cache size in check
                keys = list(self.embedding_cache.keys())
                if keys:
                    del self.embedding_cache[keys[0]]
            
            self.embedding_cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            
            # Try fallback model if primary failed
            if model != "fallback":
                logger.info(f"Trying fallback embedding model")
                return await self.generate_embedding(text, model="fallback")
            
            # Return empty embedding as last resort
            return []
    
    async def index_memory_item(
        self, 
        network_id: str,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Generate and store embedding for a memory item
        
        Args:
            network_id: ID of the network
            memory_id: ID of the memory item
            content: Content of the memory item
            metadata: Optional metadata for contextualizing the embedding
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding
            embedding = await self.generate_embedding(content)
            
            if not embedding:
                logger.error(f"Failed to generate embedding for memory {memory_id}")
                return False
            
            # Store embedding in Redis using standardized client
            vector_key = f"{VECTOR_INDEX_PREFIX}{network_id}:{memory_id}"
            await set(vector_key, json.dumps(embedding))
            
            # Update mapping for quick lookup
            mapping_key = f"{VECTOR_MAPPING_PREFIX}{network_id}"
            mapping_dict = {memory_id: datetime.utcnow().timestamp()}
            await self.redis.hset(mapping_key, memory_id, datetime.utcnow().timestamp())
            
            logger.debug(f"Indexed memory {memory_id} with vector embedding")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing memory item: {e}")
            return False
    
    async def batch_index_memory_items(
        self,
        network_id: str,
        memory_items: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """
        Generate and store embeddings for multiple memory items
        
        Args:
            network_id: ID of the network
            memory_items: List of memory items to index (each with id and content)
            
        Returns:
            Dictionary mapping memory_id to success status
        """
        results = {}
        
        # Process in batches for efficiency
        for i in range(0, len(memory_items), self.embedding_batch_size):
            batch = memory_items[i:i + self.embedding_batch_size]
            
            # Process batch concurrently
            tasks = []
            for item in batch:
                memory_id = item.get("id")
                content = item.get("content", "")
                metadata = item.get("metadata", {})
                
                if memory_id and content:
                    task = self.index_memory_item(
                        network_id=network_id,
                        memory_id=memory_id,
                        content=content,
                        metadata=metadata
                    )
                    tasks.append(task)
            
            # Wait for all tasks in batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for j, item in enumerate(batch):
                memory_id = item.get("id")
                if memory_id:
                    result = batch_results[j]
                    # Check if exception occurred
                    if isinstance(result, Exception):
                        logger.error(f"Error indexing memory {memory_id}: {result}")
                        results[memory_id] = False
                    else:
                        results[memory_id] = result
        
        return results
    
    async def remove_memory_embedding(
        self,
        network_id: str,
        memory_id: str
    ) -> bool:
        """
        Remove embedding for a memory item
        
        Args:
            network_id: ID of the network
            memory_id: ID of the memory item
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove embedding vector using standardized client
            vector_key = f"{VECTOR_INDEX_PREFIX}{network_id}:{memory_id}"
            await delete(vector_key)
            
            # Remove from mapping
            mapping_key = f"{VECTOR_MAPPING_PREFIX}{network_id}"
            await self.redis.hdel(mapping_key, memory_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing memory embedding: {e}")
            return False
    
    async def search_by_vector_similarity(
        self,
        network_id: str,
        query: str,
        limit: int = 10,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for memory items by vector similarity
        
        Args:
            network_id: ID of the network
            query: Query text
            limit: Maximum number of results
            threshold: Similarity threshold (0.0 to 1.0, higher is more similar)
            
        Returns:
            List of memory IDs with similarity scores
        """
        try:
            if not threshold:
                threshold = self.similarity_threshold
            
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return []
            
            # Get all memory IDs for this network
            mapping_key = f"{VECTOR_MAPPING_PREFIX}{network_id}"
            memory_ids = await self.redis.hkeys(mapping_key)
            
            if not memory_ids:
                return []
            
            # Calculate similarity for each memory item
            similarities = []
            
            # Process in batches for efficiency
            for i in range(0, len(memory_ids), self.embedding_batch_size):
                batch_ids = memory_ids[i:i + self.embedding_batch_size]
                
                # Get embeddings for batch
                pipeline = self.redis.pipeline()
                for memory_id in batch_ids:
                    vector_key = f"{VECTOR_INDEX_PREFIX}{network_id}:{memory_id}"
                    pipeline.get(vector_key)
                
                # Execute batch
                batch_results = await pipeline.execute()
                
                # Calculate similarities
                for j, memory_id in enumerate(batch_ids):
                    if batch_results[j]:
                        try:
                            memory_embedding = json.loads(batch_results[j])
                            similarity = self._cosine_similarity(query_embedding, memory_embedding)
                            
                            if similarity >= threshold:
                                similarities.append({
                                    "memory_id": memory_id,
                                    "similarity": similarity
                                })
                        except Exception as e:
                            logger.error(f"Error processing embedding for {memory_id}: {e}")
            
            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Limit results
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Error searching by vector similarity: {e}")
            return []
    
    async def enhanced_memory_search(
        self,
        network_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Enhanced memory search using vector similarity and metadata
        
        Args:
            network_id: ID of the network
            query: Search query
            memory_type: Optional filter by memory type
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of memory items matching the search criteria
        """
        try:
            # Get similar memory IDs by vector embedding
            similar_memories = await self.search_by_vector_similarity(
                network_id=network_id,
                query=query,
                limit=limit * 2  # Get more than needed to allow for filtering
            )
            
            # Extract memory IDs
            memory_ids = [item["memory_id"] for item in similar_memories]
            
            if not memory_ids:
                return []
            
            # Get full memory items
            pipeline = self.redis.pipeline()
            for memory_id in memory_ids:
                memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                pipeline.get(memory_key)
            
            memory_data_list = await pipeline.execute()
            
            # Process memory items
            results = []
            for i, memory_id in enumerate(memory_ids):
                if memory_data_list[i]:
                    try:
                        memory = json.loads(memory_data_list[i])
                        
                        # Filter by type if specified
                        if memory_type and memory.get("type") != memory_type:
                            continue
                        
                        # Add similarity score
                        memory["similarity_score"] = similar_memories[i]["similarity"]
                        
                        results.append(memory)
                    except Exception as e:
                        logger.error(f"Error processing memory data for {memory_id}: {e}")
            
            # Apply pagination
            return results[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Error in enhanced memory search: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (0.0 to 1.0, higher is more similar)
        """
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

# Singleton instance
_vector_service_instance = None

def get_vector_embedding_service() -> VectorEmbeddingService:
    """Get the singleton instance of VectorEmbeddingService"""
    global _vector_service_instance
    if _vector_service_instance is None:
        _vector_service_instance = VectorEmbeddingService()
    return _vector_service_instance