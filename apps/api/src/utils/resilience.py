"""
Resilience utilities.

This module provides utilities for implementing resilience patterns such as
circuit breakers, retries, and timeouts.
"""

import logging
import time
import asyncio
import enum
from typing import Dict, Any, Callable, TypeVar, Awaitable
from functools import wraps

logger = logging.getLogger(__name__)

# Circuit breaker states
class CircuitState(enum.Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests flow through
    OPEN = "open"      # Failing, requests are rejected
    HALF_OPEN = "half_open"  # Testing if service is recovered

# Type for wrapped functions
T = TypeVar("T")

class CircuitBreaker:
    """
    Circuit breaker implementation.
    
    The circuit breaker pattern prevents cascading failures by stopping requests
    to a failing service.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_timeout: float = 5.0,
    ):
        """
        Initialize a circuit breaker.
        
        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds before trying to recover
            half_open_timeout: Time in seconds between allowing requests in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_timeout = half_open_timeout
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.last_success_time = 0
        
        logger.info(
            f"Circuit breaker '{name}' initialized with "
            f"failure_threshold={failure_threshold}, "
            f"recovery_timeout={recovery_timeout}s"
        )
    
    def allow_request(self) -> bool:
        """
        Check if a request should be allowed.
        
        Returns:
            bool: True if request is allowed, False otherwise
        """
        if self.state == CircuitState.CLOSED:
            return True
            
        if self.state == CircuitState.OPEN:
            now = time.time()
            if now - self.last_failure_time > self.recovery_timeout:
                logger.info(f"Circuit breaker '{self.name}' transitioning from open to half-open")
                self.state = CircuitState.HALF_OPEN
                return True
            return False
            
        # Half-open state
        now = time.time()
        if now - self.last_success_time > self.half_open_timeout:
            return True
        return False
    
    def record_success(self) -> None:
        """Record a successful operation."""
        self.last_success_time = time.time()
        
        if self.state != CircuitState.CLOSED:
            logger.info(f"Circuit breaker '{self.name}' reset to closed after success")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            logger.warning(f"Circuit breaker '{self.name}' tripped open after {self.failure_count} failures")
            self.state = CircuitState.OPEN

# Global registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(name: str) -> CircuitBreaker:
    """
    Get a circuit breaker by name.
    
    If the circuit breaker doesn't exist, it will be created.
    
    Args:
        name: Name of the circuit breaker
        
    Returns:
        CircuitBreaker: The circuit breaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name)
    return _circuit_breakers[name]

def with_circuit_breaker(
    circuit_breaker_name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    fallback_value: Any = None,
):
    """
    Decorator for wrapping a function with a circuit breaker.
    
    Args:
        circuit_breaker_name: Name of the circuit breaker
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Time in seconds before trying to recover
        fallback_value: Value to return when circuit is open
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Get or create circuit breaker
            cb = get_circuit_breaker(circuit_breaker_name)
            cb.failure_threshold = failure_threshold
            cb.recovery_timeout = recovery_timeout
            
            # Check if request is allowed
            if not cb.allow_request():
                logger.warning(f"Circuit breaker '{circuit_breaker_name}' is open, request rejected")
                return fallback_value
            
            try:
                # Call the wrapped function
                result = await func(*args, **kwargs)
                
                # Record success
                cb.record_success()
                
                return result
            except Exception as e:
                # Record failure
                cb.record_failure()
                
                logger.error(f"Circuit breaker '{circuit_breaker_name}' recorded failure: {e}")
                raise
                
        return wrapper
    return decorator

async def with_timeout(seconds: float, coro: Awaitable[T]) -> T:
    """
    Run a coroutine with a timeout.
    
    Args:
        seconds: Timeout in seconds
        coro: Coroutine to run
        
    Returns:
        Any: The result of the coroutine
        
    Raises:
        asyncio.TimeoutError: If the coroutine times out
    """
    return await asyncio.wait_for(coro, timeout=seconds)