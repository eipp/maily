"""
Memory Indexing System for AI Mesh Network

This module provides a memory indexing system for efficient memory retrieval
based on content relevance, type, and timestamp.
"""

import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
import logging
from datetime import datetime

from ...utils.redis_client import get_redis_client

logger = logging.getLogger("ai_service.implementations.memory.memory_indexing")

# Redis key prefixes
MEMORY_KEY_PREFIX = "ai_mesh:memory:"
MEMORY_INDEX_PREFIX = "ai_mesh:memory_index:"
MEMORY_EXPIRATION_PREFIX = "ai_mesh:memory_expiration:"
MEMORY_TYPE_INDEX_PREFIX = "ai_mesh:memory_type_index:"

# Memory types
MEMORY_TYPES = ["fact", "context", "decision", "feedback"]

class MemoryIndexingSystem:
    """Memory indexing system for efficient memory retrieval"""
    
    def __init__(self):
        """Initialize the memory indexing system"""
        self.redis = get_redis_client()
        
    async def add_memory_to_index(
        self, 
        network_id: str, 
        memory_id: str, 
        memory_type: str, 
        content: str, 
        metadata: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Add a memory item to the indexing system
        
        Args:
            network_id: ID of the network
            memory_id: ID of the memory item
            memory_type: Type of memory (fact, context, decision, feedback)
            content: Content of the memory item
            metadata: Metadata for the memory item
            ttl: Time-to-live in seconds (if None, memory won't expire)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract keywords from content
            keywords = self._extract_keywords(content)
            
            # Create pipeline for batch operations
            pipeline = self.redis.pipeline()
            
            # Add to type index
            type_index_key = f"{MEMORY_TYPE_INDEX_PREFIX}{network_id}:{memory_type}"
            pipeline.lpush(type_index_key, memory_id)
            
            # Add to keyword indices
            for keyword in keywords:
                keyword_index_key = f"{MEMORY_INDEX_PREFIX}{network_id}:{keyword}"
                pipeline.lpush(keyword_index_key, memory_id)
            
            # Add to timestamp index (using sorted set with score as timestamp)
            timestamp_index_key = f"{MEMORY_INDEX_PREFIX}{network_id}:timestamp"
            current_time = time.time()
            pipeline.zadd(timestamp_index_key, {memory_id: current_time})
            
            # Set expiration if TTL provided
            if ttl is not None and ttl > 0:
                # Calculate expiration timestamp
                expiration_time = current_time + ttl
                
                # Store expiration info
                expiration_key = f"{MEMORY_EXPIRATION_PREFIX}{network_id}"
                pipeline.zadd(expiration_key, {memory_id: expiration_time})
                
                # Start background expiration check if not already running
                asyncio.create_task(self._check_expired_memories(network_id))
            
            # Execute all operations
            await pipeline.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add memory to index: {e}")
            return False
    
    async def search_memories(
        self, 
        network_id: str, 
        query: Optional[str] = None, 
        memory_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "recency",  # Options: recency, relevance, semantic
        use_vector_search: bool = True  # Whether to use vector-based search
    ) -> List[str]:
        """
        Search for memory items using the indexing system
        
        Args:
            network_id: ID of the network
            query: Search query (keywords)
            memory_type: Filter by memory type
            limit: Maximum number of results
            offset: Offset for pagination
            sort_by: Sort order (recency, relevance, or semantic)
            use_vector_search: Whether to use vector-based search for semantic option
            
        Returns:
            List of memory IDs matching the search criteria
        """
        try:
            # Use semantic search if specified
            if query and sort_by == "semantic" and use_vector_search:
                try:
                    # Import vector embedding service here to avoid circular imports
                    from .vector_embeddings import get_vector_embedding_service
                    vector_service = get_vector_embedding_service()
                    
                    # Get similar memory IDs
                    similar_memories = await vector_service.search_by_vector_similarity(
                        network_id=network_id,
                        query=query,
                        limit=limit * 2  # Get more than needed to allow for filtering
                    )
                    
                    # Extract memory IDs
                    memory_ids = [item["memory_id"] for item in similar_memories]
                    
                    # Filter by type if specified
                    if memory_type:
                        # Get memory details to check types
                        pipeline = self.redis.pipeline()
                        for mem_id in memory_ids:
                            memory_key = f"{MEMORY_KEY_PREFIX}{mem_id}"
                            pipeline.get(memory_key)
                        
                        memory_data_list = await pipeline.execute()
                        
                        # Filter by type
                        filtered_memory_ids = []
                        for i, mem_id in enumerate(memory_ids):
                            if memory_data_list[i]:
                                try:
                                    memory_data = json.loads(memory_data_list[i])
                                    if memory_data.get("type") == memory_type:
                                        filtered_memory_ids.append(mem_id)
                                except:
                                    pass
                        
                        memory_ids = filtered_memory_ids
                    
                    # Apply pagination
                    return memory_ids[offset:offset + limit]
                
                except Exception as e:
                    logger.error(f"Vector search failed, falling back to keyword search: {e}")
                    # Fall back to keyword search
                    sort_by = "relevance"
            
            memory_ids = None
            
            # Filter by type if specified
            if memory_type:
                type_index_key = f"{MEMORY_TYPE_INDEX_PREFIX}{network_id}:{memory_type}"
                memory_ids_by_type = await self.redis.lrange(type_index_key, 0, -1)
                memory_ids = set(memory_ids_by_type)
            
            # Filter by query if specified
            if query:
                # Extract keywords from query
                keywords = self._extract_keywords(query)
                
                # Get memory IDs for each keyword
                keyword_memory_ids = []
                for keyword in keywords:
                    keyword_index_key = f"{MEMORY_INDEX_PREFIX}{network_id}:{keyword}"
                    ids = await self.redis.lrange(keyword_index_key, 0, -1)
                    if ids:
                        keyword_memory_ids.append(set(ids))
                
                # Find intersection of memory IDs
                if keyword_memory_ids:
                    query_memory_ids = set.intersection(*keyword_memory_ids)
                    
                    # Combine with type filter if specified
                    if memory_ids is not None:
                        memory_ids = memory_ids.intersection(query_memory_ids)
                    else:
                        memory_ids = query_memory_ids
            
            # If no filtering applied, get all memories sorted by timestamp
            if memory_ids is None:
                timestamp_index_key = f"{MEMORY_INDEX_PREFIX}{network_id}:timestamp"
                if sort_by == "recency":
                    # Get newest first
                    memory_ids = await self.redis.zrevrange(timestamp_index_key, 0, -1)
                else:
                    # Get all and sort by relevance later
                    memory_ids = await self.redis.zrange(timestamp_index_key, 0, -1)
                memory_ids = set(memory_ids)
            
            # Convert to list
            result = list(memory_ids)
            
            # Apply sorting if using relevance
            if query and sort_by == "relevance" and result:
                # Get memory contents to calculate relevance
                memory_contents = {}
                pipeline = self.redis.pipeline()
                
                for mem_id in result:
                    memory_key = f"{MEMORY_KEY_PREFIX}{mem_id}"
                    pipeline.get(memory_key)
                
                memory_data_list = await pipeline.execute()
                
                # Calculate relevance scores
                relevance_scores = []
                for i, mem_id in enumerate(result):
                    if memory_data_list[i]:
                        memory_data = json.loads(memory_data_list[i])
                        # Note: _calculate_relevance is now async
                        relevance = await self._calculate_relevance(query, memory_data["content"])
                        relevance_scores.append((mem_id, relevance))
                
                # Sort by relevance score (descending)
                relevance_scores.sort(key=lambda x: x[1], reverse=True)
                result = [mem_id for mem_id, _ in relevance_scores]
            
            # Apply pagination
            return result[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    async def remove_memory_from_index(self, network_id: str, memory_id: str) -> bool:
        """
        Remove a memory item from the indexing system
        
        Args:
            network_id: ID of the network
            memory_id: ID of the memory item
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get memory item to extract its type and content
            memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
            memory_data = await self.redis.get(memory_key)
            
            if not memory_data:
                return False
            
            memory = json.loads(memory_data)
            memory_type = memory.get("type", "fact")
            content = memory.get("content", "")
            
            # Extract keywords from content
            keywords = self._extract_keywords(content)
            
            # Create pipeline for batch operations
            pipeline = self.redis.pipeline()
            
            # Remove from type index
            type_index_key = f"{MEMORY_TYPE_INDEX_PREFIX}{network_id}:{memory_type}"
            pipeline.lrem(type_index_key, 0, memory_id)
            
            # Remove from keyword indices
            for keyword in keywords:
                keyword_index_key = f"{MEMORY_INDEX_PREFIX}{network_id}:{keyword}"
                pipeline.lrem(keyword_index_key, 0, memory_id)
            
            # Remove from timestamp index
            timestamp_index_key = f"{MEMORY_INDEX_PREFIX}{network_id}:timestamp"
            pipeline.zrem(timestamp_index_key, memory_id)
            
            # Remove from expiration index
            expiration_key = f"{MEMORY_EXPIRATION_PREFIX}{network_id}"
            pipeline.zrem(expiration_key, memory_id)
            
            # Execute all operations
            await pipeline.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove memory from index: {e}")
            return False
    
    async def get_memory_stats(self, network_id: str) -> Dict[str, Any]:
        """
        Get statistics about memory items for a network
        
        Args:
            network_id: ID of the network
            
        Returns:
            Dictionary with memory statistics
        """
        try:
            stats = {}
            
            # Get counts by type
            pipeline = self.redis.pipeline()
            
            # Add commands to get count by type
            for memory_type in MEMORY_TYPES:
                type_index_key = f"{MEMORY_TYPE_INDEX_PREFIX}{network_id}:{memory_type}"
                pipeline.llen(type_index_key)
            
            # Get total count
            timestamp_index_key = f"{MEMORY_INDEX_PREFIX}{network_id}:timestamp"
            pipeline.zcard(timestamp_index_key)
            
            # Get expiration queue size
            expiration_key = f"{MEMORY_EXPIRATION_PREFIX}{network_id}"
            pipeline.zcard(expiration_key)
            
            # Execute pipeline
            results = await pipeline.execute()
            
            # Process results
            for i, memory_type in enumerate(MEMORY_TYPES):
                stats[f"{memory_type}_count"] = results[i] or 0
            
            stats["total_count"] = results[len(MEMORY_TYPES)] or 0
            stats["expiring_count"] = results[len(MEMORY_TYPES) + 1] or 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    async def _check_expired_memories(self, network_id: str):
        """
        Check for expired memories and remove them
        
        Args:
            network_id: ID of the network
        """
        try:
            # Get expiration key
            expiration_key = f"{MEMORY_EXPIRATION_PREFIX}{network_id}"
            
            # Current time
            current_time = time.time()
            
            # Get expired memories (score <= current time)
            expired_memories = await self.redis.zrangebyscore(
                expiration_key, 
                0, 
                current_time
            )
            
            if not expired_memories:
                return
            
            logger.info(f"Found {len(expired_memories)} expired memories to remove")
            
            # Remove each expired memory
            for memory_id in expired_memories:
                # Remove from index
                await self.remove_memory_from_index(network_id, memory_id)
                
                # Remove the actual memory
                memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                await self.redis.delete(memory_key)
            
            logger.info(f"Successfully removed {len(expired_memories)} expired memories")
            
        except Exception as e:
            logger.error(f"Error checking expired memories: {e}")
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """
        Extract keywords from text for indexing
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            Set of keywords
        """
        # Simple keyword extraction - split by spaces and punctuation
        # In a real implementation, this would use NLP techniques
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        for char in ",.!?;:()[]{}\"'":
            text = text.replace(char, " ")
        
        # Split by spaces and filter out short words
        words = [word for word in text.split() if len(word) > 3]
        
        # Return unique keywords
        return set(words)
    
    async def _calculate_relevance(self, query: str, content: str) -> float:
        """
        Calculate relevance score between query and content
        
        Args:
            query: Search query
            content: Memory content
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        # Use vector embeddings for semantic similarity
        try:
            # Import vector embedding service here to avoid circular imports
            from .vector_embeddings import get_vector_embedding_service
            vector_service = get_vector_embedding_service()
            
            # Generate embeddings
            query_embedding = await vector_service.generate_embedding(query)
            content_embedding = await vector_service.generate_embedding(content)
            
            # Calculate cosine similarity
            similarity = vector_service._cosine_similarity(query_embedding, content_embedding)
            
            return similarity
        
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            
            # Fall back to keyword-based relevance as backup
            query_keywords = self._extract_keywords(query)
            content_keywords = self._extract_keywords(content)
            
            if not query_keywords or not content_keywords:
                return 0.0
            
            # Calculate Jaccard similarity
            intersection = len(query_keywords.intersection(content_keywords))
            union = len(query_keywords.union(content_keywords))
            
            return intersection / union if union > 0 else 0.0

# Singleton instance
_memory_indexing_instance = None

def get_memory_indexing_system() -> MemoryIndexingSystem:
    """Get the singleton instance of MemoryIndexingSystem"""
    global _memory_indexing_instance
    if _memory_indexing_instance is None:
        _memory_indexing_instance = MemoryIndexingSystem()
    return _memory_indexing_instance