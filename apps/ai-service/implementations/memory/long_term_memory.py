"""
Long-term memory persistence for AI Mesh Network.

This module provides tiered storage for AI Mesh memory:
- Recent/frequent memories in Redis (hot tier)
- Older memories in PostgreSQL (cold tier)
"""

import logging
import json
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta
import uuid

from ...utils.redis_client import get_redis_client

logger = logging.getLogger("ai_service.implementations.memory.long_term_memory")

# PostgreSQL-related imports
try:
    import asyncpg
    POSTGRES_AVAILABLE = True
except ImportError:
    logger.warning("asyncpg not available. Long-term memory will use Redis only.")
    POSTGRES_AVAILABLE = False

# Constants
MEMORY_KEY_PREFIX = "ai_mesh:memory:"
MEMORY_ACCESS_PREFIX = "ai_mesh:memory_access:"
MEMORY_INDEX_PREFIX = "ai_mesh:memory_index:"
DEFAULT_MAX_MEMORY_AGE_DAYS = 90
DEFAULT_HOT_TIER_TTL = 60 * 60 * 24 * 7  # 7 days

class TieredMemoryStorage:
    """
    Tiered memory storage for AI Mesh Network.
    
    Features:
    - Stores frequently accessed memories in Redis (hot tier)
    - Stores less frequently accessed memories in PostgreSQL (cold tier)
    - Automatically moves memories between tiers based on access patterns
    - Provides memory rotation, pruning, and archiving
    - Supports vector search across both tiers
    """
    
    def __init__(self):
        """Initialize the tiered memory storage."""
        self.redis = None
        self.pg_pool = None
        self.setup_complete = False
        
        # Cache for memory access counts to reduce Redis calls
        self.access_count_cache = {}
        self.network_memory_cache = {}
        self.cache_expiry = {}
        self.max_cache_size = 1000
        self.cache_ttl = 300  # 5 minutes
        
        # Settings
        self.hot_tier_ttl = DEFAULT_HOT_TIER_TTL
        self.memory_rotation_interval = 60 * 60  # 1 hour
        self.memory_pruning_interval = 60 * 60 * 24  # 1 day
        self.access_threshold_hot = 5  # Access count to promote to hot tier
        self.max_memory_age_days = DEFAULT_MAX_MEMORY_AGE_DAYS
    
    async def setup(self, pg_config: Optional[Dict[str, Any]] = None):
        """
        Set up the tiered memory storage.
        
        Args:
            pg_config: PostgreSQL configuration
        """
        if self.setup_complete:
            return
        
        # Get Redis client
        self.redis = await get_redis_client()
        
        # Set up PostgreSQL if available
        if POSTGRES_AVAILABLE and pg_config:
            try:
                # Create connection pool
                self.pg_pool = await asyncpg.create_pool(
                    host=pg_config.get("host", "localhost"),
                    port=pg_config.get("port", 5432),
                    user=pg_config.get("user", "postgres"),
                    password=pg_config.get("password", ""),
                    database=pg_config.get("database", "maily"),
                    min_size=pg_config.get("min_connections", 1),
                    max_size=pg_config.get("max_connections", 10)
                )
                
                # Create table if it doesn't exist
                async with self.pg_pool.acquire() as conn:
                    await conn.execute("""
                    CREATE TABLE IF NOT EXISTS ai_mesh_memories (
                        memory_id TEXT PRIMARY KEY,
                        network_id TEXT NOT NULL,
                        memory_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        confidence FLOAT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        last_accessed TIMESTAMP NOT NULL,
                        access_count INTEGER NOT NULL DEFAULT 0,
                        metadata JSONB,
                        vector REAL[] -- For vector embeddings if used
                    );
                    
                    CREATE INDEX IF NOT EXISTS ai_mesh_memories_network_id_idx 
                    ON ai_mesh_memories(network_id);
                    
                    CREATE INDEX IF NOT EXISTS ai_mesh_memories_last_accessed_idx 
                    ON ai_mesh_memories(last_accessed);
                    
                    CREATE INDEX IF NOT EXISTS ai_mesh_memories_memory_type_idx 
                    ON ai_mesh_memories(memory_type);
                    """)
                
                logger.info("PostgreSQL connection established and tables created")
                
                # Start background tasks
                asyncio.create_task(self._memory_rotation_task())
                asyncio.create_task(self._memory_pruning_task())
                
            except Exception as e:
                logger.error(f"Failed to set up PostgreSQL: {e}")
                self.pg_pool = None
        
        self.setup_complete = True
    
    async def store_memory(
        self,
        memory_id: str,
        network_id: str,
        content: str,
        memory_type: str,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
        vector_embedding: Optional[List[float]] = None,
        force_tier: Optional[str] = None
    ) -> bool:
        """
        Store a memory item in the appropriate tier.
        
        Args:
            memory_id: Unique ID for the memory
            network_id: Network ID
            content: Memory content
            memory_type: Type of memory (fact, context, decision, feedback)
            confidence: Confidence score (0.0 to 1.0)
            metadata: Additional metadata for the memory
            vector_embedding: Vector embedding for semantic search
            force_tier: Force storage in a specific tier ('hot' or 'cold')
            
        Returns:
            True if successful, False otherwise
        """
        if not self.setup_complete:
            await self.setup()
        
        try:
            # Create memory object
            memory = {
                "id": memory_id,
                "network_id": network_id,
                "type": memory_type,
                "content": content,
                "confidence": confidence,
                "created_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "access_count": 1,
                "metadata": metadata or {}
            }
            
            # Determine storage tier
            if force_tier == "cold" and self.pg_pool:
                return await self._store_in_cold_tier(memory, vector_embedding)
            elif force_tier == "hot" or not self.pg_pool:
                return await self._store_in_hot_tier(memory)
            else:
                # Default: store in hot tier
                return await self._store_in_hot_tier(memory)
                
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False
    
    async def _store_in_hot_tier(self, memory: Dict[str, Any]) -> bool:
        """Store memory in Redis (hot tier)"""
        try:
            # Store memory in Redis
            memory_key = f"{MEMORY_KEY_PREFIX}{memory['id']}"
            await self.redis.set(
                memory_key, 
                json.dumps(memory),
                ex=self.hot_tier_ttl
            )
            
            # Initialize access count
            access_key = f"{MEMORY_ACCESS_PREFIX}{memory['id']}"
            await self.redis.set(access_key, "1", ex=self.hot_tier_ttl)
            
            # Add to index for the network
            index_key = f"{MEMORY_INDEX_PREFIX}{memory['network_id']}"
            await self.redis.sadd(index_key, memory['id'])
            await self.redis.expire(index_key, self.hot_tier_ttl)
            
            # Update cache
            self._update_cache(memory)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store in hot tier: {e}")
            return False
    
    async def _store_in_cold_tier(
        self, 
        memory: Dict[str, Any], 
        vector_embedding: Optional[List[float]] = None
    ) -> bool:
        """Store memory in PostgreSQL (cold tier)"""
        if not self.pg_pool:
            logger.warning("PostgreSQL not available, falling back to hot tier")
            return await self._store_in_hot_tier(memory)
            
        try:
            async with self.pg_pool.acquire() as conn:
                # Convert JSON data
                metadata_json = json.dumps(memory.get("metadata", {}))
                created_at = datetime.fromisoformat(memory["created_at"].replace("Z", "+00:00"))
                last_accessed = datetime.fromisoformat(memory["last_accessed"].replace("Z", "+00:00"))
                
                # Insert into database
                if vector_embedding:
                    await conn.execute(
                        """
                        INSERT INTO ai_mesh_memories 
                        (memory_id, network_id, memory_type, content, confidence, 
                         created_at, last_accessed, access_count, metadata, vector)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (memory_id) 
                        DO UPDATE SET 
                            content = EXCLUDED.content,
                            confidence = EXCLUDED.confidence,
                            last_accessed = EXCLUDED.last_accessed,
                            access_count = ai_mesh_memories.access_count + 1,
                            metadata = EXCLUDED.metadata,
                            vector = EXCLUDED.vector
                        """,
                        memory["id"], memory["network_id"], memory["type"],
                        memory["content"], memory["confidence"],
                        created_at, last_accessed, memory.get("access_count", 1),
                        metadata_json, vector_embedding
                    )
                else:
                    await conn.execute(
                        """
                        INSERT INTO ai_mesh_memories 
                        (memory_id, network_id, memory_type, content, confidence, 
                         created_at, last_accessed, access_count, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (memory_id) 
                        DO UPDATE SET 
                            content = EXCLUDED.content,
                            confidence = EXCLUDED.confidence,
                            last_accessed = EXCLUDED.last_accessed,
                            access_count = ai_mesh_memories.access_count + 1,
                            metadata = EXCLUDED.metadata
                        """,
                        memory["id"], memory["network_id"], memory["type"],
                        memory["content"], memory["confidence"],
                        created_at, last_accessed, memory.get("access_count", 1),
                        metadata_json
                    )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to store in cold tier: {e}")
            return False
    
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a memory item from any tier.
        
        Args:
            memory_id: Memory ID to retrieve
            
        Returns:
            Memory object if found, None otherwise
        """
        if not self.setup_complete:
            await self.setup()
        
        try:
            # First check Redis (hot tier)
            memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
            memory_data = await self.redis.get(memory_key)
            
            if memory_data:
                # Memory found in hot tier
                memory = json.loads(memory_data)
                
                # Update access count and last accessed time
                await self._increment_access_count(memory_id)
                
                return memory
            
            # Not in hot tier, check cold tier if available
            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                        UPDATE ai_mesh_memories
                        SET last_accessed = $1, access_count = access_count + 1
                        WHERE memory_id = $2
                        RETURNING *
                        """,
                        datetime.utcnow(), memory_id
                    )
                    
                    if row:
                        # Convert row to dictionary
                        memory = {
                            "id": row["memory_id"],
                            "network_id": row["network_id"],
                            "type": row["memory_type"],
                            "content": row["content"],
                            "confidence": row["confidence"],
                            "created_at": row["created_at"].isoformat(),
                            "last_accessed": row["last_accessed"].isoformat(),
                            "access_count": row["access_count"],
                            "metadata": row["metadata"] if row["metadata"] else {}
                        }
                        
                        # Check if memory should be promoted to hot tier
                        if row["access_count"] >= self.access_threshold_hot:
                            await self._promote_to_hot_tier(memory)
                        
                        return memory
            
            # Memory not found in any tier
            return None
            
        except Exception as e:
            logger.error(f"Failed to get memory: {e}")
            return None
    
    async def get_network_memories(
        self,
        network_id: str,
        memory_type: Optional[str] = None,
        limit: int = 50,
        skip_promotion: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get memories for a network.
        
        Args:
            network_id: Network ID
            memory_type: Optional filter by memory type
            limit: Maximum number of memories to return
            skip_promotion: Skip promotion from cold to hot tier
            
        Returns:
            List of memory objects
        """
        if not self.setup_complete:
            await self.setup()
            
        # Check cache first
        cache_key = f"{network_id}:{memory_type or 'all'}:{limit}"
        if cache_key in self.network_memory_cache and time.time() < self.cache_expiry.get(cache_key, 0):
            return self.network_memory_cache[cache_key]
        
        memories = []
        memory_ids = set()
        
        try:
            # First get from hot tier (Redis)
            index_key = f"{MEMORY_INDEX_PREFIX}{network_id}"
            hot_memory_ids = await self.redis.smembers(index_key)
            
            if hot_memory_ids:
                # Use pipeline for batch retrieval
                pipeline = self.redis.pipeline()
                for memory_id in hot_memory_ids:
                    memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                    pipeline.get(memory_key)
                
                # Execute pipeline
                hot_memory_data = await pipeline.execute()
                
                # Process results
                for data in hot_memory_data:
                    if not data:
                        continue
                    
                    memory = json.loads(data)
                    
                    # Filter by type if specified
                    if memory_type and memory["type"] != memory_type:
                        continue
                    
                    memory_ids.add(memory["id"])
                    memories.append(memory)
                    
                    # Update access counts in batch later
                    if not skip_promotion:
                        await self._increment_access_count(memory["id"])
            
            # Then check cold tier (PostgreSQL) if available
            if self.pg_pool and len(memories) < limit:
                # Calculate how many more memories we need
                remaining = limit - len(memories)
                
                async with self.pg_pool.acquire() as conn:
                    query = """
                    SELECT * FROM ai_mesh_memories
                    WHERE network_id = $1
                    """
                    params = [network_id]
                    
                    if memory_type:
                        query += " AND memory_type = $2"
                        params.append(memory_type)
                    
                    # Exclude memories already retrieved from hot tier
                    if memory_ids:
                        placeholders = ", ".join(f"${i+len(params)+1}" for i in range(len(memory_ids)))
                        query += f" AND memory_id NOT IN ({placeholders})"
                        params.extend(memory_ids)
                    
                    query += " ORDER BY last_accessed DESC LIMIT $" + str(len(params) + 1)
                    params.append(remaining)
                    
                    rows = await conn.fetch(query, *params)
                    
                    # Process results
                    promote_ids = []
                    for row in rows:
                        memory = {
                            "id": row["memory_id"],
                            "network_id": row["network_id"],
                            "type": row["memory_type"],
                            "content": row["content"],
                            "confidence": row["confidence"],
                            "created_at": row["created_at"].isoformat(),
                            "last_accessed": row["last_accessed"].isoformat(),
                            "access_count": row["access_count"],
                            "metadata": row["metadata"] if row["metadata"] else {}
                        }
                        
                        memories.append(memory)
                        
                        # Check if memory should be promoted to hot tier
                        if not skip_promotion and row["access_count"] >= self.access_threshold_hot:
                            promote_ids.append(memory["id"])
                    
                    # Update access counts in batch
                    if not skip_promotion and rows:
                        await conn.executemany(
                            """
                            UPDATE ai_mesh_memories
                            SET last_accessed = $1, access_count = access_count + 1
                            WHERE memory_id = $2
                            """,
                            [(datetime.utcnow(), row["memory_id"]) for row in rows]
                        )
                    
                    # Promote hot memories in batch
                    for memory_id in promote_ids:
                        memory = next((m for m in memories if m["id"] == memory_id), None)
                        if memory:
                            await self._promote_to_hot_tier(memory)
            
            # Sort by last_accessed (newest first)
            memories.sort(key=lambda x: x["last_accessed"], reverse=True)
            
            # Apply limit
            memories = memories[:limit]
            
            # Update cache
            self.network_memory_cache[cache_key] = memories
            self.cache_expiry[cache_key] = time.time() + self.cache_ttl
            
            # Manage cache size
            if len(self.network_memory_cache) > self.max_cache_size:
                self._clean_cache()
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get network memories: {e}")
            return []
    
    async def search_memories(
        self,
        network_id: str,
        query: str,
        memory_type: Optional[str] = None,
        vector_embedding: Optional[List[float]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search memories by content or vector similarity.
        
        Args:
            network_id: Network ID
            query: Text query for content search
            memory_type: Optional filter by memory type
            vector_embedding: Optional vector embedding for semantic search
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        if not self.setup_complete:
            await self.setup()
        
        try:
            results = []
            searched_ids = set()
            
            # First search in Redis (hot tier)
            # This is a simple string match search as Redis doesn't have built-in full-text search
            # In a production system, consider integrating with Redis Stack/RediSearch
            index_key = f"{MEMORY_INDEX_PREFIX}{network_id}"
            hot_memory_ids = await self.redis.smembers(index_key)
            
            if hot_memory_ids:
                # Use pipeline for batch retrieval
                pipeline = self.redis.pipeline()
                for memory_id in hot_memory_ids:
                    memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                    pipeline.get(memory_key)
                
                # Execute pipeline
                hot_memory_data = await pipeline.execute()
                
                # Process results
                for data in hot_memory_data:
                    if not data:
                        continue
                    
                    memory = json.loads(data)
                    
                    # Filter by type if specified
                    if memory_type and memory["type"] != memory_type:
                        continue
                    
                    # Simple text match (case-insensitive)
                    if query.lower() in memory["content"].lower():
                        results.append(memory)
                        searched_ids.add(memory["id"])
                        
                        # Update access count
                        await self._increment_access_count(memory["id"])
            
            # Then search in PostgreSQL if available
            if self.pg_pool and len(results) < limit:
                remaining = limit - len(results)
                
                async with self.pg_pool.acquire() as conn:
                    if vector_embedding and len(vector_embedding) > 0:
                        # Vector similarity search (if vector is provided)
                        query_parts = ["SELECT *, vector <=> $3 as distance FROM ai_mesh_memories WHERE network_id = $1"]
                        params = [network_id, memory_type, vector_embedding]
                        
                        if memory_type:
                            query_parts.append("AND memory_type = $2")
                        
                        # Exclude memories already retrieved from hot tier
                        if searched_ids:
                            placeholders = ", ".join(f"${i+4}" for i in range(len(searched_ids)))
                            query_parts.append(f"AND memory_id NOT IN ({placeholders})")
                            params.extend(searched_ids)
                        
                        query_parts.append("ORDER BY distance LIMIT $" + str(len(params) + 1))
                        params.append(remaining)
                        
                        rows = await conn.fetch(" ".join(query_parts), *params)
                    else:
                        # Full-text search
                        query_parts = ["SELECT * FROM ai_mesh_memories WHERE network_id = $1"]
                        params = [network_id]
                        
                        if memory_type:
                            query_parts.append("AND memory_type = $2")
                            params.append(memory_type)
                        else:
                            params.append(None)  # Placeholder for consistent param numbering
                        
                        # Text search condition
                        query_parts.append("AND content ILIKE $3")
                        params.append(f"%{query}%")
                        
                        # Exclude memories already retrieved from hot tier
                        if searched_ids:
                            placeholders = ", ".join(f"${i+4}" for i in range(len(searched_ids)))
                            query_parts.append(f"AND memory_id NOT IN ({placeholders})")
                            params.extend(searched_ids)
                        
                        query_parts.append("ORDER BY last_accessed DESC LIMIT $" + str(len(params) + 1))
                        params.append(remaining)
                        
                        rows = await conn.fetch(" ".join(query_parts), *params)
                    
                    # Process results
                    promote_ids = []
                    for row in rows:
                        memory = {
                            "id": row["memory_id"],
                            "network_id": row["network_id"],
                            "type": row["memory_type"],
                            "content": row["content"],
                            "confidence": row["confidence"],
                            "created_at": row["created_at"].isoformat(),
                            "last_accessed": row["last_accessed"].isoformat(),
                            "access_count": row["access_count"],
                            "metadata": row["metadata"] if row["metadata"] else {}
                        }
                        
                        # Add distance/relevance if available
                        if "distance" in row:
                            memory["similarity"] = 1.0 - float(row["distance"])
                        
                        results.append(memory)
                        
                        # Check if memory should be promoted to hot tier
                        if row["access_count"] + 1 >= self.access_threshold_hot:
                            promote_ids.append(memory["id"])
                    
                    # Update access counts in batch
                    if rows:
                        await conn.executemany(
                            """
                            UPDATE ai_mesh_memories
                            SET last_accessed = $1, access_count = access_count + 1
                            WHERE memory_id = $2
                            """,
                            [(datetime.utcnow(), row["memory_id"]) for row in rows]
                        )
                    
                    # Promote hot memories in batch
                    for memory_id in promote_ids:
                        memory = next((m for m in results if m["id"] == memory_id), None)
                        if memory:
                            await self._promote_to_hot_tier(memory)
            
            # Sort results: either by similarity if available, or recency
            if any("similarity" in r for r in results):
                results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            else:
                results.sort(key=lambda x: x["last_accessed"], reverse=True)
            
            # Apply limit
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory from all tiers.
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.setup_complete:
            await self.setup()
        
        try:
            # Delete from Redis
            memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
            access_key = f"{MEMORY_ACCESS_PREFIX}{memory_id}"
            
            # Get memory to find network_id
            memory_data = await self.redis.get(memory_key)
            if memory_data:
                memory = json.loads(memory_data)
                network_id = memory.get("network_id")
                
                # Remove from index
                if network_id:
                    index_key = f"{MEMORY_INDEX_PREFIX}{network_id}"
                    await self.redis.srem(index_key, memory_id)
            
            # Delete keys
            pipeline = self.redis.pipeline()
            pipeline.delete(memory_key)
            pipeline.delete(access_key)
            await pipeline.execute()
            
            # Delete from PostgreSQL if available
            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    await conn.execute(
                        "DELETE FROM ai_mesh_memories WHERE memory_id = $1",
                        memory_id
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    async def clear_network_memories(self, network_id: str) -> bool:
        """
        Delete all memories for a network.
        
        Args:
            network_id: Network ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.setup_complete:
            await self.setup()
        
        try:
            # Get all memory IDs for the network from Redis
            index_key = f"{MEMORY_INDEX_PREFIX}{network_id}"
            memory_ids = await self.redis.smembers(index_key)
            
            # Delete all memories
            if memory_ids:
                # Delete from Redis
                pipeline = self.redis.pipeline()
                
                # Delete individual memory entries
                for memory_id in memory_ids:
                    memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                    access_key = f"{MEMORY_ACCESS_PREFIX}{memory_id}"
                    pipeline.delete(memory_key)
                    pipeline.delete(access_key)
                
                # Delete the index itself
                pipeline.delete(index_key)
                
                await pipeline.execute()
            
            # Delete from PostgreSQL if available
            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    await conn.execute(
                        "DELETE FROM ai_mesh_memories WHERE network_id = $1",
                        network_id
                    )
            
            # Clear from cache
            for key in list(self.network_memory_cache.keys()):
                if key.startswith(f"{network_id}:"):
                    del self.network_memory_cache[key]
                    if key in self.cache_expiry:
                        del self.cache_expiry[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear network memories: {e}")
            return False
    
    async def _increment_access_count(self, memory_id: str) -> int:
        """Increment access count for a memory item"""
        try:
            access_key = f"{MEMORY_ACCESS_PREFIX}{memory_id}"
            
            # Increment access count
            count = await self.redis.incr(access_key)
            
            # Reset expiry
            await self.redis.expire(access_key, self.hot_tier_ttl)
            
            # Reset memory expiry as well
            memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
            await self.redis.expire(memory_key, self.hot_tier_ttl)
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to increment access count: {e}")
            return 0
    
    async def _promote_to_hot_tier(self, memory: Dict[str, Any]) -> bool:
        """Promote a memory from cold tier to hot tier"""
        try:
            # Store in Redis
            memory_key = f"{MEMORY_KEY_PREFIX}{memory['id']}"
            
            # Update last_accessed time
            memory["last_accessed"] = datetime.utcnow().isoformat()
            
            await self.redis.set(
                memory_key, 
                json.dumps(memory),
                ex=self.hot_tier_ttl
            )
            
            # Set access count
            access_key = f"{MEMORY_ACCESS_PREFIX}{memory['id']}"
            await self.redis.set(
                access_key, 
                str(memory.get("access_count", 1)),
                ex=self.hot_tier_ttl
            )
            
            # Add to index
            index_key = f"{MEMORY_INDEX_PREFIX}{memory['network_id']}"
            await self.redis.sadd(index_key, memory['id'])
            await self.redis.expire(index_key, self.hot_tier_ttl)
            
            # Update cache
            self._update_cache(memory)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to promote memory to hot tier: {e}")
            return False
    
    async def _demote_to_cold_tier(self, memory_id: str) -> bool:
        """Demote a memory from hot tier to cold tier"""
        if not self.pg_pool:
            logger.debug(f"PostgreSQL not available, keeping memory {memory_id} in hot tier")
            return False
            
        try:
            # Get memory from Redis
            memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
            memory_data = await self.redis.get(memory_key)
            
            if not memory_data:
                return False
                
            memory = json.loads(memory_data)
            
            # Get access count
            access_key = f"{MEMORY_ACCESS_PREFIX}{memory_id}"
            access_count_data = await self.redis.get(access_key)
            access_count = int(access_count_data) if access_count_data else 1
            
            # Store in PostgreSQL
            async with self.pg_pool.acquire() as conn:
                # Convert dates
                created_at = datetime.fromisoformat(memory["created_at"].replace("Z", "+00:00"))
                last_accessed = datetime.fromisoformat(memory["last_accessed"].replace("Z", "+00:00"))
                
                # Convert metadata to JSON
                metadata_json = json.dumps(memory.get("metadata", {}))
                
                # Insert/update in PostgreSQL
                await conn.execute(
                    """
                    INSERT INTO ai_mesh_memories 
                    (memory_id, network_id, memory_type, content, confidence, 
                     created_at, last_accessed, access_count, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (memory_id) 
                    DO UPDATE SET 
                        content = EXCLUDED.content,
                        confidence = EXCLUDED.confidence,
                        last_accessed = EXCLUDED.last_accessed,
                        access_count = EXCLUDED.access_count,
                        metadata = EXCLUDED.metadata
                    """,
                    memory["id"], memory["network_id"], memory["type"],
                    memory["content"], memory["confidence"],
                    created_at, last_accessed, access_count,
                    metadata_json
                )
                
                # Delete from Redis
                pipeline = self.redis.pipeline()
                pipeline.delete(memory_key)
                pipeline.delete(access_key)
                
                # Remove from index
                index_key = f"{MEMORY_INDEX_PREFIX}{memory['network_id']}"
                pipeline.srem(index_key, memory_id)
                
                await pipeline.execute()
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to demote memory to cold tier: {e}")
            return False
    
    async def _memory_rotation_task(self):
        """Background task to move memories between tiers based on access patterns"""
        if not self.pg_pool:
            logger.info("PostgreSQL not available, memory rotation disabled")
            return
            
        try:
            while True:
                await asyncio.sleep(self.memory_rotation_interval)
                
                try:
                    # Find infrequently accessed memories in hot tier to demote
                    # These are memories with low access counts and not accessed recently
                    demotion_cutoff = datetime.utcnow() - timedelta(days=1)
                    demotion_cutoff_str = demotion_cutoff.isoformat()
                    
                    # Scan for memory IDs in Redis
                    cursor = 0
                    all_memory_ids = set()
                    
                    while True:
                        cursor, keys = await self.redis.scan(
                            cursor,
                            match=f"{MEMORY_KEY_PREFIX}*",
                            count=1000
                        )
                        
                        for key in keys:
                            memory_id = key[len(MEMORY_KEY_PREFIX):]
                            all_memory_ids.add(memory_id)
                        
                        if cursor == 0:
                            break
                    
                    # Check each memory for demotion criteria
                    for memory_id in all_memory_ids:
                        memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                        memory_data = await self.redis.get(memory_key)
                        
                        if not memory_data:
                            continue
                            
                        memory = json.loads(memory_data)
                        
                        # Check if memory was accessed recently
                        last_accessed = datetime.fromisoformat(memory["last_accessed"].replace("Z", "+00:00"))
                        
                        if last_accessed < demotion_cutoff:
                            # Check access count
                            access_key = f"{MEMORY_ACCESS_PREFIX}{memory_id}"
                            access_count_data = await self.redis.get(access_key)
                            access_count = int(access_count_data) if access_count_data else 0
                            
                            # If access count is low, demote to cold tier
                            if access_count < self.access_threshold_hot:
                                await self._demote_to_cold_tier(memory_id)
                    
                    # Find frequently accessed memories in cold tier to promote
                    if self.pg_pool:
                        async with self.pg_pool.acquire() as conn:
                            rows = await conn.fetch(
                                """
                                SELECT * FROM ai_mesh_memories
                                WHERE access_count >= $1
                                AND last_accessed > $2
                                LIMIT 100
                                """,
                                self.access_threshold_hot,
                                demotion_cutoff
                            )
                            
                            # Promote each memory to hot tier
                            for row in rows:
                                memory = {
                                    "id": row["memory_id"],
                                    "network_id": row["network_id"],
                                    "type": row["memory_type"],
                                    "content": row["content"],
                                    "confidence": row["confidence"],
                                    "created_at": row["created_at"].isoformat(),
                                    "last_accessed": row["last_accessed"].isoformat(),
                                    "access_count": row["access_count"],
                                    "metadata": row["metadata"] if row["metadata"] else {}
                                }
                                
                                await self._promote_to_hot_tier(memory)
                
                except Exception as e:
                    logger.error(f"Error in memory rotation: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Memory rotation task cancelled")
        except Exception as e:
            logger.error(f"Memory rotation task failed: {e}")
            # Restart the task
            asyncio.create_task(self._memory_rotation_task())
    
    async def _memory_pruning_task(self):
        """Background task to prune old memories"""
        try:
            while True:
                await asyncio.sleep(self.memory_pruning_interval)
                
                try:
                    # Calculate cutoff date
                    cutoff_date = datetime.utcnow() - timedelta(days=self.max_memory_age_days)
                    
                    # Delete old memories from cold tier
                    if self.pg_pool:
                        async with self.pg_pool.acquire() as conn:
                            result = await conn.execute(
                                """
                                DELETE FROM ai_mesh_memories
                                WHERE created_at < $1
                                """,
                                cutoff_date
                            )
                            
                            if result != "DELETE 0":
                                rows_deleted = int(result.split()[1])
                                logger.info(f"Pruned {rows_deleted} old memories from cold tier")
                    
                    # No need to prune hot tier as Redis keys have TTL
                    
                except Exception as e:
                    logger.error(f"Error in memory pruning: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Memory pruning task cancelled")
        except Exception as e:
            logger.error(f"Memory pruning task failed: {e}")
            # Restart the task
            asyncio.create_task(self._memory_pruning_task())
    
    def _update_cache(self, memory: Dict[str, Any]):
        """Update memory in cache"""
        network_id = memory.get("network_id")
        if not network_id:
            return
            
        # Update in network cache if present
        for cache_key, memories in self.network_memory_cache.items():
            if cache_key.startswith(f"{network_id}:"):
                # Check if memory exists in this cache
                for i, m in enumerate(memories):
                    if m["id"] == memory["id"]:
                        # Update memory
                        memories[i] = memory
                        break
                else:
                    # If memory not in cache, don't add it to avoid cache inconsistency
                    # It will be loaded on next query
                    pass
    
    def _clean_cache(self):
        """Clean expired or excess cache entries"""
        now = time.time()
        
        # Remove expired entries
        expired_keys = [k for k, v in self.cache_expiry.items() if v < now]
        for key in expired_keys:
            if key in self.network_memory_cache:
                del self.network_memory_cache[key]
            del self.cache_expiry[key]
        
        # If still over limit, remove oldest entries
        if len(self.network_memory_cache) > self.max_cache_size:
            # Get oldest by expiry time
            sorted_keys = sorted(self.cache_expiry.items(), key=lambda x: x[1])
            oldest_keys = [k for k, _ in sorted_keys[:len(self.network_memory_cache) - self.max_cache_size]]
            
            for key in oldest_keys:
                if key in self.network_memory_cache:
                    del self.network_memory_cache[key]
                del self.cache_expiry[key]
    
    async def close(self):
        """Close connections and resources"""
        # No need to close Redis client as it's managed externally
        
        # Close PostgreSQL connection pool
        if self.pg_pool:
            await self.pg_pool.close()
            self.pg_pool = None
            self.setup_complete = False

# Singleton instance
_tiered_memory_storage_instance = None

async def get_tiered_memory_storage() -> TieredMemoryStorage:
    """Get the singleton instance of TieredMemoryStorage"""
    global _tiered_memory_storage_instance
    if _tiered_memory_storage_instance is None:
        _tiered_memory_storage_instance = TieredMemoryStorage()
        
        # Set up with default config
        # In production, this would be loaded from environment or config file
        pg_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "",
            "database": "maily",
            "min_connections": 1,
            "max_connections": 10
        }
        
        try:
            await _tiered_memory_storage_instance.setup(pg_config)
        except Exception as e:
            logger.warning(f"Failed to set up PostgreSQL, falling back to Redis only: {e}")
            await _tiered_memory_storage_instance.setup(None)
            
    return _tiered_memory_storage_instance