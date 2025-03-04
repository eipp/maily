"""
Redis Client Utility for AI Service

This module provides a Redis client for the AI service with connection pooling,
circuit breaker pattern for resilience, and standardized error handling.
"""

import logging
import os
import time
import asyncio
from typing import Any, Optional, List, Dict, Union
import redis.asyncio as redis
from redis.asyncio.retry import Retry
from redis.exceptions import RedisError, ConnectionError, TimeoutError
import json

logger = logging.getLogger("ai_service.utils.redis_client")

# Circuit breaker constants
CB_FAILURE_THRESHOLD = int(os.environ.get("REDIS_CB_FAILURE_THRESHOLD", "5"))
CB_RESET_TIMEOUT = float(os.environ.get("REDIS_CB_RESET_TIMEOUT", "30.0"))
CB_HALF_OPEN_TIMEOUT = float(os.environ.get("REDIS_CB_HALF_OPEN_TIMEOUT", "5.0"))

# Connection pool settings
POOL_MIN_SIZE = int(os.environ.get("REDIS_POOL_MIN_SIZE", "5"))
POOL_MAX_SIZE = int(os.environ.get("REDIS_POOL_MAX_SIZE", "20"))

# Operation timeout
DEFAULT_TIMEOUT = float(os.environ.get("REDIS_DEFAULT_TIMEOUT", "1.0"))

class CircuitBreaker:
    """Circuit breaker implementation for Redis operations"""
    
    def __init__(self, name: str, failure_threshold: int = CB_FAILURE_THRESHOLD, 
                 reset_timeout: float = CB_RESET_TIMEOUT, 
                 half_open_timeout: float = CB_HALF_OPEN_TIMEOUT):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
        logger.info(f"Initialized circuit breaker '{name}' with failure_threshold={failure_threshold}")
    
    def record_success(self):
        """Record a successful operation"""
        if self.state != "closed":
            logger.info(f"Circuit breaker '{self.name}' reset from {self.state} to closed after success")
            self.state = "closed"
            self.failures = 0
    
    def record_failure(self):
        """Record a failed operation"""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.state == "closed" and self.failures >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker '{self.name}' tripped open after {self.failures} failures")
    
    def allow_request(self) -> bool:
        """Check if a request should be allowed based on circuit state"""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            # Check if enough time has passed to try again
            if time.time() - self.last_failure_time > self.reset_timeout:
                logger.info(f"Circuit breaker '{self.name}' transitioning from open to half-open")
                self.state = "half-open"
                return True
            return False
        
        # Half-open state: allow occasional requests
        if time.time() - self.last_failure_time > self.half_open_timeout:
            logger.debug(f"Circuit breaker '{self.name}' allowing test request in half-open state")
            return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state,
            "failures": self.failures,
            "time_since_last_failure": time.time() - self.last_failure_time if self.last_failure_time > 0 else None
        }

class RedisClient:
    """Redis client for AI service with connection pooling and circuit breaker"""
    
    def __init__(self, url: str = None):
        """Initialize Redis client"""
        self.url = url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.client = None
        self.circuit_breaker = CircuitBreaker("redis")
        self.operations_total = 0
        self.operations_success = 0
        self.operations_failed = 0
        self.last_error = None
        self.connection_attempts = 0
        self.connect_lock = asyncio.Lock()
        
    async def connect(self):
        """Connect to Redis with connection pooling"""
        async with self.connect_lock:
            if self.client is not None:
                return

            self.connection_attempts += 1
            
            try:
                if not self.circuit_breaker.allow_request():
                    logger.warning("Circuit breaker preventing Redis connection attempt")
                    raise RedisError("Circuit breaker for Redis is open")
                
                # Configure connection with advanced options
                retry_config = Retry(
                    backoff=Retry.exponential_backoff(
                        cap=1.0, base=0.5
                    ),
                    retries=3,
                    # Errors to retry on
                    errors=(ConnectionError, TimeoutError),
                )
                
                # Create client with connection pool
                self.client = redis.from_url(
                    self.url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=POOL_MAX_SIZE,
                    retry=retry_config,
                    health_check_interval=15
                )
                
                # Test connection
                await asyncio.wait_for(
                    self.client.ping(), 
                    timeout=2.0
                )
                
                # Record success
                self.circuit_breaker.record_success()
                logger.info(f"Connected to Redis at {self.url} with connection pool")
                
            except Exception as e:
                self.last_error = str(e)
                self.circuit_breaker.record_failure()
                self.client = None
                logger.error(f"Failed to connect to Redis: {e}")
                raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            try:
                await self.client.close()
                self.client = None
                logger.info("Disconnected from Redis")
            except Exception as e:
                logger.error(f"Error disconnecting from Redis: {e}")
                self.client = None
    
    async def _ensure_connected(self):
        """Ensure Redis client is connected with circuit breaker protection"""
        if self.client is None:
            await self.connect()
    
    async def _execute_with_cb(self, operation_name: str, coroutine, timeout: float = DEFAULT_TIMEOUT):
        """Execute Redis operation with circuit breaker protection"""
        if not self.circuit_breaker.allow_request():
            logger.warning(f"Circuit breaker preventing Redis {operation_name} operation")
            self.operations_total += 1
            self.operations_failed += 1
            return None
            
        self.operations_total += 1
        start_time = time.time()
        
        try:
            # Execute operation with timeout
            result = await asyncio.wait_for(coroutine, timeout=timeout)
            
            # Record metrics
            self.operations_success += 1
            self.circuit_breaker.record_success()
            duration = time.time() - start_time
            logger.debug(f"Redis {operation_name} completed in {duration:.3f}s")
            
            return result
            
        except (ConnectionError, TimeoutError) as e:
            # Connection errors - record for circuit breaker
            self.operations_failed += 1
            self.circuit_breaker.record_failure()
            self.last_error = f"{operation_name} error: {str(e)}"
            logger.error(f"Redis {operation_name} connection error: {e}")
            # Reset client on connection errors
            self.client = None
            return None
            
        except Exception as e:
            # Other errors
            self.operations_failed += 1
            self.last_error = f"{operation_name} error: {str(e)}"
            logger.error(f"Redis {operation_name} error: {e}")
            return None
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis with circuit breaker protection"""
        await self._ensure_connected()
        return await self._execute_with_cb("GET", self.client.get(key))
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with circuit breaker protection"""
        await self._ensure_connected()
        result = await self._execute_with_cb("SET", self.client.set(key, value, ex=ex))
        return result is not None
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis with circuit breaker protection"""
        await self._ensure_connected()
        result = await self._execute_with_cb("DEL", self.client.delete(key))
        return result is not None
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern from Redis with circuit breaker protection"""
        await self._ensure_connected()
        result = await self._execute_with_cb("KEYS", self.client.keys(pattern))
        return result or []
    
    async def ping(self) -> bool:
        """Ping Redis with circuit breaker protection"""
        # Allow ping even when circuit breaker is open (used for health checks)
        if self.client is None:
            try:
                await self.connect()
            except Exception:
                return False
        
        try:
            result = await asyncio.wait_for(self.client.ping(), timeout=1.0)
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Failed to ping Redis: {e}")
            return False
    
    async def hset(self, key: str, field: str, value: str) -> bool:
        """Set hash field in Redis with circuit breaker protection"""
        await self._ensure_connected()
        result = await self._execute_with_cb("HSET", self.client.hset(key, field, value))
        return result is not None
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field from Redis with circuit breaker protection"""
        await self._ensure_connected()
        return await self._execute_with_cb("HGET", self.client.hget(key, field))
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields from Redis with circuit breaker protection"""
        await self._ensure_connected()
        result = await self._execute_with_cb("HGETALL", self.client.hgetall(key))
        return result or {}
    
    async def lpush(self, key: str, *values: str) -> bool:
        """Push values to list in Redis with circuit breaker protection"""
        await self._ensure_connected()
        result = await self._execute_with_cb("LPUSH", self.client.lpush(key, *values))
        return result is not None
    
    async def rpush(self, key: str, *values: str) -> bool:
        """Push values to list in Redis with circuit breaker protection"""
        await self._ensure_connected()
        result = await self._execute_with_cb("RPUSH", self.client.rpush(key, *values))
        return result is not None
    
    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get range of values from list in Redis with circuit breaker protection"""
        await self._ensure_connected()
        result = await self._execute_with_cb("LRANGE", self.client.lrange(key, start, end))
        return result or []
        
    def pipeline(self):
        """Get a Redis pipeline for batch operations"""
        return RedisPipeline(self)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis client statistics"""
        return {
            "connected": self.client is not None,
            "operations_total": self.operations_total,
            "operations_success": self.operations_success,
            "operations_failed": self.operations_failed,
            "circuit_breaker": self.circuit_breaker.get_stats(),
            "last_error": self.last_error
        }
    
    async def publish(self, channel: str, message: str) -> bool:
        """Publish message to channel in Redis with circuit breaker protection"""
        await self._ensure_connected()
        result = await self._execute_with_cb("PUBLISH", self.client.publish(channel, message))
        return result is not None
    
    async def subscribe(self, channel: str):
        """Subscribe to channel in Redis with circuit breaker protection"""
        await self._ensure_connected()
        try:
            if not self.circuit_breaker.allow_request():
                logger.warning(f"Circuit breaker preventing Redis SUBSCRIBE operation")
                return None
                
            pubsub = self.client.pubsub()
            await asyncio.wait_for(pubsub.subscribe(channel), timeout=2.0)
            self.circuit_breaker.record_success()
            return pubsub
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
            return None
    
    async def info(self, section: Optional[str] = None) -> Dict[str, str]:
        """Get Redis server info with circuit breaker protection"""
        await self._ensure_connected()
        try:
            if section:
                result = await self._execute_with_cb("INFO", self.client.info(section))
            else:
                result = await self._execute_with_cb("INFO", self.client.info())
            return result or {}
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {}

class RedisPipeline:
    """Redis pipeline implementation with circuit breaker protection"""
    
    def __init__(self, client: RedisClient):
        self.client = client
        self.pipeline = None
        self.commands = []
    
    async def __aenter__(self):
        """Enter pipeline context manager"""
        await self.client._ensure_connected()
        self.pipeline = self.client.client.pipeline()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        """Exit pipeline context manager"""
        self.pipeline = None
        self.commands = []
    
    def get(self, key: str):
        """Add GET command to pipeline"""
        if self.pipeline is None:
            raise RuntimeError("Pipeline not initialized - use 'async with' context")
        self.commands.append(("GET", key))
        return self.pipeline.get(key)
    
    def set(self, key: str, value: str, ex: Optional[int] = None):
        """Add SET command to pipeline"""
        if self.pipeline is None:
            raise RuntimeError("Pipeline not initialized - use 'async with' context")
        self.commands.append(("SET", key))
        if ex:
            return self.pipeline.set(key, value, ex=ex)
        return self.pipeline.set(key, value)
    
    def delete(self, key: str):
        """Add DEL command to pipeline"""
        if self.pipeline is None:
            raise RuntimeError("Pipeline not initialized - use 'async with' context")
        self.commands.append(("DEL", key))
        return self.pipeline.delete(key)
    
    def keys(self, pattern: str):
        """Add KEYS command to pipeline"""
        if self.pipeline is None:
            raise RuntimeError("Pipeline not initialized - use 'async with' context")
        self.commands.append(("KEYS", pattern))
        return self.pipeline.keys(pattern)
    
    def info(self, section: Optional[str] = None):
        """Add INFO command to pipeline"""
        if self.pipeline is None:
            raise RuntimeError("Pipeline not initialized - use 'async with' context")
        self.commands.append(("INFO", section or ""))
        if section:
            return self.pipeline.info(section)
        return self.pipeline.info()
    
    async def execute(self):
        """Execute all commands in the pipeline with circuit breaker protection"""
        if self.pipeline is None:
            raise RuntimeError("Pipeline not initialized - use 'async with' context")
            
        # Check circuit breaker
        if not self.client.circuit_breaker.allow_request():
            logger.warning(f"Circuit breaker preventing Redis pipeline execution with {len(self.commands)} commands")
            self.client.operations_total += 1
            self.client.operations_failed += 1
            return None
            
        self.client.operations_total += 1
        start_time = time.time()
        
        try:
            # Execute pipeline with timeout
            result = await asyncio.wait_for(
                self.pipeline.execute(), 
                timeout=DEFAULT_TIMEOUT * (len(self.commands) or 1)
            )
            
            # Record success
            self.client.operations_success += 1
            self.client.circuit_breaker.record_success()
            
            duration = time.time() - start_time
            logger.debug(f"Redis pipeline with {len(self.commands)} commands completed in {duration:.3f}s")
            
            return result
            
        except Exception as e:
            self.client.operations_failed += 1
            self.client.last_error = f"Pipeline error: {str(e)}"
            self.client.circuit_breaker.record_failure()
            
            # Reset client on connection errors
            if isinstance(e, (ConnectionError, TimeoutError)):
                self.client.client = None
                
            logger.error(f"Redis pipeline error: {e}")
            return None

# Singleton instance
_redis_client_instance = None

def get_redis_client() -> RedisClient:
    """Get the singleton instance of RedisClient"""
    global _redis_client_instance
    if _redis_client_instance is None:
        _redis_client_instance = RedisClient()
    return _redis_client_instance

async def init_redis():
    """Initialize Redis connection"""
    client = get_redis_client()
    await client.connect()
    return client

async def close_redis():
    """Close Redis connection"""
    global _redis_client_instance
    if _redis_client_instance is not None:
        await _redis_client_instance.disconnect()
        _redis_client_instance = None
