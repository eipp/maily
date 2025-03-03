"""
Resilience utilities for the API service.

This module provides resilience engineering utilities for the API service,
including circuit breakers, retry mechanisms, and rate limiting.
"""

import logging
import time
import asyncio
import functools
from typing import Dict, Any, Optional, TypeVar, Callable, Awaitable, cast
from enum import Enum

logger = logging.getLogger(__name__)

# Type variables for better type hinting
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])
AsyncF = TypeVar('AsyncF', bound=Callable[..., Awaitable[Any]])

class RateLimiter:
    """
    Token bucket rate limiter implementation.
    
    This class implements the token bucket algorithm for rate limiting.
    """
    
    def __init__(
        self,
        name: str,
        tokens_per_second: float,
        bucket_size: int,
    ):
        """
        Initialize a rate limiter.
        
        Args:
            name: Name of the rate limiter (used for logging)
            tokens_per_second: Rate at which tokens are added to the bucket
            bucket_size: Maximum number of tokens the bucket can hold
        """
        self.name = name
        self.tokens_per_second = tokens_per_second
        self.bucket_size = bucket_size
        
        self.tokens = bucket_size
        self.last_refill_time = time.time()
        
        logger.info(f"Rate limiter '{name}' initialized")
    
    def _refill(self) -> None:
        """Refill the token bucket based on elapsed time."""
        current_time = time.time()
        elapsed = current_time - self.last_refill_time
        
        # Calculate how many tokens to add based on elapsed time
        new_tokens = elapsed * self.tokens_per_second
        
        # Update token count, but don't exceed bucket size
        self.tokens = min(self.tokens + new_tokens, self.bucket_size)
        
        # Update last refill time
        self.last_refill_time = current_time
    
    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens were acquired, False otherwise
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    async def acquire_async(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket (async version).
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens were acquired, False otherwise
        """
        return self.acquire(tokens)


# Global registry of rate limiters
_rate_limiters: Dict[str, RateLimiter] = {}


def get_rate_limiter(name: str) -> RateLimiter:
    """
    Get a rate limiter by name, creating it if it doesn't exist.
    
    Args:
        name: Name of the rate limiter
        
    Returns:
        The rate limiter instance
    """
    if name not in _rate_limiters:
        # Default to 10 requests per second with a bucket size of 20
        _rate_limiters[name] = RateLimiter(name, 10.0, 20)
    
    return _rate_limiters[name]


def configure_rate_limiter(
    name: str,
    tokens_per_second: float,
    bucket_size: int,
) -> RateLimiter:
    """
    Configure a rate limiter with the given parameters.
    
    Args:
        name: Name of the rate limiter
        tokens_per_second: Rate at which tokens are added to the bucket
        bucket_size: Maximum number of tokens the bucket can hold
        
    Returns:
        The configured rate limiter instance
    """
    _rate_limiters[name] = RateLimiter(
        name=name,
        tokens_per_second=tokens_per_second,
        bucket_size=bucket_size,
    )
    
    return _rate_limiters[name]


class RateLimitExceededError(Exception):
    """Exception raised when a rate limit is exceeded."""
    
    def __init__(self, limiter_name: str):
        self.limiter_name = limiter_name
        super().__init__(f"Rate limit exceeded for '{limiter_name}'")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"  # Normal operation, requests are allowed
    OPEN = "OPEN"      # Circuit is open, requests are not allowed
    HALF_OPEN = "HALF_OPEN"  # Testing if the service is back to normal


class CircuitBreaker:
    """
    Circuit breaker implementation for external dependencies.
    
    This class implements the circuit breaker pattern to prevent cascading failures
    when external dependencies are unavailable or experiencing issues.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
        excluded_exceptions: Optional[list] = None,
    ):
        """
        Initialize a circuit breaker.
        
        Args:
            name: Name of the circuit breaker (used for logging)
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds before trying to recover (half-open state)
            half_open_max_calls: Maximum number of calls allowed in half-open state
            excluded_exceptions: List of exception types that should not count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.excluded_exceptions = excluded_exceptions or []
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    def allow_request(self) -> bool:
        """
        Check if a request should be allowed based on the circuit state.
        
        Returns:
            True if the request should be allowed, False otherwise
        """
        current_time = time.time()
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if current_time - self.last_failure_time >= self.recovery_timeout:
                logger.info(f"Circuit breaker '{self.name}' transitioning from OPEN to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                return False
        
        if self.state == CircuitState.HALF_OPEN and self.half_open_calls >= self.half_open_max_calls:
            return False
        
        return True
    
    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            
            # If we've reached the threshold of successful calls in half-open state,
            # close the circuit
            if self.half_open_calls >= self.half_open_max_calls:
                logger.info(f"Circuit breaker '{self.name}' transitioning from HALF_OPEN to CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
        
        # Reset failure count on success in closed state
        if self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self, exception: Exception) -> None:
        """
        Record a failed call.
        
        Args:
            exception: The exception that caused the failure
        """
        # Don't count excluded exceptions as failures
        if any(isinstance(exception, exc_type) for exc_type in self.excluded_exceptions):
            return
        
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            
            if self.failure_count >= self.failure_threshold:
                logger.warning(f"Circuit breaker '{self.name}' transitioning from CLOSED to OPEN")
                self.state = CircuitState.OPEN
        
        elif self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit breaker '{self.name}' transitioning from HALF_OPEN to OPEN")
            self.state = CircuitState.OPEN


class CircuitBreakerOpenError(Exception):
    """Exception raised when a circuit breaker is open."""
    
    def __init__(self, circuit_name: str):
        self.circuit_name = circuit_name
        super().__init__(f"Circuit breaker '{circuit_name}' is open")


# Global registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """
    Get a circuit breaker by name, creating it if it doesn't exist.
    
    Args:
        name: Name of the circuit breaker
        
    Returns:
        The circuit breaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name)
    
    return _circuit_breakers[name]


def configure_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    half_open_max_calls: int = 3,
    excluded_exceptions: Optional[list] = None,
) -> CircuitBreaker:
    """
    Configure a circuit breaker with the given parameters.
    
    Args:
        name: Name of the circuit breaker
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Time in seconds before trying to recover (half-open state)
        half_open_max_calls: Maximum number of calls allowed in half-open state
        excluded_exceptions: List of exception types that should not count as failures
        
    Returns:
        The configured circuit breaker instance
    """
    _circuit_breakers[name] = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        half_open_max_calls=half_open_max_calls,
        excluded_exceptions=excluded_exceptions,
    )
    
    return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    half_open_max_calls: int = 3,
    excluded_exceptions: Optional[list] = None,
    fallback_function: Optional[Callable] = None,
) -> Callable[[F], F]:
    """
    Decorator to apply a circuit breaker to a function.
    
    Args:
        name: Name of the circuit breaker
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Time in seconds before trying to recover (half-open state)
        half_open_max_calls: Maximum number of calls allowed in half-open state
        excluded_exceptions: List of exception types that should not count as failures
        fallback_function: Function to call when the circuit is open
        
    Returns:
        Decorated function with circuit breaker applied
    """
    # Configure the circuit breaker
    cb = configure_circuit_breaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        half_open_max_calls=half_open_max_calls,
        excluded_exceptions=excluded_exceptions,
    )
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not cb.allow_request():
                if fallback_function:
                    return fallback_function(*args, **kwargs)
                raise CircuitBreakerOpenError(cb.name)
            
            try:
                result = func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure(e)
                raise
        
        return cast(F, wrapper)
    
    return decorator


def async_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    half_open_max_calls: int = 3,
    excluded_exceptions: Optional[list] = None,
    fallback_function: Optional[Callable] = None,
) -> Callable[[AsyncF], AsyncF]:
    """
    Decorator to apply a circuit breaker to an async function.
    
    Args:
        name: Name of the circuit breaker
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Time in seconds before trying to recover (half-open state)
        half_open_max_calls: Maximum number of calls allowed in half-open state
        excluded_exceptions: List of exception types that should not count as failures
        fallback_function: Function to call when the circuit is open
        
    Returns:
        Decorated async function with circuit breaker applied
    """
    # Configure the circuit breaker
    cb = configure_circuit_breaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        half_open_max_calls=half_open_max_calls,
        excluded_exceptions=excluded_exceptions,
    )
    
    def decorator(func: AsyncF) -> AsyncF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not cb.allow_request():
                if fallback_function:
                    if asyncio.iscoroutinefunction(fallback_function):
                        return await fallback_function(*args, **kwargs)
                    return fallback_function(*args, **kwargs)
                raise CircuitBreakerOpenError(cb.name)
            
            try:
                result = await func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure(e)
                raise
        
        return cast(AsyncF, wrapper)
    
    return decorator
