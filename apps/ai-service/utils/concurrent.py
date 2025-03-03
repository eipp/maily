"""
Utilities for concurrent processing in the AI Mesh Network
"""

import asyncio
import logging
from typing import List, Dict, Any, Callable, TypeVar, Awaitable, Optional, Tuple, Union

logger = logging.getLogger("ai_service.utils.concurrent")

T = TypeVar('T')
R = TypeVar('R')

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for handling failing services
    
    The circuit breaker monitors for failures and prevents operation execution
    when the failure rate exceeds a threshold, allowing the service to recover.
    
    States:
    - CLOSED: Normal operation, service is functioning correctly
    - OPEN: Service is failing, requests are immediately rejected
    - HALF_OPEN: Trial period to test if service has recovered
    """
    
    # Circuit states
    CLOSED = 'closed'      # Normal operation
    OPEN = 'open'          # No requests allowed
    HALF_OPEN = 'half_open'  # Testing recovery
    
    def __init__(
        self, 
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_trials: int = 3,
        reset_timeout: float = 300.0
    ):
        """
        Initialize the circuit breaker
        
        Args:
            name: Identifier for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds to wait before testing recovery
            half_open_max_trials: Max number of trials in half-open state
            reset_timeout: Time in seconds to force reset circuit if stuck
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_trials = half_open_max_trials
        self.reset_timeout = reset_timeout
        
        # State management
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.last_state_change_time = 0
        self.half_open_trial_count = 0
        
        # Success/failure tracking
        self.success_count = 0
        self.total_failures = 0
        self.consecutive_successes = 0
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    async def execute(
        self, 
        func: Callable[..., Awaitable[T]], 
        *args, 
        fallback: Optional[Callable[..., Awaitable[T]]] = None,
        **kwargs
    ) -> T:
        """
        Execute the function with circuit breaker protection
        
        Args:
            func: Async function to execute
            *args: Arguments to pass to the function
            fallback: Optional fallback function if circuit is open
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function or fallback
            
        Raises:
            Exception: If the circuit is open and no fallback is provided
        """
        import time
        current_time = time.time()
        
        # Check for force reset if circuit has been in non-closed state too long
        if (self.state != self.CLOSED and 
            current_time - self.last_state_change_time > self.reset_timeout):
            logger.warning(f"Circuit '{self.name}' force reset after {self.reset_timeout}s in {self.state} state")
            self._reset_to_closed()
        
        # Check circuit state
        if self.state == self.OPEN:
            # Check if recovery timeout has elapsed
            if current_time - self.last_failure_time > self.recovery_timeout:
                logger.info(f"Circuit '{self.name}' transitioning from OPEN to HALF_OPEN after recovery timeout")
                self.state = self.HALF_OPEN
                self.half_open_trial_count = 0
                self.last_state_change_time = current_time
            else:
                # Circuit is open, use fallback or raise exception
                if fallback:
                    logger.info(f"Circuit '{self.name}' is OPEN, using fallback")
                    return await fallback(*args, **kwargs)
                else:
                    logger.warning(f"Circuit '{self.name}' is OPEN, no fallback provided")
                    raise CircuitBreakerOpenException(f"Circuit '{self.name}' is open")
        
        # Execute function (in CLOSED or HALF_OPEN state)
        try:
            result = await func(*args, **kwargs)
            
            # Handle success
            self.success_count += 1
            self.consecutive_successes += 1
            
            # If in HALF_OPEN, check if we should close the circuit
            if self.state == self.HALF_OPEN:
                self.half_open_trial_count += 1
                if self.half_open_trial_count >= self.half_open_max_trials:
                    logger.info(f"Circuit '{self.name}' transitioning from HALF_OPEN to CLOSED after {self.half_open_trial_count} successful trials")
                    self._reset_to_closed()
            
            return result
            
        except Exception as e:
            # Handle failure
            self.failure_count += 1
            self.total_failures += 1
            self.consecutive_successes = 0
            self.last_failure_time = current_time
            
            # Update circuit state based on failure
            if self.state == self.CLOSED and self.failure_count >= self.failure_threshold:
                logger.warning(f"Circuit '{self.name}' transitioning from CLOSED to OPEN after {self.failure_count} failures")
                self.state = self.OPEN
                self.last_state_change_time = current_time
            elif self.state == self.HALF_OPEN:
                logger.warning(f"Circuit '{self.name}' transitioning from HALF_OPEN to OPEN after failure during trial")
                self.state = self.OPEN
                self.last_state_change_time = current_time
            
            # Use fallback or re-raise
            if fallback:
                logger.info(f"Circuit '{self.name}' using fallback after failure: {str(e)}")
                return await fallback(*args, **kwargs)
            else:
                raise
    
    def _reset_to_closed(self):
        """Reset the circuit to closed state"""
        self.state = self.CLOSED
        self.failure_count = 0
        self.half_open_trial_count = 0
        self.last_state_change_time = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the circuit breaker"""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_failures": self.total_failures,
            "consecutive_successes": self.consecutive_successes,
            "half_open_trial_count": self.half_open_trial_count,
        }


class CircuitBreakerOpenException(Exception):
    """Exception raised when a circuit breaker is open"""
    pass


async def process_concurrently(
    items: List[Any],
    processor: Callable[[Any], Awaitable[R]],
    max_concurrency: int = 10,
    ordered: bool = True
) -> List[R]:
    """
    Process items concurrently with a maximum concurrency limit
    
    Args:
        items: List of items to process
        processor: Async function that processes a single item
        max_concurrency: Maximum number of concurrent tasks
        ordered: Whether to return results in the same order as inputs
        
    Returns:
        List of results from processing each item
    """
    if not items:
        return []
    
    # Use semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def process_with_semaphore(i: int, item: Any) -> Tuple[int, R]:
        """Process an item with semaphore control and track original index"""
        async with semaphore:
            try:
                result = await processor(item)
                return i, result
            except Exception as e:
                logger.error(f"Error processing item {i}: {str(e)}")
                raise
    
    # Create tasks with index tracking
    tasks = [
        asyncio.create_task(process_with_semaphore(i, item))
        for i, item in enumerate(items)
    ]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    processed_results = []
    for i, result in results:
        if isinstance(result, Exception):
            logger.error(f"Task {i} raised exception: {result}")
            # Re-raise the exception if needed
            # raise result
            processed_results.append((i, None))
        else:
            processed_results.append((i, result))
    
    # Return in original order if required
    if ordered:
        processed_results.sort(key=lambda x: x[0])
        return [r for _, r in processed_results]
    else:
        return [r for _, r in processed_results if r is not None]


async def with_retry(
    func: Callable[..., Awaitable[T]],
    *args,
    retry_count: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 10.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_exceptions: Tuple[Exception, ...] = (Exception,),
    **kwargs
) -> T:
    """
    Execute a function with exponential backoff retry
    
    Args:
        func: Async function to execute
        *args: Arguments to pass to the function
        retry_count: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        backoff_factor: Factor to multiply backoff time by after each retry
        jitter: Whether to add randomness to backoff time
        retry_exceptions: Exceptions to retry on
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function
        
    Raises:
        Exception: If all retry attempts fail
    """
    import random
    
    last_exception = None
    
    for attempt in range(retry_count + 1):
        try:
            return await func(*args, **kwargs)
        except retry_exceptions as e:
            last_exception = e
            
            if attempt == retry_count:
                logger.error(f"All {retry_count} retry attempts failed")
                raise
            
            # Calculate backoff time
            backoff = min(
                initial_backoff * (backoff_factor ** attempt),
                max_backoff
            )
            
            # Add jitter to prevent thundering herd
            if jitter:
                backoff = backoff * (0.5 + random.random())
            
            logger.warning(f"Attempt {attempt + 1}/{retry_count + 1} failed: {str(e)}. Retrying in {backoff:.2f}s")
            await asyncio.sleep(backoff)
    
    # This should never happen, but just in case
    raise last_exception or RuntimeError("Unexpected error in retry logic")


class AsyncTaskManager:
    """
    Manages a pool of async tasks with priority and dependency tracking
    """
    
    def __init__(self, max_concurrency: int = 10):
        """
        Initialize the task manager
        
        Args:
            max_concurrency: Maximum number of concurrent tasks
        """
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.tasks = {}
        self.results = {}
        self.pending_tasks = set()
        self.completed_tasks = set()
        self.failed_tasks = set()
    
    async def execute_task(
        self, 
        task_id: str, 
        func: Callable[..., Awaitable[T]], 
        *args, 
        priority: int = 0,
        dependencies: List[str] = None,
        **kwargs
    ) -> T:
        """
        Execute a task with dependency tracking
        
        Args:
            task_id: Unique identifier for the task
            func: Async function to execute
            *args: Arguments to pass to the function
            priority: Task priority (higher is more important)
            dependencies: List of task IDs that must complete before this task
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the task
        """
        # Check if task already executed
        if task_id in self.results:
            return self.results[task_id]
        
        # Check dependencies
        dependencies = dependencies or []
        for dep_id in dependencies:
            if dep_id not in self.completed_tasks:
                if dep_id in self.failed_tasks:
                    raise DependencyFailedException(f"Dependency {dep_id} failed")
                if dep_id not in self.pending_tasks:
                    raise DependencyNotFoundException(f"Dependency {dep_id} not found")
                # Wait for dependency to complete
                await self.wait_for_task(dep_id)
        
        # Add to pending tasks
        self.pending_tasks.add(task_id)
        
        # Execute task with semaphore
        async with self.semaphore:
            try:
                result = await func(*args, **kwargs)
                self.results[task_id] = result
                self.completed_tasks.add(task_id)
                self.pending_tasks.remove(task_id)
                return result
            except Exception as e:
                self.failed_tasks.add(task_id)
                self.pending_tasks.remove(task_id)
                logger.error(f"Task {task_id} failed: {str(e)}")
                raise
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Wait for a specific task to complete
        
        Args:
            task_id: ID of task to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Result of the task
            
        Raises:
            TimeoutError: If timeout is reached
            TaskFailedException: If the task failed
        """
        if task_id in self.completed_tasks:
            return self.results[task_id]
        
        if task_id in self.failed_tasks:
            raise TaskFailedException(f"Task {task_id} failed")
        
        if task_id not in self.pending_tasks:
            raise TaskNotFoundException(f"Task {task_id} not found")
        
        # Wait for task to complete or timeout
        start_time = time.time()
        while task_id in self.pending_tasks:
            if timeout and time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout waiting for task {task_id}")
            await asyncio.sleep(0.1)
        
        if task_id in self.completed_tasks:
            return self.results[task_id]
        else:
            raise TaskFailedException(f"Task {task_id} failed")
    
    async def wait_all(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Wait for all pending tasks to complete
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Dictionary of task results
            
        Raises:
            TimeoutError: If timeout is reached
        """
        if not self.pending_tasks:
            return self.results
        
        # Wait for all tasks to complete or timeout
        start_time = time.time()
        while self.pending_tasks:
            if timeout and time.time() - start_time > timeout:
                remaining = len(self.pending_tasks)
                raise TimeoutError(f"Timeout waiting for {remaining} tasks to complete")
            await asyncio.sleep(0.1)
        
        return self.results
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get current status of all tasks"""
        return {
            "pending": list(self.pending_tasks),
            "completed": list(self.completed_tasks),
            "failed": list(self.failed_tasks),
            "total_tasks": len(self.pending_tasks) + len(self.completed_tasks) + len(self.failed_tasks),
        }


class DependencyFailedException(Exception):
    """Exception raised when a task dependency has failed"""
    pass


class DependencyNotFoundException(Exception):
    """Exception raised when a task dependency is not found"""
    pass


class TaskFailedException(Exception):
    """Exception raised when a task has failed"""
    pass


class TaskNotFoundException(Exception):
    """Exception raised when a task is not found"""
    pass