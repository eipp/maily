"""
Concurrent Verification Utilities

This module provides utilities for concurrent verification operations
using async/await patterns for improved performance.
"""

import asyncio
import logging
from typing import List, Dict, Any, Callable, Coroutine, TypeVar, Tuple, Optional, Set
from functools import wraps
import time
from datetime import datetime, timedelta

logger = logging.getLogger("api.utils.concurrent_verification")

T = TypeVar('T')
R = TypeVar('R')

class VerificationResult:
    """Container for verification results with metadata"""
    
    def __init__(self, success: bool, data: Any = None, error: Exception = None, duration_ms: float = 0):
        self.success = success
        self.data = data
        self.error = error
        self.duration_ms = duration_ms
        self.timestamp = datetime.utcnow()
    
    def __repr__(self) -> str:
        return (f"VerificationResult(success={self.success}, "
                f"data={self.data}, error={self.error}, "
                f"duration_ms={self.duration_ms})")

async def verify_concurrently(
    verification_funcs: List[Tuple[str, Callable[..., Coroutine[Any, Any, T]], Dict[str, Any]]],
    timeout: float = 10.0,
    min_success: int = 1
) -> Dict[str, VerificationResult]:
    """
    Run multiple verification functions concurrently
    
    Args:
        verification_funcs: List of (name, function, kwargs) tuples to execute
        timeout: Maximum time to wait for all verifications (seconds)
        min_success: Minimum number of successful verifications required
        
    Returns:
        Dictionary of verification name -> VerificationResult
    """
    results: Dict[str, VerificationResult] = {}
    success_count = 0
    
    # Create tasks with timeouts for each verification function
    async def run_with_timeout(name: str, func: Callable[..., Coroutine[Any, Any, T]], kwargs: Dict[str, Any]) -> Tuple[str, VerificationResult]:
        start_time = time.time()
        try:
            # Run the function with timeout
            result = await asyncio.wait_for(func(**kwargs), timeout=timeout)
            duration_ms = (time.time() - start_time) * 1000
            return name, VerificationResult(True, result, None, duration_ms)
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            logger.warning(f"Verification {name} timed out after {duration_ms:.2f}ms")
            return name, VerificationResult(False, None, asyncio.TimeoutError(f"Timed out after {timeout}s"), duration_ms)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(f"Verification {name} failed: {e}")
            return name, VerificationResult(False, None, e, duration_ms)
    
    # Create and gather all verification tasks
    tasks = [run_with_timeout(name, func, kwargs) for name, func, kwargs in verification_funcs]
    
    # Execute all tasks concurrently and collect results
    for name, result in await asyncio.gather(*tasks):
        results[name] = result
        if result.success:
            success_count += 1
    
    # Check if we have enough successful verifications
    if success_count < min_success:
        logger.error(f"Verification failed: Only {success_count} successful verifications, {min_success} required")
    else:
        logger.info(f"Verification succeeded with {success_count} successful verifications")
    
    return results

async def verify_with_fallback(
    primary_func: Callable[..., Coroutine[Any, Any, T]],
    fallback_funcs: List[Callable[..., Coroutine[Any, Any, T]]],
    primary_kwargs: Dict[str, Any] = None,
    fallback_kwargs: List[Dict[str, Any]] = None,
    timeout: float = 5.0
) -> Tuple[T, str]:
    """
    Try to execute primary verification function with fallbacks if it fails
    
    Args:
        primary_func: Primary verification function to try first
        fallback_funcs: List of fallback functions to try if primary fails
        primary_kwargs: Keyword arguments for primary function
        fallback_kwargs: List of keyword arguments for fallback functions
        timeout: Timeout for each verification attempt
        
    Returns:
        Tuple of (result, source) where source is 'primary' or 'fallback_N'
    """
    primary_kwargs = primary_kwargs or {}
    fallback_kwargs = fallback_kwargs or [{}] * len(fallback_funcs)
    
    # Try primary function first
    try:
        start_time = time.time()
        result = await asyncio.wait_for(primary_func(**primary_kwargs), timeout=timeout)
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Primary verification succeeded in {duration_ms:.2f}ms")
        return result, "primary"
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"Primary verification failed: {e}")
    
    # Try fallbacks in sequence
    for i, (func, kwargs) in enumerate(zip(fallback_funcs, fallback_kwargs)):
        try:
            start_time = time.time()
            result = await asyncio.wait_for(func(**kwargs), timeout=timeout)
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"Fallback verification {i} succeeded in {duration_ms:.2f}ms")
            return result, f"fallback_{i}"
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Fallback verification {i} failed: {e}")
    
    # All verifications failed
    raise ValueError("All verification methods failed")

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for verification operations.
    Tracks failures and prevents operation execution when failure threshold is reached.
    """
    
    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 60.0):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before circuit opens
            reset_timeout: Seconds before attempting to reset circuit
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.is_open = False
        self.last_failure_time = None
    
    def __call__(self, func):
        """
        Decorator for functions to add circuit breaker protection
        
        Args:
            func: Function to wrap with circuit breaker
            
        Returns:
            Wrapped function with circuit breaker
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.is_open:
                # Check if reset timeout has passed since last failure
                if (self.last_failure_time and
                    (datetime.utcnow() - self.last_failure_time).total_seconds() > self.reset_timeout):
                    # Allow a single test request through in half-open state
                    logger.info("Circuit in half-open state, testing with a single request")
                    self.is_open = False
                else:
                    # Circuit is open and timeout hasn't elapsed
                    logger.warning(f"Circuit open, skipping operation: {func.__name__}")
                    raise RuntimeError(f"Circuit open for {func.__name__}")
            
            try:
                # Call the original function
                result = await func(*args, **kwargs)
                
                # Reset failure count on success if half-open
                if self.failures > 0:
                    logger.info(f"Circuit reset after successful request for {func.__name__}")
                    self.failures = 0
                
                return result
            except Exception as e:
                # Record failure
                self.failures += 1
                self.last_failure_time = datetime.utcnow()
                
                # Check if threshold is reached
                if self.failures >= self.failure_threshold:
                    logger.error(f"Circuit opened after {self.failures} failures in {func.__name__}")
                    self.is_open = True
                
                # Re-raise the exception
                raise
            
        return wrapper

async def batch_verify(
    items: List[Any], 
    verify_func: Callable[[Any], Coroutine[Any, Any, bool]],
    batch_size: int = 10,
    concurrency_limit: int = 5
) -> Dict[Any, bool]:
    """
    Verify multiple items in batches with concurrency control
    
    Args:
        items: List of items to verify
        verify_func: Async function that verifies a single item
        batch_size: Number of items to verify in each batch
        concurrency_limit: Maximum number of concurrent verification tasks
        
    Returns:
        Dictionary mapping items to verification results
    """
    results = {}
    semaphore = asyncio.Semaphore(concurrency_limit)
    
    async def verify_with_semaphore(item):
        async with semaphore:
            try:
                return item, await verify_func(item)
            except Exception as e:
                logger.exception(f"Error verifying item {item}: {e}")
                return item, False
    
    # Process in batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_tasks = [verify_with_semaphore(item) for item in batch]
        batch_results = await asyncio.gather(*batch_tasks)
        
        # Add batch results to overall results
        for item, result in batch_results:
            results[item] = result
    
    return results