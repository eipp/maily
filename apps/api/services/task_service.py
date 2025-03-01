"""
Background task processing service.

This service provides task tracking, retry mechanisms, and status updates
for background tasks in the API.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Awaitable

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')
TaskResult = TypeVar('TaskResult')
TaskFunction = Callable[..., Awaitable[Any]]


class TaskStatus(str, Enum):
    """Task status enum."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class TaskPriority(int, Enum):
    """Task priority enum."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskService:
    """Service for managing background tasks."""

    def __init__(self, db=None, redis_client=None):
        """
        Initialize the task service.

        Args:
            db: Database connection
            redis_client: Redis client for caching
        """
        self.db = db
        self.redis_client = redis_client
        self.tasks = {}  # In-memory task storage (for demo/testing)
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    async def create_task(
        self,
        function: TaskFunction,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new background task.

        Args:
            function: Async function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            task_id: Optional task ID (generated if not provided)
            priority: Task priority
            metadata: Additional metadata

        Returns:
            Task ID
        """
        # Generate task ID if not provided
        task_id = task_id or str(uuid.uuid4())

        # Create task data
        task_data = {
            "task_id": task_id,
            "status": TaskStatus.PENDING,
            "function": function.__name__,
            "args": args or [],
            "kwargs": kwargs or {},
            "priority": priority.value,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "completed_at": None,
            "result": None,
            "error": None,
            "retries": 0,
            "progress": 0
        }

        # Store task data
        self.tasks[task_id] = task_data

        # Store in Redis for quick access
        if self.redis_client:
            try:
                # Convert function to string since it's not JSON serializable
                redis_task = task_data.copy()
                redis_task["function"] = function.__name__

                self.redis_client.setex(
                    f"task:{task_id}",
                    86400,  # 1 day TTL
                    json.dumps(redis_task)
                )
            except Exception as e:
                logger.error(f"Failed to store task in Redis: {e}")

        # Store in database
        if self.db:
            try:
                # Database storage implementation would go here
                pass
            except Exception as e:
                logger.error(f"Failed to store task in database: {e}")

        # Schedule task execution
        asyncio.create_task(self._execute_task(task_id, function, args or [], kwargs or {}))

        return task_id

    async def _execute_task(
        self,
        task_id: str,
        function: TaskFunction,
        args: List[Any],
        kwargs: Dict[str, Any]
    ) -> None:
        """
        Execute a background task with retry logic.

        Args:
            task_id: Task ID
            function: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
        """
        # Update task status
        await self.update_task_status(task_id, TaskStatus.RUNNING)

        retries = 0
        while retries <= self.max_retries:
            try:
                # Execute function
                result = await function(*args, **kwargs)

                # Update task with result
                await self.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    result=result,
                    completed_at=datetime.now().isoformat(),
                    progress=100
                )

                logger.info(f"Task {task_id} completed successfully")
                return

            except Exception as e:
                logger.error(f"Task {task_id} failed: {str(e)}")

                # Increment retry count
                retries += 1

                if retries <= self.max_retries:
                    # Update status to retrying
                    await self.update_task(
                        task_id,
                        status=TaskStatus.RETRYING,
                        error=str(e),
                        retries=retries
                    )

                    # Wait before retrying
                    await asyncio.sleep(self.retry_delay * retries)
                else:
                    # Max retries exceeded, mark as failed
                    await self.update_task(
                        task_id,
                        status=TaskStatus.FAILED,
                        error=str(e),
                        retries=retries
                    )
                    return

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus
    ) -> None:
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status
        """
        await self.update_task(task_id, status=status)

    async def update_task_progress(
        self,
        task_id: str,
        progress: int
    ) -> None:
        """
        Update task progress.

        Args:
            task_id: Task ID
            progress: Progress percentage (0-100)
        """
        await self.update_task(task_id, progress=progress)

    async def update_task(
        self,
        task_id: str,
        **updates
    ) -> None:
        """
        Update task data.

        Args:
            task_id: Task ID
            **updates: Fields to update
        """
        # Get current task data
        task_data = self.tasks.get(task_id)
        if not task_data:
            logger.error(f"Task {task_id} not found")
            return

        # Update fields
        for key, value in updates.items():
            if key in task_data:
                task_data[key] = value

        # Update timestamp
        task_data["updated_at"] = datetime.now().isoformat()

        # Store updated task data
        self.tasks[task_id] = task_data

        # Update in Redis
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"task:{task_id}",
                    86400,  # 1 day TTL
                    json.dumps(task_data)
                )
            except Exception as e:
                logger.error(f"Failed to update task in Redis: {e}")

        # Update in database
        if self.db:
            try:
                # Database update implementation would go here
                pass
            except Exception as e:
                logger.error(f"Failed to update task in database: {e}")

    async def get_task_status(
        self,
        task_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get task status.

        Args:
            task_id: Task ID

        Returns:
            Task status data or None if not found
        """
        # Try Redis first
        if self.redis_client:
            try:
                cached = self.redis_client.get(f"task:{task_id}")
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Failed to get task from Redis: {e}")

        # Try in-memory cache
        if task_id in self.tasks:
            return self.tasks[task_id]

        # Try database
        if self.db:
            try:
                # Database query implementation would go here
                pass
            except Exception as e:
                logger.error(f"Failed to get task from database: {e}")

        return None

    async def cancel_task(
        self,
        task_id: str
    ) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task ID

        Returns:
            True if cancelled, False otherwise
        """
        task_data = await self.get_task_status(task_id)
        if not task_data:
            return False

        # Can only cancel pending or running tasks
        if task_data["status"] not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            return False

        # Update status
        await self.update_task(task_id, status=TaskStatus.CANCELLED)

        return True

    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filtering.

        Args:
            status: Optional status filter
            limit: Maximum number of tasks to return
            offset: Offset for pagination

        Returns:
            List of task data
        """
        # Filter tasks by status if provided
        if status:
            filtered_tasks = [
                task for task in self.tasks.values()
                if task["status"] == status
            ]
        else:
            filtered_tasks = list(self.tasks.values())

        # Sort by created_at
        sorted_tasks = sorted(
            filtered_tasks,
            key=lambda x: x["created_at"],
            reverse=True
        )

        # Apply pagination
        paginated_tasks = sorted_tasks[offset:offset + limit]

        return paginated_tasks

    async def cleanup_old_tasks(
        self,
        days: int = 7
    ) -> int:
        """
        Clean up old tasks.

        Args:
            days: Number of days to keep tasks

        Returns:
            Number of tasks cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_date_str = cutoff_date.isoformat()

        # Find old tasks
        old_task_ids = [
            task_id for task_id, task in self.tasks.items()
            if task["created_at"] < cutoff_date_str
        ]

        # Delete old tasks
        for task_id in old_task_ids:
            # Delete from in-memory cache
            if task_id in self.tasks:
                del self.tasks[task_id]

            # Delete from Redis
            if self.redis_client:
                try:
                    self.redis_client.delete(f"task:{task_id}")
                except Exception as e:
                    logger.error(f"Failed to delete task from Redis: {e}")

            # Delete from database
            if self.db:
                try:
                    # Database delete implementation would go here
                    pass
                except Exception as e:
                    logger.error(f"Failed to delete task from database: {e}")

        return len(old_task_ids)


# Create a singleton instance
task_service = TaskService()
