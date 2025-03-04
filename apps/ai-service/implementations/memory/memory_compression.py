"""
Memory Compression System for AI Mesh Network

This module provides functionality to compress and decompress memory items,
reducing storage requirements for large memory datasets.
"""

import json
import zlib
import base64
import logging
from typing import Dict, Any, Optional, Union, List
import time

from ...utils.redis_client import get_redis_client

logger = logging.getLogger("ai_service.implementations.memory.memory_compression")

# Constants
COMPRESSION_THRESHOLD = 1024  # Compress memories larger than 1KB
COMPRESSION_LEVEL = 6  # zlib compression level (0-9, higher = more compression but slower)
MEMORY_KEY_PREFIX = "ai_mesh:memory:"
COMPRESSED_FLAG = "__compressed__"

class MemoryCompressionSystem:
    """Memory compression system for efficient storage of large memory items"""
    
    def __init__(self):
        """Initialize the memory compression system"""
        self.redis = get_redis_client()
        self.compression_stats = {
            "compressed_count": 0,
            "total_bytes_before": 0,
            "total_bytes_after": 0,
            "compression_ratio": 0.0
        }
    
    async def store_memory(
        self, 
        memory_id: str, 
        memory_data: Dict[str, Any],
        force_compression: bool = False
    ) -> bool:
        """
        Store a memory item with automatic compression if needed
        
        Args:
            memory_id: ID of the memory item
            memory_data: Memory data (dictionary)
            force_compression: Force compression even if below threshold
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to JSON string
            json_data = json.dumps(memory_data)
            
            # Check if compression needed
            data_size = len(json_data)
            should_compress = force_compression or data_size > COMPRESSION_THRESHOLD
            
            if should_compress:
                # Compress data
                compressed_data = self._compress_data(json_data)
                
                # Add compression flag and store compressed data
                result = await self._store_compressed(memory_id, compressed_data)
                
                # Update stats
                if result:
                    compressed_size = len(compressed_data)
                    self.compression_stats["compressed_count"] += 1
                    self.compression_stats["total_bytes_before"] += data_size
                    self.compression_stats["total_bytes_after"] += compressed_size
                    
                    # Update compression ratio
                    before = self.compression_stats["total_bytes_before"]
                    after = self.compression_stats["total_bytes_after"]
                    if before > 0:
                        self.compression_stats["compression_ratio"] = 1.0 - (after / before)
                
                return result
            else:
                # Store uncompressed
                memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                return await self.redis.set(memory_key, json_data)
                
        except Exception as e:
            logger.error(f"Failed to store memory with compression: {e}")
            return False
    
    async def retrieve_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory item, automatically decompressing if needed
        
        Args:
            memory_id: ID of the memory item
            
        Returns:
            Memory data dictionary if found, None otherwise
        """
        try:
            # Get memory data
            memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
            data = await self.redis.get(memory_key)
            
            if not data:
                return None
            
            # Check if compressed
            try:
                parsed = json.loads(data)
                if isinstance(parsed, dict) and COMPRESSED_FLAG in parsed:
                    # Decompress data
                    compressed_data = parsed[COMPRESSED_FLAG]
                    decompressed_json = self._decompress_data(compressed_data)
                    return json.loads(decompressed_json)
                else:
                    # Already uncompressed
                    return parsed
            except json.JSONDecodeError:
                logger.error(f"Failed to parse memory data for {memory_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve memory with decompression: {e}")
            return None
    
    async def get_compression_stats(self) -> Dict[str, Any]:
        """
        Get compression statistics
        
        Returns:
            Dictionary with compression statistics
        """
        # Calculate current stats
        stats = self.compression_stats.copy()
        
        # Add timestamp
        stats["timestamp"] = time.time()
        
        return stats
    
    async def compress_all_large_memories(
        self, 
        network_id: Optional[str] = None,
        threshold: int = COMPRESSION_THRESHOLD
    ) -> Dict[str, Any]:
        """
        Compress all large memory items for a network or all networks
        
        Args:
            network_id: Optional network ID to limit compression to
            threshold: Size threshold in bytes for compression
            
        Returns:
            Dictionary with compression results
        """
        try:
            # Get memory keys
            if network_id:
                memory_pattern = f"{MEMORY_KEY_PREFIX}*network_id={network_id}*"
            else:
                memory_pattern = f"{MEMORY_KEY_PREFIX}*"
                
            memory_keys = await self.redis.keys(memory_pattern)
            
            if not memory_keys:
                return {"compressed": 0, "examined": 0, "skipped": 0, "errors": 0}
            
            logger.info(f"Examining {len(memory_keys)} memory items for compression")
            
            # Process each memory
            results = {
                "compressed": 0,
                "examined": len(memory_keys),
                "skipped": 0,
                "errors": 0,
                "bytes_before": 0,
                "bytes_after": 0
            }
            
            for memory_key in memory_keys:
                try:
                    # Get memory data
                    data = await self.redis.get(memory_key)
                    if not data:
                        results["skipped"] += 1
                        continue
                    
                    # Check if already compressed
                    try:
                        parsed = json.loads(data)
                        if isinstance(parsed, dict) and COMPRESSED_FLAG in parsed:
                            results["skipped"] += 1
                            continue
                            
                        # Check size
                        data_size = len(data)
                        results["bytes_before"] += data_size
                        
                        if data_size <= threshold:
                            results["skipped"] += 1
                            continue
                        
                        # Compress data
                        memory_id = memory_key.replace(MEMORY_KEY_PREFIX, "")
                        compressed_data = self._compress_data(data)
                        compressed_size = len(compressed_data)
                        results["bytes_after"] += compressed_size
                        
                        # Store compressed
                        success = await self._store_compressed(memory_id, compressed_data)
                        
                        if success:
                            results["compressed"] += 1
                        else:
                            results["errors"] += 1
                            
                    except json.JSONDecodeError:
                        results["errors"] += 1
                        logger.error(f"Failed to parse memory data for {memory_key}")
                        
                except Exception as e:
                    results["errors"] += 1
                    logger.error(f"Error processing memory {memory_key}: {e}")
            
            # Calculate compression ratio
            if results["bytes_before"] > 0:
                results["compression_ratio"] = 1.0 - (results["bytes_after"] / results["bytes_before"])
            else:
                results["compression_ratio"] = 0.0
                
            logger.info(f"Compression results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to compress all memories: {e}")
            return {"error": str(e), "compressed": 0, "examined": 0, "skipped": 0, "errors": 1}
    
    def _compress_data(self, data: str) -> str:
        """
        Compress data using zlib and encode as base64
        
        Args:
            data: Data string to compress
            
        Returns:
            Base64-encoded compressed data
        """
        # Compress with zlib
        compressed = zlib.compress(data.encode('utf-8'), COMPRESSION_LEVEL)
        
        # Encode with base64 for safe storage
        b64_compressed = base64.b64encode(compressed).decode('ascii')
        
        return b64_compressed
    
    def _decompress_data(self, compressed_data: str) -> str:
        """
        Decompress data from base64-encoded zlib-compressed format
        
        Args:
            compressed_data: Base64-encoded compressed data
            
        Returns:
            Original decompressed string
        """
        # Decode base64
        compressed = base64.b64decode(compressed_data)
        
        # Decompress with zlib
        decompressed = zlib.decompress(compressed).decode('utf-8')
        
        return decompressed
    
    async def _store_compressed(self, memory_id: str, compressed_data: str) -> bool:
        """
        Store compressed data with compression flag
        
        Args:
            memory_id: ID of the memory item
            compressed_data: Compressed data string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create compressed data structure
            data = {COMPRESSED_FLAG: compressed_data}
            
            # Store in Redis
            memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
            return await self.redis.set(memory_key, json.dumps(data))
            
        except Exception as e:
            logger.error(f"Failed to store compressed data: {e}")
            return False

# Singleton instance
_memory_compression_instance = None

def get_memory_compression_system() -> MemoryCompressionSystem:
    """Get the singleton instance of MemoryCompressionSystem"""
    global _memory_compression_instance
    if _memory_compression_instance is None:
        _memory_compression_instance = MemoryCompressionSystem()
    return _memory_compression_instance