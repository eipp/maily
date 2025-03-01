"""
Enhanced OctoOrchestrator for advanced AI agent orchestration.
Provides intelligent routing, monitoring, and failover capabilities.
"""
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from enum import Enum
import asyncio
import time
import random
import uuid
import json
import structlog
from datetime import datetime, timedelta

from ..adapters.base import ModelAdapter
from ..monitoring.ai_usage_tracker import AIUsageTracker
from ..errors import AIGenerationError, InvalidInputError, RoutingError

logger = structlog.get_logger(__name__)

class AgentType(str, Enum):
    """Types of agents in the system."""
    CONTENT = "content"
    ANALYTICS = "analytics"
    DISPATCHER = "dispatcher"
    EVALUATOR = "evaluator"
    VALIDATOR = "validator"
    SUMMARIZER = "summarizer"
    RESEARCHER = "researcher"
    PERSONALIZATION = "personalization"

class AgentLevel(int, Enum):
    """Agent capability levels."""
    BASIC = 1        # Basic capabilities, simple tasks
    STANDARD = 2     # Standard capabilities, common tasks
    ADVANCED = 3     # Advanced capabilities, complex tasks
    EXPERT = 4       # Expert capabilities, specialized tasks
    ORCHESTRATOR = 5 # Orchestration capabilities, can manage other agents

class TaskPriority(int, Enum):
    """Task priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class TaskStatus(str, Enum):
    """Task status states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    TIMEOUT = "timeout"

class AgentInterface:
    """Interface for AI agents that can process tasks."""

    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        level: AgentLevel = AgentLevel.STANDARD,
        model_adapter: Optional[ModelAdapter] = None,
        capabilities: Set[str] = None,
        max_concurrent_tasks: int = 5
    ):
        """Initialize agent interface.

        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent
            level: Agent capability level
            model_adapter: Optional model adapter for this agent
            capabilities: Set of specific capabilities this agent has
            max_concurrent_tasks: Maximum concurrent tasks this agent can handle
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.level = level
        self.model_adapter = model_adapter
        self.capabilities = capabilities or set()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.active_tasks = 0
        self.total_tasks = 0
        self.success_count = 0
        self.failure_count = 0
        self.average_duration_ms = 0
        self.last_used = datetime.now()

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task.

        Args:
            task: Task data

        Returns:
            Task result

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement process_task method")

    def get_load(self) -> float:
        """Get current agent load ratio (0.0 to 1.0).

        Returns:
            Load ratio from 0.0 (idle) to 1.0 (fully loaded)
        """
        return self.active_tasks / self.max_concurrent_tasks if self.max_concurrent_tasks > 0 else 1.0

    def is_available(self) -> bool:
        """Check if agent is available for new tasks.

        Returns:
            True if agent can accept new tasks, False otherwise
        """
        return self.active_tasks < self.max_concurrent_tasks

    def update_stats(
        self,
        success: bool,
        duration_ms: float
    ) -> None:
        """Update agent performance statistics.

        Args:
            success: Whether the task succeeded
            duration_ms: Task duration in milliseconds
        """
        self.total_tasks += 1
        self.last_used = datetime.now()

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

        # Update rolling average duration
        if self.average_duration_ms == 0:
            self.average_duration_ms = duration_ms
        else:
            # Use exponential moving average with 0.1 weight for new values
            self.average_duration_ms = (0.9 * self.average_duration_ms) + (0.1 * duration_ms)

    def can_handle_task(self, task_requirements: Dict[str, Any]) -> bool:
        """Check if agent can handle specific task requirements.

        Args:
            task_requirements: Task requirements specification

        Returns:
            True if agent meets requirements, False otherwise
        """
        # Check agent type
        if task_requirements.get("agent_type") and self.agent_type != task_requirements["agent_type"]:
            return False

        # Check minimum level
        if task_requirements.get("min_level") and self.level < task_requirements["min_level"]:
            return False

        # Check required capabilities
        required_capabilities = task_requirements.get("capabilities", set())
        if required_capabilities and not required_capabilities.issubset(self.capabilities):
            return False

        return True

class EnhancedOctoOrchestrator:
    """Enhanced orchestrator with advanced routing and monitoring.

    Attributes:
        agents: Dictionary of agent lists by agent type
        tasks: Dictionary of task data by task ID
        performance_metrics: Agent and task performance metrics
        usage_tracker: AI usage tracking
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize enhanced orchestrator.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.agents: Dict[AgentType, List[AgentInterface]] = {
            agent_type: [] for agent_type in AgentType
        }
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics: Dict[str, Dict[str, Any]] = {
            "agents": {},
            "tasks": {},
            "routes": {}
        }
        self.usage_tracker = AIUsageTracker()

        # Initialize task queue and workers
        self.task_queues: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in TaskPriority
        }
        self.worker_tasks: List[asyncio.Task] = []
        self.worker_count = self.config.get("worker_count", 10)
        self.running = False

        # Enhanced configs
        self.failover_retries = self.config.get("failover_retries", 2)
        self.timeout_seconds = self.config.get("timeout_seconds", 30)
        self.health_check_interval = self.config.get("health_check_interval", 60)
        self.auto_scaling = self.config.get("auto_scaling", True)

        # Initialize routing policy
        self.routing_policy = self.config.get("routing_policy", "load_balanced")

        # Performance history for intelligent routing
        self.task_type_history: Dict[str, List[Dict[str, Any]]] = {}

        logger.info("Enhanced OctoOrchestrator initialized",
                    worker_count=self.worker_count,
                    routing_policy=self.routing_policy,
                    auto_scaling=self.auto_scaling)

    def register_agent(self, agent: AgentInterface) -> None:
        """Register an agent for task processing.

        Args:
            agent: Agent to register
        """
        agent_type = agent.agent_type
        self.agents[agent_type].append(agent)

        # Initialize performance metrics
        self.performance_metrics["agents"][agent.agent_id] = {
            "agent_type": agent_type,
            "level": agent.level,
            "capabilities": list(agent.capabilities),
            "success_rate": 0.0,
            "average_duration_ms": 0.0,
            "last_used": datetime.now().isoformat(),
            "task_count": 0
        }

        logger.info("Agent registered",
                   agent_id=agent.agent_id,
                   agent_type=agent_type,
                   level=agent.level)

    async def start(self) -> None:
        """Start the orchestrator and workers."""
        if self.running:
            return

        self.running = True

        # Start worker tasks
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._worker_loop(i))
            self.worker_tasks.append(worker)

        # Start health check task
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info("OctoOrchestrator started",
                   worker_count=len(self.worker_tasks))

    async def stop(self) -> None:
        """Stop the orchestrator and workers."""
        if not self.running:
            return

        self.running = False

        # Cancel all worker tasks
        for worker in self.worker_tasks:
            worker.cancel()

        # Cancel health check task
        self.health_check_task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        self.worker_tasks.clear()

        logger.info("OctoOrchestrator stopped")

    async def dispatch_task(
        self,
        agent_type: AgentType,
        input_data: Dict[str, Any],
        priority: int = TaskPriority.NORMAL,
        task_requirements: Dict[str, Any] = None,
        parent_task_id: Optional[str] = None
    ) -> str:
        """Dispatch a task with advanced routing and tracking.

        Args:
            agent_type: Type of agent to handle task
            input_data: Task input data
            priority: Task priority
            task_requirements: Specific requirements for the task
            parent_task_id: Optional parent task ID for subtasks

        Returns:
            Task ID for tracking

        Raises:
            RoutingError: If no suitable agent is available
        """
        task_id = str(uuid.uuid4())
        task_type = input_data.get("task_type", "default")

        # Track usage before dispatch
        self.usage_tracker.start_tracking(agent_type)

        # Create task data
        task = {
            "id": task_id,
            "agent_type": agent_type,
            "priority": priority,
            "status": TaskStatus.PENDING,
            "input_data": input_data,
            "result": None,
            "error": None,
            "requirements": task_requirements or {},
            "parent_id": parent_task_id,
            "subtasks": [],
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "duration_ms": 0,
            "task_type": task_type,
            "assigned_agent": None,
            "routing_attempts": 0
        }

        # Store task
        self.tasks[task_id] = task

        # Add task to queue
        task_priority = TaskPriority(priority)
        await self.task_queues[task_priority].put(task_id)

        logger.info("Task dispatched",
                   task_id=task_id,
                   agent_type=agent_type,
                   priority=priority,
                   task_type=task_type,
                   parent_id=parent_task_id or None)

        # If parent task, add this as subtask
        if parent_task_id and parent_task_id in self.tasks:
            self.tasks[parent_task_id]["subtasks"].append(task_id)

        return task_id

    async def get_task_result(
        self,
        task_id: str,
        wait: bool = True,
        timeout: float = None
    ) -> Dict[str, Any]:
        """Get task result, optionally waiting for completion.

        Args:
            task_id: Task ID
            wait: Whether to wait for task completion
            timeout: Optional timeout in seconds

        Returns:
            Task result data

        Raises:
            ValueError: If task ID is invalid
            asyncio.TimeoutError: If task doesn't complete within timeout
        """
        if task_id not in self.tasks:
            raise ValueError(f"Invalid task ID: {task_id}")

        if not wait or self.tasks[task_id]["status"] in [
            TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED, TaskStatus.TIMEOUT
        ]:
            return self._build_task_result(task_id)

        # Wait for task completion
        start_time = time.time()
        timeout = timeout or self.timeout_seconds

        while True:
            if self.tasks[task_id]["status"] in [
                TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED, TaskStatus.TIMEOUT
            ]:
                return self._build_task_result(task_id)

            # Check timeout
            if timeout and time.time() - start_time > timeout:
                # Update task status to timeout
                self.tasks[task_id]["status"] = TaskStatus.TIMEOUT
                self.tasks[task_id]["error"] = "Task processing timed out"

                logger.warning("Task timed out",
                              task_id=task_id,
                              timeout=timeout)

                raise asyncio.TimeoutError(f"Task {task_id} processing timed out")

            # Wait a bit before checking again
            await asyncio.sleep(0.1)

    def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status without waiting.

        Args:
            task_id: Task ID

        Returns:
            Task status data

        Raises:
            ValueError: If task ID is invalid
        """
        if task_id not in self.tasks:
            raise ValueError(f"Invalid task ID: {task_id}")

        return {
            "task_id": task_id,
            "status": self.tasks[task_id]["status"],
            "created_at": self.tasks[task_id]["created_at"],
            "started_at": self.tasks[task_id]["started_at"],
            "completed_at": self.tasks[task_id]["completed_at"],
            "agent_type": self.tasks[task_id]["agent_type"],
            "has_result": self.tasks[task_id]["result"] is not None,
            "has_error": self.tasks[task_id]["error"] is not None,
            "subtasks_count": len(self.tasks[task_id]["subtasks"])
        }

    def get_agent_stats(
        self,
        agent_type: Optional[AgentType] = None
    ) -> Dict[str, Any]:
        """Get agent performance statistics.

        Args:
            agent_type: Optional agent type to filter by

        Returns:
            Agent statistics
        """
        if agent_type:
            stats = {
                "count": len(self.agents[agent_type]),
                "available": sum(1 for agent in self.agents[agent_type] if agent.is_available()),
                "agents": {
                    agent.agent_id: {
                        "load": agent.get_load(),
                        "active_tasks": agent.active_tasks,
                        "total_tasks": agent.total_tasks,
                        "success_rate": agent.success_count / max(1, agent.total_tasks),
                        "average_duration_ms": agent.average_duration_ms,
                        "level": agent.level,
                        "last_used": agent.last_used.isoformat()
                    }
                    for agent in self.agents[agent_type]
                }
            }
        else:
            stats = {
                "count": sum(len(agents) for agents in self.agents.values()),
                "available": sum(
                    1 for agents in self.agents.values()
                    for agent in agents if agent.is_available()
                ),
                "by_type": {
                    a_type.value: {
                        "count": len(self.agents[a_type]),
                        "available": sum(1 for agent in self.agents[a_type] if agent.is_available())
                    }
                    for a_type in AgentType
                }
            }

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the orchestrator.

        Returns:
            Health check results
        """
        agent_counts = {
            a_type.value: len(agents) for a_type, agents in self.agents.items()
        }

        queue_sizes = {
            f"priority_{priority.value}": queue.qsize()
            for priority, queue in self.task_queues.items()
        }

        # Calculate task statistics
        pending_count = sum(
            1 for task in self.tasks.values()
            if task["status"] == TaskStatus.PENDING
        )

        running_count = sum(
            1 for task in self.tasks.values()
            if task["status"] == TaskStatus.RUNNING
        )

        completed_count = sum(
            1 for task in self.tasks.values()
            if task["status"] == TaskStatus.COMPLETED
        )

        failed_count = sum(
            1 for task in self.tasks.values()
            if task["status"] in [TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELED]
        )

        # Calculate success rate
        total_completed = completed_count + failed_count
        success_rate = completed_count / max(1, total_completed)

        return {
            "status": "healthy" if self.running else "stopped",
            "agents": {
                "total": sum(agent_counts.values()),
                "by_type": agent_counts
            },
            "tasks": {
                "total": len(self.tasks),
                "pending": pending_count,
                "running": running_count,
                "completed": completed_count,
                "failed": failed_count,
                "success_rate": success_rate
            },
            "queues": queue_sizes,
            "workers": {
                "total": self.worker_count,
                "active": len(self.worker_tasks)
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker loop for processing tasks.

        Args:
            worker_id: Worker identifier
        """
        logger.info("Worker started", worker_id=worker_id)

        while self.running:
            try:
                # Check queues in priority order
                task_id = None

                for priority in sorted(TaskPriority, reverse=True):
                    if not self.task_queues[priority].empty():
                        # Get task from queue
                        task_id = await self.task_queues[priority].get()
                        break

                if not task_id:
                    # No tasks available, wait a bit
                    await asyncio.sleep(0.1)
                    continue

                # Process task
                await self._process_task(task_id, worker_id)

                # Mark task as done
                self.task_queues[priority].task_done()

            except asyncio.CancelledError:
                logger.info("Worker cancelled", worker_id=worker_id)
                break

            except Exception as e:
                logger.error("Worker error",
                            worker_id=worker_id,
                            error=str(e),
                            exc_info=True)

                # Wait a bit before continuing
                await asyncio.sleep(1)

    async def _process_task(self, task_id: str, worker_id: int) -> None:
        """Process a task with the appropriate agent.

        Args:
            task_id: Task ID
            worker_id: Worker ID
        """
        task = self.tasks[task_id]
        agent_type = task["agent_type"]
        task_type = task["task_type"]

        # Update task status
        task["status"] = TaskStatus.RUNNING
        task["started_at"] = datetime.now().isoformat()
        task["routing_attempts"] += 1

        # Select optimal agent
        agent = self._select_optimal_agent(task)

        if not agent:
            task["status"] = TaskStatus.FAILED
            task["error"] = f"No available agent of type {agent_type}"
            task["completed_at"] = datetime.now().isoformat()

            logger.warning("No available agent",
                          task_id=task_id,
                          agent_type=agent_type,
                          worker_id=worker_id)

            self.usage_tracker.complete_tracking(task_id, agent_type.value, success=False)
            return

        # Track assigned agent
        task["assigned_agent"] = agent.agent_id

        # Increment agent active tasks
        agent.active_tasks += 1

        start_time = time.time()
        success = False

        try:
            # Process task with timeout
            try:
                result = await asyncio.wait_for(
                    agent.process_task(task),
                    timeout=self.timeout_seconds
                )

                # Update task result
                task["result"] = result
                task["status"] = TaskStatus.COMPLETED
                success = True

            except asyncio.TimeoutError:
                task["status"] = TaskStatus.TIMEOUT
                task["error"] = "Task processing timed out"

                logger.warning("Task processing timed out",
                              task_id=task_id,
                              agent_id=agent.agent_id,
                              worker_id=worker_id)

            except Exception as e:
                if task["routing_attempts"] <= self.failover_retries:
                    # Try routing to another agent
                    logger.warning("Task failed, attempting failover",
                                  task_id=task_id,
                                  agent_id=agent.agent_id,
                                  error=str(e),
                                  attempt=task["routing_attempts"],
                                  max_attempts=self.failover_retries)

                    # Reset task status to pending
                    task["status"] = TaskStatus.PENDING

                    # Put back in the queue
                    priority = TaskPriority(task["priority"])
                    await self.task_queues[priority].put(task_id)

                else:
                    # No more retries, mark as failed
                    task["status"] = TaskStatus.FAILED
                    task["error"] = str(e)

                    logger.error("Task failed after retries",
                                task_id=task_id,
                                agent_id=agent.agent_id,
                                worker_id=worker_id,
                                error=str(e))

        finally:
            # Update task completion data
            if task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT]:
                task["completed_at"] = datetime.now().isoformat()
                task["duration_ms"] = int((time.time() - start_time) * 1000)

                # Update agent stats
                agent.active_tasks -= 1
                agent.update_stats(
                    success=(task["status"] == TaskStatus.COMPLETED),
                    duration_ms=task["duration_ms"]
                )

                # Update performance metrics
                self._update_metrics(task_id, task_type, agent.agent_id,
                                   task["duration_ms"], success)

                # Track completion
                self.usage_tracker.complete_tracking(
                    task_id,
                    agent_type.value,
                    success=(task["status"] == TaskStatus.COMPLETED)
                )

                logger.info("Task completed",
                           task_id=task_id,
                           agent_id=agent.agent_id,
                           status=task["status"],
                           duration_ms=task["duration_ms"],
                           worker_id=worker_id)
            else:
                # Just decrement active tasks for retried tasks
                agent.active_tasks -= 1

    def _select_optimal_agent(self, task: Dict[str, Any]) -> Optional[AgentInterface]:
        """Select optimal agent for task based on routing policy.

        Args:
            task: Task data

        Returns:
            Selected agent or None if no suitable agent available
        """
        agent_type = task["agent_type"]
        requirements = task["requirements"]
        task_type = task["task_type"]

        # Filter agents by type and requirements
        available_agents = [
            agent for agent in self.agents[agent_type]
            if agent.is_available() and agent.can_handle_task(requirements)
        ]

        if not available_agents:
            return None

        # Select agent based on routing policy
        if self.routing_policy == "round_robin":
            # Simple round-robin selection
            return available_agents[0]

        elif self.routing_policy == "load_balanced":
            # Choose agent with lowest load
            return min(available_agents, key=lambda a: a.get_load())

        elif self.routing_policy == "random":
            # Random selection
            return random.choice(available_agents)

        elif self.routing_policy == "intelligent":
            # Intelligent routing based on task type and agent performance
            return self._intelligent_routing(available_agents, task_type)

        else:
            # Default to load balanced
            return min(available_agents, key=lambda a: a.get_load())

    def _intelligent_routing(
        self,
        available_agents: List[AgentInterface],
        task_type: str
    ) -> AgentInterface:
        """Intelligently route task based on historical performance.

        Args:
            available_agents: List of available agents
            task_type: Type of task

        Returns:
            Selected agent
        """
        if not available_agents:
            return None

        # If no history for this task type or very low sample size, use load balancing
        if task_type not in self.task_type_history or len(self.task_type_history[task_type]) < 5:
            return min(available_agents, key=lambda a: a.get_load())

        # Calculate scores for each agent based on performance history
        scores = {}

        for agent in available_agents:
            # Get agent's history for this task type
            agent_history = [
                entry for entry in self.task_type_history[task_type]
                if entry["agent_id"] == agent.agent_id
            ]

            if not agent_history:
                # No history for this agent and task type
                # Give it a neutral score based on level and load
                scores[agent.agent_id] = 50 * (agent.level / 5) * (1 - agent.get_load())
                continue

            # Calculate performance score
            success_rate = sum(1 for entry in agent_history if entry["success"]) / len(agent_history)

            # Calculate speed score (inverse of duration, normalized)
            durations = [entry["duration_ms"] for entry in agent_history]
            avg_duration = sum(durations) / len(durations)
            # Normalize to a 0-100 scale (lower is better)
            speed_score = 100 / (1 + (avg_duration / 1000))

            # Calculate load score
            load_score = 100 * (1 - agent.get_load())

            # Calculate recency score (favor more recent results)
            last_used_score = 100
            if agent.last_used:
                seconds_since_used = (datetime.now() - agent.last_used).total_seconds()
                # Normalize to a 0-100 scale (higher is more recent)
                last_used_score = 100 * (1 - min(1, seconds_since_used / 86400))

            # Combine scores with weights
            scores[agent.agent_id] = (
                0.4 * success_rate * 100 +  # 40% weight on success rate
                0.25 * speed_score +        # 25% weight on speed
                0.2 * load_score +          # 20% weight on current load
                0.1 * last_used_score +     # 10% weight on recency
                0.05 * (agent.level * 20)   # 5% weight on agent level
            )

        # Select agent with highest score
        best_agent_id = max(scores, key=scores.get)

        # Find the agent instance
        for agent in available_agents:
            if agent.agent_id == best_agent_id:
                return agent

        # Fallback to load balancing if something went wrong
        return min(available_agents, key=lambda a: a.get_load())

    def _update_metrics(
        self,
        task_id: str,
        task_type: str,
        agent_id: str,
        duration_ms: int,
        success: bool
    ) -> None:
        """Update performance metrics for intelligent routing.

        Args:
            task_id: Task ID
            task_type: Task type
            agent_id: Agent ID
            duration_ms: Task duration in milliseconds
            success: Whether task succeeded
        """
        # Initialize task type history if needed
        if task_type not in self.task_type_history:
            self.task_type_history[task_type] = []

        # Add entry to history
        entry = {
            "task_id": task_id,
            "agent_id": agent_id,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }

        self.task_type_history[task_type].append(entry)

        # Limit history size
        max_history = self.config.get("max_history_per_task_type", 100)
        if len(self.task_type_history[task_type]) > max_history:
            # Keep only the most recent entries
            self.task_type_history[task_type] = self.task_type_history[task_type][-max_history:]

        # Update agent metrics
        if agent_id in self.performance_metrics["agents"]:
            metrics = self.performance_metrics["agents"][agent_id]

            # Update task count
            metrics["task_count"] += 1

            # Update success rate (exponential moving average)
            success_value = 1.0 if success else 0.0
            if metrics["task_count"] == 1:
                metrics["success_rate"] = success_value
            else:
                metrics["success_rate"] = (0.9 * metrics["success_rate"]) + (0.1 * success_value)

            # Update average duration (exponential moving average)
            if metrics["average_duration_ms"] == 0:
                metrics["average_duration_ms"] = duration_ms
            else:
                metrics["average_duration_ms"] = (0.9 * metrics["average_duration_ms"]) + (0.1 * duration_ms)

            # Update last used
            metrics["last_used"] = datetime.now().isoformat()

    def _build_task_result(self, task_id: str) -> Dict[str, Any]:
        """Build complete task result including subtasks.

        Args:
            task_id: Task ID

        Returns:
            Task result data
        """
        task = self.tasks[task_id]

        result = {
            "task_id": task_id,
            "status": task["status"],
            "created_at": task["created_at"],
            "started_at": task["started_at"],
            "completed_at": task["completed_at"],
            "duration_ms": task["duration_ms"],
            "agent_type": task["agent_type"],
            "result": task["result"],
            "error": task["error"]
        }

        # Add subtasks if any
        if task["subtasks"]:
            result["subtasks"] = [
                self._build_task_result(subtask_id)
                for subtask_id in task["subtasks"]
            ]

        return result

    async def _health_check_loop(self) -> None:
        """Background task for periodic health checks."""
        while self.running:
            try:
                await asyncio.sleep(self.health_check_interval)

                # Perform health check
                health = await self.health_check()

                # Log health status
                logger.debug("Orchestrator health check",
                            status=health["status"],
                            agents_total=health["agents"]["total"],
                            tasks_pending=health["tasks"]["pending"],
                            tasks_running=health["tasks"]["running"],
                            success_rate=health["tasks"]["success_rate"])

                # Auto-scaling if enabled
                if self.auto_scaling:
                    await self._auto_scale_workers(health)

            except asyncio.CancelledError:
                logger.info("Health check loop cancelled")
                break

            except Exception as e:
                logger.error("Health check error",
                            error=str(e),
                            exc_info=True)

    async def _auto_scale_workers(self, health: Dict[str, Any]) -> None:
        """Auto-scale worker count based on load.

        Args:
            health: Health check data
        """
        pending_tasks = health["tasks"]["pending"]
        running_tasks = health["tasks"]["running"]
        current_workers = len(self.worker_tasks)

        # Calculate target worker count
        min_workers = self.config.get("min_workers", 5)
        max_workers = self.config.get("max_workers", 50)

        # Simple scaling formula based on pending and running tasks
        target_workers = min(
            max_workers,
            max(
                min_workers,
                current_workers + (pending_tasks // 10) - (idle_workers := max(0, current_workers - running_tasks) // 2)
            )
        )

        # Only scale if significant change
        if abs(target_workers - current_workers) >= 3:
            logger.info("Auto-scaling workers",
                       current=current_workers,
                       target=target_workers,
                       pending_tasks=pending_tasks,
                       running_tasks=running_tasks)

            if target_workers > current_workers:
                # Scale up
                for i in range(current_workers, target_workers):
                    worker = asyncio.create_task(self._worker_loop(i))
                    self.worker_tasks.append(worker)
            elif target_workers < current_workers:
                # Scale down (cancel excess workers)
                for i in range(current_workers - target_workers):
                    if self.worker_tasks:
                        worker = self.worker_tasks.pop()
                        worker.cancel()

            # Update worker count
            self.worker_count = target_workers
