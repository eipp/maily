"""AI Agent orchestration service for multi-agent systems."""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Awaitable
from enum import Enum
import uuid
import time
import json
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AgentType(str, Enum):
    """Types of agents in the system."""
    CONTENT_GENERATION = "content_generation"
    FALLBACK_REFINEMENT = "fallback_refinement"
    ANALYTICS = "analytics"
    DISPATCHER = "dispatcher"
    CANVAS = "canvas"
    TRUST = "trust"


class AgentTaskStatus(str, Enum):
    """Status of an agent task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentTask(BaseModel):
    """Model for an agent task."""
    id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex}")
    agent_type: AgentType
    priority: int = 0
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: AgentTaskStatus = AgentTaskStatus.PENDING
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    parent_task_id: Optional[str] = None
    subtasks: List[str] = Field(default_factory=list)
    validation_results: Dict[str, Any] = Field(default_factory=dict)


class AgentInterface(BaseModel):
    """Interface for registering an agent."""
    agent_type: AgentType
    name: str
    description: str
    capabilities: List[str]
    task_handler: Optional[Callable[[AgentTask], Awaitable[Dict[str, Any]]]] = None


class OctoOrchestrator:
    """Central orchestrator for the OctoTools framework."""

    def __init__(self):
        """Initialize the orchestrator."""
        self.agents: Dict[AgentType, List[AgentInterface]] = {agent_type: [] for agent_type in AgentType}
        self.tasks: Dict[str, AgentTask] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}

    def register_agent(self, agent: AgentInterface) -> bool:
        """Register an agent with the orchestrator.

        Args:
            agent: Agent interface to register

        Returns:
            True if registered successfully, False otherwise
        """
        if not agent.task_handler:
            logger.error(f"Cannot register agent {agent.name} without task handler")
            return False

        self.agents[agent.agent_type].append(agent)
        logger.info(f"Registered agent {agent.name} of type {agent.agent_type}")
        return True

    async def dispatch_task(
        self,
        agent_type: AgentType,
        input_data: Dict[str, Any],
        priority: int = 0,
        parent_task_id: Optional[str] = None
    ) -> Optional[str]:
        """Dispatch a task to an agent of the specified type.

        Args:
            agent_type: Type of agent to dispatch to
            input_data: Input data for the task
            priority: Priority of the task (higher is more important)
            parent_task_id: ID of parent task if this is a subtask

        Returns:
            Task ID if dispatched successfully, None otherwise
        """
        # Create task
        task = AgentTask(
            agent_type=agent_type,
            priority=priority,
            input_data=input_data,
            parent_task_id=parent_task_id
        )

        # Store task
        self.tasks[task.id] = task

        # If this is a subtask, update parent
        if parent_task_id and parent_task_id in self.tasks:
            self.tasks[parent_task_id].subtasks.append(task.id)

        # Find available agent
        available_agents = self.agents[agent_type]
        if not available_agents:
            logger.error(f"No agents of type {agent_type} available")
            task.status = AgentTaskStatus.FAILED
            task.error = f"No agents of type {agent_type} available"
            return None

        # For now, just use the first agent (could implement more sophisticated routing)
        agent = available_agents[0]

        # Start task execution
        asyncio_task = asyncio.create_task(self._execute_task(task, agent))
        self.active_tasks[task.id] = asyncio_task

        logger.info(f"Dispatched task {task.id} to agent {agent.name}")
        return task.id

    async def _execute_task(self, task: AgentTask, agent: AgentInterface) -> None:
        """Execute a task using the specified agent.

        Args:
            task: Task to execute
            agent: Agent to use for execution
        """
        try:
            # Update task status
            task.status = AgentTaskStatus.RUNNING
            task.started_at = time.time()

            # Call agent handler
            task_handler = agent.task_handler
            if not task_handler:
                raise ValueError(f"Agent {agent.name} has no task handler")

            # Execute task
            result = await task_handler(task)

            # Update task
            task.output_data = result
            task.status = AgentTaskStatus.COMPLETED
            task.completed_at = time.time()

            # Process chain of thought validation if provided
            if "chain_of_thought" in result:
                validation_results = await self._validate_chain_of_thought(result["chain_of_thought"])
                task.validation_results = validation_results

            # Complete parent task if all subtasks are complete
            if task.parent_task_id and task.parent_task_id in self.tasks:
                parent_task = self.tasks[task.parent_task_id]
                if self._are_all_subtasks_complete(parent_task):
                    await self._finalize_parent_task(parent_task)

            logger.info(f"Task {task.id} completed successfully")

        except Exception as e:
            # Handle errors
            logger.exception(f"Error executing task {task.id}: {str(e)}")
            task.status = AgentTaskStatus.FAILED
            task.error = str(e)
            task.completed_at = time.time()

            # If task failed, try fallback agent if appropriate
            if task.agent_type != AgentType.FALLBACK_REFINEMENT:
                await self._try_fallback(task)

    async def _try_fallback(self, failed_task: AgentTask) -> Optional[str]:
        """Try to execute a fallback refinement for a failed task.

        Args:
            failed_task: Task that failed

        Returns:
            ID of fallback task if created, None otherwise
        """
        # Don't create fallback loops
        if failed_task.parent_task_id and self.tasks[failed_task.parent_task_id].agent_type == AgentType.FALLBACK_REFINEMENT:
            logger.warning(f"Not creating fallback for task {failed_task.id} to avoid loops")
            return None

        # Create fallback input with original task data and error
        fallback_input = {
            "original_task": failed_task.dict(),
            "error": failed_task.error,
            "original_input": failed_task.input_data
        }

        # Dispatch fallback task
        logger.info(f"Creating fallback for failed task {failed_task.id}")
        return await self.dispatch_task(
            agent_type=AgentType.FALLBACK_REFINEMENT,
            input_data=fallback_input,
            priority=failed_task.priority + 1,  # Higher priority for fallbacks
            parent_task_id=None  # This is a new top-level task
        )

    async def _validate_chain_of_thought(self, chain_of_thought: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a chain of thought reasoning process.

        Args:
            chain_of_thought: List of reasoning steps

        Returns:
            Validation results
        """
        # Basic validation for now
        validation_results = {
            "valid": True,
            "checks": []
        }

        # Check each step has required fields
        for i, step in enumerate(chain_of_thought):
            check = {"step": i, "valid": True, "issues": []}

            if "reasoning" not in step:
                check["valid"] = False
                check["issues"].append("Missing reasoning")

            if "conclusion" not in step:
                check["valid"] = False
                check["issues"].append("Missing conclusion")

            validation_results["checks"].append(check)

            # If any step is invalid, the whole chain is invalid
            if not check["valid"]:
                validation_results["valid"] = False

        return validation_results

    def _are_all_subtasks_complete(self, task: AgentTask) -> bool:
        """Check if all subtasks of a task are complete.

        Args:
            task: Task to check

        Returns:
            True if all subtasks are complete, False otherwise
        """
        for subtask_id in task.subtasks:
            if subtask_id not in self.tasks:
                logger.error(f"Subtask {subtask_id} not found for task {task.id}")
                return False

            subtask = self.tasks[subtask_id]
            if subtask.status not in [AgentTaskStatus.COMPLETED, AgentTaskStatus.FAILED]:
                return False

        return True

    async def _finalize_parent_task(self, parent_task: AgentTask) -> None:
        """Finalize a parent task by aggregating subtask results.

        Args:
            parent_task: Parent task to finalize
        """
        # Collect outputs from all subtasks
        subtask_outputs = []
        all_successful = True

        for subtask_id in parent_task.subtasks:
            subtask = self.tasks[subtask_id]

            if subtask.status == AgentTaskStatus.FAILED:
                all_successful = False

            if subtask.output_data:
                subtask_outputs.append({
                    "task_id": subtask.id,
                    "agent_type": subtask.agent_type,
                    "output": subtask.output_data
                })

        # Update parent task
        if all_successful:
            parent_task.status = AgentTaskStatus.COMPLETED
        else:
            parent_task.status = AgentTaskStatus.FAILED
            parent_task.error = "One or more subtasks failed"

        parent_task.completed_at = time.time()
        parent_task.output_data = {
            "subtask_outputs": subtask_outputs,
            "all_successful": all_successful
        }

        logger.info(f"Finalized parent task {parent_task.id} with {len(subtask_outputs)} subtasks")

    async def get_task(self, task_id: str) -> Optional[AgentTask]:
        """Get a task by ID.

        Args:
            task_id: ID of task to get

        Returns:
            Task if found, None otherwise
        """
        return self.tasks.get(task_id)

    async def get_task_status(self, task_id: str) -> Optional[AgentTaskStatus]:
        """Get status of a task.

        Args:
            task_id: ID of task to get status for

        Returns:
            Task status if found, None otherwise
        """
        task = await self.get_task(task_id)
        return task.status if task else None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.

        Args:
            task_id: ID of task to cancel

        Returns:
            True if canceled successfully, False otherwise
        """
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found for cancellation")
            return False

        task = self.tasks[task_id]

        # Cancel if still running
        if task.status == AgentTaskStatus.RUNNING and task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]

        # Update task status
        task.status = AgentTaskStatus.FAILED
        task.error = "Task was canceled"
        task.completed_at = time.time()

        # Cancel all subtasks
        for subtask_id in task.subtasks:
            await self.cancel_task(subtask_id)

        logger.info(f"Canceled task {task_id}")
        return True
