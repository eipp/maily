"""
Model Evaluation Service

This module provides services for evaluating and comparing AI models
on various tasks and metrics.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

from pydantic import BaseModel, Field

from ..dependencies import get_model_service
from ..adapters.base import ModelRequest, ModelResponse
from ..utils.token_counter import count_tokens, estimate_cost

logger = logging.getLogger(__name__)


class EvaluationTask(BaseModel):
    """Model for an evaluation task."""
    id: str
    name: str
    description: str
    prompt: str
    expected_output: Optional[str] = None
    evaluation_criteria: List[str] = []
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class ModelEvaluation(BaseModel):
    """Model for a model evaluation."""
    model_name: str
    task_id: str
    prompt: str
    response: str
    latency_ms: float
    token_count: int
    estimated_cost: float
    scores: Dict[str, float] = {}
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelComparison(BaseModel):
    """Model for a model comparison."""
    task_id: str
    evaluations: Dict[str, ModelEvaluation]
    summary: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelEvaluator:
    """
    Service for evaluating and comparing AI models.

    This class provides methods for evaluating models on various tasks
    and comparing their performance.
    """

    def __init__(self):
        """Initialize the model evaluator."""
        self.tasks: Dict[str, EvaluationTask] = {}
        self.evaluations: Dict[str, Dict[str, ModelEvaluation]] = {}
        self.comparisons: Dict[str, ModelComparison] = {}

    def register_task(self, task: EvaluationTask) -> EvaluationTask:
        """
        Register an evaluation task.

        Args:
            task: The task to register.

        Returns:
            The registered task.

        Raises:
            ValueError: If a task with the given ID already exists.
        """
        if task.id in self.tasks:
            raise ValueError(f"Task {task.id} already exists")

        self.tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> Optional[EvaluationTask]:
        """
        Get a task by ID.

        Args:
            task_id: The ID of the task to get.

        Returns:
            The task, or None if not found.
        """
        return self.tasks.get(task_id)

    def list_tasks(self, tag: Optional[str] = None) -> List[EvaluationTask]:
        """
        List all tasks, optionally filtered by tag.

        Args:
            tag: Optional tag to filter by.

        Returns:
            A list of tasks.
        """
        if tag:
            return [t for t in self.tasks.values() if tag in t.tags]
        return list(self.tasks.values())

    async def evaluate_model(
        self,
        model_name: str,
        task_id: str,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelEvaluation:
        """
        Evaluate a model on a task.

        Args:
            model_name: The name of the model to evaluate.
            task_id: The ID of the task to evaluate on.
            temperature: The temperature to use for generation.
            max_tokens: The maximum number of tokens to generate.
            metadata: Optional metadata to include in the evaluation.

        Returns:
            The evaluation results.

        Raises:
            ValueError: If the task is not found.
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        metadata = metadata or {}

        # Track start time
        start_time = time.time()

        # Get consolidated service instance
        consolidated_ai_service = get_model_service()

        # Generate response
        response = await consolidated_ai_service.generate_text(
            prompt=task.prompt,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata={"evaluation": True, "task_id": task_id, **metadata}
        )

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # Count tokens
        token_count = response.usage.get("total_tokens", 0)
        if token_count == 0:
            # Fallback to estimating tokens
            prompt_tokens = response.usage.get("prompt_tokens", count_tokens(task.prompt, model_name))
            completion_tokens = response.usage.get("completion_tokens", count_tokens(response.content, model_name))
            token_count = prompt_tokens + completion_tokens

        # Estimate cost
        estimated_cost = estimate_cost(
            response.usage.get("prompt_tokens", token_count // 2),
            response.usage.get("completion_tokens", token_count // 2),
            model_name
        )

        # Create evaluation
        evaluation = ModelEvaluation(
            model_name=model_name,
            task_id=task_id,
            prompt=task.prompt,
            response=response.content,
            latency_ms=latency_ms,
            token_count=token_count,
            estimated_cost=estimated_cost,
            metadata={
                **metadata,
                "usage": response.usage,
                "finish_reason": response.finish_reason
            }
        )

        # Store evaluation
        if task_id not in self.evaluations:
            self.evaluations[task_id] = {}
        self.evaluations[task_id][model_name] = evaluation

        return evaluation

    async def compare_models(
        self,
        model_names: List[str],
        task_id: str,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelComparison:
        """
        Compare multiple models on a task.

        Args:
            model_names: The names of the models to compare.
            task_id: The ID of the task to evaluate on.
            temperature: The temperature to use for generation.
            max_tokens: The maximum number of tokens to generate.
            metadata: Optional metadata to include in the comparison.

        Returns:
            The comparison results.

        Raises:
            ValueError: If the task is not found.
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        metadata = metadata or {}

        # Evaluate each model
        evaluations = {}
        for model_name in model_names:
            evaluation = await self.evaluate_model(
                model_name=model_name,
                task_id=task_id,
                temperature=temperature,
                max_tokens=max_tokens,
                metadata=metadata
            )
            evaluations[model_name] = evaluation

        # Compute summary statistics
        summary = self._compute_comparison_summary(evaluations)

        # Create comparison
        comparison = ModelComparison(
            task_id=task_id,
            evaluations=evaluations,
            summary=summary
        )

        # Store comparison
        self.comparisons[f"{task_id}_{datetime.utcnow().isoformat()}"] = comparison

        return comparison

    def _compute_comparison_summary(self, evaluations: Dict[str, ModelEvaluation]) -> Dict[str, Any]:
        """
        Compute summary statistics for a comparison.

        Args:
            evaluations: The evaluations to summarize.

        Returns:
            A dictionary of summary statistics.
        """
        if not evaluations:
            return {}

        # Compute average latency, token count, and cost
        avg_latency = sum(e.latency_ms for e in evaluations.values()) / len(evaluations)
        avg_token_count = sum(e.token_count for e in evaluations.values()) / len(evaluations)
        avg_cost = sum(e.estimated_cost for e in evaluations.values()) / len(evaluations)

        # Find fastest, cheapest, and most expensive models
        fastest_model = min(evaluations.items(), key=lambda x: x[1].latency_ms)[0]
        cheapest_model = min(evaluations.items(), key=lambda x: x[1].estimated_cost)[0]
        most_expensive_model = max(evaluations.items(), key=lambda x: x[1].estimated_cost)[0]

        return {
            "model_count": len(evaluations),
            "avg_latency_ms": avg_latency,
            "avg_token_count": avg_token_count,
            "avg_cost": avg_cost,
            "fastest_model": fastest_model,
            "cheapest_model": cheapest_model,
            "most_expensive_model": most_expensive_model
        }

    async def evaluate_model_batch(
        self,
        model_name: str,
        task_ids: List[str],
        temperature: float = 0.0,
        max_tokens: int = 1000,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, ModelEvaluation]:
        """
        Evaluate a model on multiple tasks.

        Args:
            model_name: The name of the model to evaluate.
            task_ids: The IDs of the tasks to evaluate on.
            temperature: The temperature to use for generation.
            max_tokens: The maximum number of tokens to generate.
            metadata: Optional metadata to include in the evaluations.

        Returns:
            A dictionary mapping task IDs to evaluation results.

        Raises:
            ValueError: If any task is not found.
        """
        # Check that all tasks exist
        for task_id in task_ids:
            if task_id not in self.tasks:
                raise ValueError(f"Task {task_id} not found")

        # Evaluate model on each task
        evaluations = {}
        for task_id in task_ids:
            evaluation = await self.evaluate_model(
                model_name=model_name,
                task_id=task_id,
                temperature=temperature,
                max_tokens=max_tokens,
                metadata=metadata
            )
            evaluations[task_id] = evaluation

        return evaluations

    def get_evaluation(self, task_id: str, model_name: str) -> Optional[ModelEvaluation]:
        """
        Get an evaluation by task ID and model name.

        Args:
            task_id: The ID of the task.
            model_name: The name of the model.

        Returns:
            The evaluation, or None if not found.
        """
        if task_id not in self.evaluations:
            return None
        return self.evaluations[task_id].get(model_name)

    def list_evaluations(self, task_id: Optional[str] = None, model_name: Optional[str] = None) -> List[ModelEvaluation]:
        """
        List evaluations, optionally filtered by task ID and/or model name.

        Args:
            task_id: Optional task ID to filter by.
            model_name: Optional model name to filter by.

        Returns:
            A list of evaluations.
        """
        results = []

        if task_id:
            # Filter by task ID
            if task_id not in self.evaluations:
                return []

            if model_name:
                # Filter by task ID and model name
                evaluation = self.evaluations[task_id].get(model_name)
                return [evaluation] if evaluation else []
            else:
                # Filter by task ID only
                return list(self.evaluations[task_id].values())
        elif model_name:
            # Filter by model name only
            for task_evals in self.evaluations.values():
                if model_name in task_evals:
                    results.append(task_evals[model_name])
            return results
        else:
            # No filters, return all evaluations
            for task_evals in self.evaluations.values():
                results.extend(task_evals.values())
            return results


# Create a singleton instance
model_evaluator = ModelEvaluator()
