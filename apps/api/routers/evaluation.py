"""
Model Evaluation Router

This module provides endpoints for evaluating and comparing AI models
on various tasks and metrics.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field

from ..services.user_service import get_current_user
from ..models.user import User
from ..ai.evaluation import (
    model_evaluator,
    EvaluationTask,
    ModelEvaluation,
    ModelComparison
)

router = APIRouter(prefix="/evaluation", tags=["Model Evaluation"])


# Request/Response Models
class EvaluationTaskCreate(BaseModel):
    """Request model for creating an evaluation task."""
    id: str
    name: str
    description: str
    prompt: str
    expected_output: Optional[str] = None
    evaluation_criteria: List[str] = []
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class EvaluationTaskResponse(BaseModel):
    """Response model for an evaluation task."""
    id: str
    name: str
    description: str
    prompt: str
    expected_output: Optional[str] = None
    evaluation_criteria: List[str]
    tags: List[str]
    metadata: Dict[str, Any]


class ModelEvaluationRequest(BaseModel):
    """Request model for evaluating a model."""
    model_name: str
    task_id: str
    temperature: float = 0.0
    max_tokens: int = 1000
    metadata: Dict[str, Any] = {}


class ModelEvaluationResponse(BaseModel):
    """Response model for a model evaluation."""
    model_name: str
    task_id: str
    prompt: str
    response: str
    latency_ms: float
    token_count: int
    estimated_cost: float
    scores: Dict[str, float]
    metadata: Dict[str, Any]
    created_at: str


class ModelComparisonRequest(BaseModel):
    """Request model for comparing models."""
    model_names: List[str]
    task_id: str
    temperature: float = 0.0
    max_tokens: int = 1000
    metadata: Dict[str, Any] = {}


class ModelComparisonResponse(BaseModel):
    """Response model for a model comparison."""
    task_id: str
    evaluations: Dict[str, ModelEvaluationResponse]
    summary: Dict[str, Any]
    created_at: str


# Endpoints
@router.post("/tasks", response_model=EvaluationTaskResponse)
async def create_evaluation_task(
    task: EvaluationTaskCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new evaluation task.

    Args:
        task: The task to create.
        current_user: The current authenticated user.

    Returns:
        The created task.

    Raises:
        HTTPException: If a task with the given ID already exists.
    """
    try:
        created = model_evaluator.register_task(
            EvaluationTask(
                id=task.id,
                name=task.name,
                description=task.description,
                prompt=task.prompt,
                expected_output=task.expected_output,
                evaluation_criteria=task.evaluation_criteria,
                tags=task.tags,
                metadata=task.metadata
            )
        )

        return EvaluationTaskResponse(
            id=created.id,
            name=created.name,
            description=created.description,
            prompt=created.prompt,
            expected_output=created.expected_output,
            evaluation_criteria=created.evaluation_criteria,
            tags=created.tags,
            metadata=created.metadata
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks", response_model=List[EvaluationTaskResponse])
async def list_evaluation_tasks(
    tag: Optional[str] = Query(None, description="Filter tasks by tag")
):
    """
    List all evaluation tasks, optionally filtered by tag.

    Args:
        tag: Optional tag to filter by.

    Returns:
        A list of evaluation tasks.
    """
    tasks = model_evaluator.list_tasks(tag)
    return [
        EvaluationTaskResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            prompt=t.prompt,
            expected_output=t.expected_output,
            evaluation_criteria=t.evaluation_criteria,
            tags=t.tags,
            metadata=t.metadata
        )
        for t in tasks
    ]


@router.get("/tasks/{task_id}", response_model=EvaluationTaskResponse)
async def get_evaluation_task(
    task_id: str = Path(..., description="The ID of the task to get")
):
    """
    Get an evaluation task by ID.

    Args:
        task_id: The ID of the task to get.

    Returns:
        The evaluation task.

    Raises:
        HTTPException: If the task is not found.
    """
    task = model_evaluator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return EvaluationTaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        prompt=task.prompt,
        expected_output=task.expected_output,
        evaluation_criteria=task.evaluation_criteria,
        tags=task.tags,
        metadata=task.metadata
    )


@router.post("/evaluate", response_model=ModelEvaluationResponse)
async def evaluate_model(
    request: ModelEvaluationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Evaluate a model on a task.

    Args:
        request: The evaluation request.
        current_user: The current authenticated user.

    Returns:
        The evaluation results.

    Raises:
        HTTPException: If the task is not found.
    """
    try:
        evaluation = await model_evaluator.evaluate_model(
            model_name=request.model_name,
            task_id=request.task_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata=request.metadata
        )

        return ModelEvaluationResponse(
            model_name=evaluation.model_name,
            task_id=evaluation.task_id,
            prompt=evaluation.prompt,
            response=evaluation.response,
            latency_ms=evaluation.latency_ms,
            token_count=evaluation.token_count,
            estimated_cost=evaluation.estimated_cost,
            scores=evaluation.scores,
            metadata=evaluation.metadata,
            created_at=evaluation.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=ModelComparisonResponse)
async def compare_models(
    request: ModelComparisonRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Compare multiple models on a task.

    Args:
        request: The comparison request.
        current_user: The current authenticated user.

    Returns:
        The comparison results.

    Raises:
        HTTPException: If the task is not found.
    """
    try:
        comparison = await model_evaluator.compare_models(
            model_names=request.model_names,
            task_id=request.task_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata=request.metadata
        )

        # Convert evaluations to response format
        evaluations_response = {}
        for model_name, evaluation in comparison.evaluations.items():
            evaluations_response[model_name] = ModelEvaluationResponse(
                model_name=evaluation.model_name,
                task_id=evaluation.task_id,
                prompt=evaluation.prompt,
                response=evaluation.response,
                latency_ms=evaluation.latency_ms,
                token_count=evaluation.token_count,
                estimated_cost=evaluation.estimated_cost,
                scores=evaluation.scores,
                metadata=evaluation.metadata,
                created_at=evaluation.created_at.isoformat()
            )

        return ModelComparisonResponse(
            task_id=comparison.task_id,
            evaluations=evaluations_response,
            summary=comparison.summary,
            created_at=comparison.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluations", response_model=List[ModelEvaluationResponse])
async def list_evaluations(
    task_id: Optional[str] = Query(None, description="Filter evaluations by task ID"),
    model_name: Optional[str] = Query(None, description="Filter evaluations by model name")
):
    """
    List evaluations, optionally filtered by task ID and/or model name.

    Args:
        task_id: Optional task ID to filter by.
        model_name: Optional model name to filter by.

    Returns:
        A list of evaluations.
    """
    evaluations = model_evaluator.list_evaluations(task_id, model_name)
    return [
        ModelEvaluationResponse(
            model_name=e.model_name,
            task_id=e.task_id,
            prompt=e.prompt,
            response=e.response,
            latency_ms=e.latency_ms,
            token_count=e.token_count,
            estimated_cost=e.estimated_cost,
            scores=e.scores,
            metadata=e.metadata,
            created_at=e.created_at.isoformat()
        )
        for e in evaluations
    ]


@router.get("/evaluations/{task_id}/{model_name}", response_model=ModelEvaluationResponse)
async def get_evaluation(
    task_id: str = Path(..., description="The ID of the task"),
    model_name: str = Path(..., description="The name of the model")
):
    """
    Get an evaluation by task ID and model name.

    Args:
        task_id: The ID of the task.
        model_name: The name of the model.

    Returns:
        The evaluation.

    Raises:
        HTTPException: If the evaluation is not found.
    """
    evaluation = model_evaluator.get_evaluation(task_id, model_name)
    if not evaluation:
        raise HTTPException(status_code=404, detail=f"Evaluation for task {task_id} and model {model_name} not found")

    return ModelEvaluationResponse(
        model_name=evaluation.model_name,
        task_id=evaluation.task_id,
        prompt=evaluation.prompt,
        response=evaluation.response,
        latency_ms=evaluation.latency_ms,
        token_count=evaluation.token_count,
        estimated_cost=evaluation.estimated_cost,
        scores=evaluation.scores,
        metadata=evaluation.metadata,
        created_at=evaluation.created_at.isoformat()
    )
