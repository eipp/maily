"""
Blockchain Service for Interactive Trust Verification

This service provides blockchain-based verification for email content using the Polygon blockchain.
It implements circuit breaker patterns, memory caching, and resilience mechanisms for production reliability.
"""

import json
import logging
import hashlib
import base64
import time
import asyncio
import functools
from typing import Dict, Any, List, Optional, Tuple, Callable, MutableMapping
from datetime import datetime, timedelta
from pydantic import BaseModel
from functools import wraps, lru_cache
from collections import OrderedDict, defaultdict

# Try importing Web3 for real blockchain implementation
try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

from ..utils.encryption import encrypt_data, decrypt_data
from ..cache.redis_client import get_redis_client
from ..utils.resilience import circuit_breaker, retry_with_backoff
from ..config.settings import settings

logger = logging.getLogger("api.services.blockchain")

# Mock blockchain transaction data for simulation
# In a real implementation, this would use ethers.js or web3.py to interact with the blockchain
MOCK_TRANSACTIONS = {}
MOCK_BLOCKS = {}
MOCK_BLOCK_NUMBER = 12345678

class TimedCache:
    """
    Time-based cache implementation for blockchain data
    
    Provides an in-memory cache with expiring entries based on time.
    Thread-safe for concurrent access.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize a new timed cache
        
        Args:
            max_size: Maximum number of items to store in cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._expiry: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache if it exists and is not expired
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        async with self._lock:
            # Check if key exists and is not expired
            if key in self._cache:
                if key in self._expiry:
                    # Check if expired
                    if datetime.utcnow() > self._expiry[key]:
                        # Remove expired item
                        self._remove_item(key)
                        return None
                
                # Move to end to track LRU
                value = self._cache[key]
                self._cache.move_to_end(key)
                return value
                
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with expiration
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Time-to-live in seconds, or None to use default
        """
        ttl = ttl if ttl is not None else self.default_ttl
        
        async with self._lock:
            # Check if we need to evict for size
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Remove oldest item (first in OrderedDict)
                self._cache.popitem(last=False)
            
            # Set value
            self._cache[key] = value
            self._cache.move_to_end(key)
            
            # Set expiry time
            self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
    
    async def delete(self, key: str) -> None:
        """
        Delete a key from the cache
        
        Args:
            key: Cache key to delete
        """
        async with self._lock:
            self._remove_item(key)
    
    def _remove_item(self, key: str) -> None:
        """
        Remove an item from the cache (internal, no locking)
        
        Args:
            key: Cache key to remove
        """
        if key in self._cache:
            del self._cache[key]
        
        if key in self._expiry:
            del self._expiry[key]
    
    async def clear(self) -> None:
        """Clear all items from the cache"""
        async with self._lock:
            self._cache.clear()
            self._expiry.clear()
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired items from the cache
        
        Returns:
            Number of items removed
        """
        count = 0
        now = datetime.utcnow()
        
        async with self._lock:
            # Find expired keys
            expired_keys = [
                key for key, expiry in self._expiry.items() 
                if now > expiry
            ]
            
            # Remove expired items
            for key in expired_keys:
                self._remove_item(key)
                count += 1
                
        return count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            stats = {
                "size": len(self._cache),
                "max_size": self.max_size,
                "utilization": len(self._cache) / self.max_size if self.max_size > 0 else 0,
                "default_ttl": self.default_ttl
            }
        
        return stats


def async_lru_cache(maxsize: int = 128, ttl: int = 3600):
    """
    LRU cache decorator for async functions with TTL
    
    Args:
        maxsize: Maximum cache size
        ttl: Time-to-live in seconds
        
    Returns:
        Cached async function
    """
    cache = {}
    timestamps = {}
    make_key = lambda *args, **kwargs: hash(str(args) + str(sorted(kwargs.items())))
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = make_key(*args, **kwargs)
            
            # Check if result in cache and not expired
            now = time.time()
            if key in cache:
                last_update = timestamps[key]
                if now - last_update < ttl:
                    # Cache hit, return cached result
                    return cache[key]
            
            # Cache miss or expired, call function
            result = await func(*args, **kwargs)
            
            # Update cache
            cache[key] = result
            timestamps[key] = now
            
            # Enforce size limit
            if len(cache) > maxsize:
                # Find oldest entry
                oldest_key = min(timestamps.items(), key=lambda x: x[1])[0]
                # Remove it
                del cache[oldest_key]
                del timestamps[oldest_key]
            
            return result
        return wrapper
    return decorator

class BlockchainService:
    """Service for interacting with the Polygon blockchain"""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.contract_address = "0x1234567890123456789012345678901234567890"
        self.network = "polygon"
        self.gas_limit = 50000  # Maximum gas limit for transactions
        
        # Initialize cache system for blockchain data
        self.verification_cache = TimedCache(max_size=5000, default_ttl=3600)  # 1 hour TTL
        self.certificate_cache = TimedCache(max_size=1000, default_ttl=7200)   # 2 hour TTL
        self.transaction_cache = TimedCache(max_size=2000, default_ttl=86400)  # 24 hour TTL
        self.block_cache = TimedCache(max_size=500, default_ttl=604800)        # 1 week TTL
        
        # Start background task for cache maintenance
        self._schedule_cache_maintenance()
        
        logger.info("BlockchainService initialized with caching support")
    
    def _schedule_cache_maintenance(self):
        """Schedule periodic cache maintenance task"""
        async def maintenance_task():
            while True:
                try:
                    # Run cleanup every 15 minutes
                    await asyncio.sleep(900)
                    await self._cleanup_caches()
                except Exception as e:
                    logger.error(f"Error in cache maintenance task: {e}")
                    # Sleep a bit before trying again
                    await asyncio.sleep(60)
        
        # Run in background
        asyncio.create_task(maintenance_task())
    
    async def _cleanup_caches(self):
        """Clean up expired items from all caches"""
        verification_count = await self.verification_cache.cleanup_expired()
        certificate_count = await self.certificate_cache.cleanup_expired()
        transaction_count = await self.transaction_cache.cleanup_expired() 
        block_count = await self.block_cache.cleanup_expired()
        
        total_count = verification_count + certificate_count + transaction_count + block_count
        
        logger.info(f"Cache maintenance completed: {total_count} expired items removed")
        
        # Log cache stats
        v_stats = await self.verification_cache.get_stats()
        c_stats = await self.certificate_cache.get_stats()
        t_stats = await self.transaction_cache.get_stats()
        b_stats = await self.block_cache.get_stats()
        
        logger.debug(f"Cache stats: verification={v_stats['size']}/{v_stats['max_size']}, "
                     f"certificate={c_stats['size']}/{c_stats['max_size']}, "
                     f"transaction={t_stats['size']}/{t_stats['max_size']}, "
                     f"block={b_stats['size']}/{b_stats['max_size']}")
        
    async def verify_content(
        self, 
        content_hash: str,
        metadata: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Verify content by storing its hash on the blockchain"""
        try:
            # In a real implementation, this would create and send a blockchain transaction
            # For now, we'll simulate a blockchain transaction
            
            # Generate transaction ID
            transaction_id = f"0x{hashlib.sha256(f'{content_hash}:{int(time.time())}'.encode()).hexdigest()}"
            
            # Simulate transaction data
            transaction_data = {
                "hash": transaction_id,
                "from": f"0x{hashlib.sha256(user_id.encode()).hexdigest()[:40]}",
                "to": self.contract_address,
                "data": f"0x{content_hash}",
                "value": "0",
                "gas": self.gas_limit,
                "gasPrice": "5000000000",  # 5 Gwei
                "nonce": int(time.time()),
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata,
            }
            
            # Store transaction data
            MOCK_TRANSACTIONS[transaction_id] = transaction_data
            
            # Simulate block inclusion
            global MOCK_BLOCK_NUMBER
            MOCK_BLOCK_NUMBER += 1
            
            block_data = {
                "number": MOCK_BLOCK_NUMBER,
                "hash": f"0x{hashlib.sha256(f'block:{MOCK_BLOCK_NUMBER}'.encode()).hexdigest()}",
                "timestamp": datetime.utcnow().isoformat(),
                "transactions": [transaction_id],
            }
            
            MOCK_BLOCKS[MOCK_BLOCK_NUMBER] = block_data
            
            # Update transaction with block info
            transaction_data["blockNumber"] = MOCK_BLOCK_NUMBER
            transaction_data["blockHash"] = block_data["hash"]
            
            # Store verification data in Redis for persistence
            verification_key = f"blockchain:verification:{content_hash}"
            await self.redis.set(
                verification_key,
                json.dumps({
                    "content_hash": content_hash,
                    "transaction_id": transaction_id,
                    "block_number": MOCK_BLOCK_NUMBER,
                    "timestamp": datetime.utcnow().isoformat(),
                    "network": self.network,
                    "contract_address": self.contract_address,
                    "metadata": metadata,
                }),
                expire=86400 * 365  # 1 year
            )
            
            # Return verification data
            return {
                "transaction_id": transaction_id,
                "block_number": MOCK_BLOCK_NUMBER,
                "timestamp": datetime.utcnow().isoformat(),
                "network": self.network,
                "contract_address": self.contract_address,
            }
            
        except Exception as e:
            logger.error(f"Failed to verify content on blockchain: {e}")
            raise
    
    @async_lru_cache(maxsize=500, ttl=3600)
    async def get_verification(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get verification data for a content hash with caching"""
        try:
            # Check memory cache first
            cache_key = f"verification:{content_hash}"
            cached_data = await self.verification_cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for verification data: {content_hash}")
                return cached_data
            
            # Check Redis if not in memory cache
            verification_key = f"blockchain:verification:{content_hash}"
            verification_data = await self.redis.get(verification_key)
            
            if verification_data:
                parsed_data = json.loads(verification_data)
                
                # Store in memory cache for future requests
                await self.verification_cache.set(cache_key, parsed_data)
                
                return parsed_data
            
            logger.debug(f"Verification data not found for hash: {content_hash}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get verification data: {e}")
            return None
    
    @async_lru_cache(maxsize=500, ttl=86400)  # Cache for 24 hours
    async def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction details with caching"""
        try:
            # Check memory cache first
            cache_key = f"transaction:{transaction_id}"
            cached_data = await self.transaction_cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for transaction: {transaction_id}")
                return cached_data
            
            # Query blockchain or mock data
            # In a real implementation, this would query the blockchain
            transaction_data = None
            if transaction_id in MOCK_TRANSACTIONS:
                transaction_data = MOCK_TRANSACTIONS[transaction_id]
            
            if transaction_data:
                # Store in memory cache for future requests
                await self.transaction_cache.set(cache_key, transaction_data)
                return transaction_data
            
            logger.debug(f"Transaction not found: {transaction_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get transaction: {e}")
            return None
    
    @async_lru_cache(maxsize=200, ttl=604800)  # Cache for 1 week
    async def get_block(self, block_number: int) -> Optional[Dict[str, Any]]:
        """Get block details with caching"""
        try:
            # Check memory cache first
            cache_key = f"block:{block_number}"
            cached_data = await self.block_cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for block: {block_number}")
                return cached_data
            
            # Query blockchain or mock data
            # In a real implementation, this would query the blockchain
            block_data = None
            if block_number in MOCK_BLOCKS:
                block_data = MOCK_BLOCKS[block_number]
            
            if block_data:
                # Store in memory cache for future requests (longer TTL for blocks since they're immutable)
                await self.block_cache.set(cache_key, block_data, ttl=604800)  # 1 week
                return block_data
            
            logger.debug(f"Block not found: {block_number}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get block: {e}")
            return None
    
    async def create_token(
        self, 
        recipient: str,
        metadata: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Create a token for a recipient"""
        try:
            # In a real implementation, this would mint an NFT or token
            # For now, we'll simulate token creation
            
            # Generate token ID
            token_id = f"{int(time.time())}_{hashlib.sha256(f'{recipient}:{int(time.time())}'.encode()).hexdigest()[:16]}"
            
            # Simulate token data
            token_data = {
                "id": token_id,
                "recipient": recipient,
                "creator": user_id,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat(),
                "transaction_id": f"0x{hashlib.sha256(f'token:{token_id}'.encode()).hexdigest()}",
                "network": self.network,
                "contract_address": self.contract_address,
            }
            
            # Store token data in Redis
            token_key = f"blockchain:token:{token_id}"
            await self.redis.set(
                token_key,
                json.dumps(token_data),
                expire=86400 * 365  # 1 year
            )
            
            # Return token data
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to create token: {e}")
            raise
    
    async def get_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get token details"""
        try:
            # Get token data from Redis
            token_key = f"blockchain:token:{token_id}"
            token_data = await self.redis.get(token_key)
            
            if token_data:
                return json.loads(token_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get token: {e}")
            return None
    
    async def get_tokens_for_recipient(self, recipient: str) -> List[Dict[str, Any]]:
        """Get all tokens for a recipient"""
        try:
            # In a real implementation, this would query the blockchain
            # For now, we'll simulate by scanning Redis keys
            # This is not efficient and would be implemented differently in production
            
            # Get all token keys
            token_keys = await self.redis.keys("blockchain:token:*")
            tokens = []
            
            for key in token_keys:
                token_data = await self.redis.get(key)
                if token_data:
                    token = json.loads(token_data)
                    if token.get("recipient") == recipient:
                        tokens.append(token)
            
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to get tokens for recipient: {e}")
            return []
    
    def generate_content_hash(self, content: str) -> str:
        """Generate hash of content for verification"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    @circuit_breaker(failure_threshold=5, reset_timeout=300)
    async def verify_certificate(
        self, 
        certificate_id: str,
        content_hash: str
    ) -> Dict[str, Any]:
        """Verify a certificate against the blockchain with circuit breaker and caching"""
        try:
            # Check memory cache first
            cache_key = f"certificate_verification:{certificate_id}:{content_hash}"
            cached_result = await self.certificate_cache.get(cache_key)
            
            if cached_result:
                logger.debug(f"Cache hit for certificate verification: {certificate_id}")
                return cached_result
            
            # Get verification data (which is itself cached)
            verification_data = await self.get_verification(content_hash)
            
            if not verification_data:
                result = {
                    "verified": False,
                    "message": "No verification data found for this content",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Cache negative results for a shorter period
                await self.certificate_cache.set(cache_key, result, ttl=1800)  # 30 minutes
                
                return result
            
            # Check if certificate ID matches
            if verification_data.get("metadata", {}).get("certificate_id") != certificate_id:
                result = {
                    "verified": False,
                    "message": "Certificate ID does not match verification data",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Cache negative results for a shorter period
                await self.certificate_cache.set(cache_key, result, ttl=1800)  # 30 minutes
                
                return result
            
            # In a real implementation, this would verify the certificate on the blockchain
            # For now, we'll simulate verification
            
            result = {
                "verified": True,
                "message": "Certificate verified successfully",
                "verification_data": verification_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache positive results for longer
            await self.certificate_cache.set(cache_key, result, ttl=7200)  # 2 hours
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to verify certificate: {e}")
            
            # Create error result
            error_result = {
                "verified": False,
                "message": f"Error verifying certificate: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            
            # Still cache error results, but for a shorter time
            await self.certificate_cache.set(cache_key, error_result, ttl=300)  # 5 minutes
            
            return error_result

# Singleton instance
_instance = None

def get_blockchain_service():
    """Get singleton instance of BlockchainService"""
    global _instance
    if _instance is None:
        _instance = BlockchainService()
    return _instance
