#!/usr/bin/env python3
"""
FastAPI endpoints for Maily's AI/ML capabilities

This module exposes the ML pipeline functionality through REST API endpoints.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from .ml_pipeline import (
    build_ml_pipeline,
    Pipeline,
    ModelType,
    ABTestConfig
)

# Create router
router = APIRouter(prefix="/ai", tags=["AI/ML"])

# Global pipeline instance
_pipeline: Optional[Pipeline] = None

def get_pipeline() -> Pipeline:
    """Dependency to get the ML pipeline instance"""
    global _pipeline
    if _pipeline is None:
        _pipeline = build_ml_pipeline()
    return _pipeline


# Request/Response models
class PredictEngagementRequest(BaseModel):
    """Request model for engagement prediction"""
    email_ids: List[str]
    campaign_id: Optional[str] = None


class PredictEngagementResponse(BaseModel):
    """Response model for engagement prediction"""
    predictions: Dict[str, float]
    model_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OptimizeSubjectRequest(BaseModel):
    """Request model for subject line optimization"""
    subject_lines: List[str]
    audience_segment: str
    campaign_id: Optional[str] = None


class OptimizeSubjectResponse(BaseModel):
    """Response model for subject line optimization"""
    scores: Dict[str, float]
    best_subject: str
    model_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CreateABTestRequest(BaseModel):
    """Request model for creating an A/B test"""
    name: str
    description: Optional[str] = None
    variants: List[str]
    metrics: List[str]
    duration_days: int = 7


class ABTestResponse(BaseModel):
    """Response model for A/B test operations"""
    test_id: int
    name: str
    status: str
    start_date: datetime
    end_date: datetime


class TrainModelRequest(BaseModel):
    """Request model for training a model"""
    model_type: ModelType
    feature_set_name: str
    training_days: int = 90


class ModelInfoResponse(BaseModel):
    """Response model for model information"""
    name: str
    version: str
    metrics: Dict[str, float]
    created_at: str


# API Endpoints
@router.post("/predict-engagement", response_model=PredictEngagementResponse)
async def predict_engagement(
    request: PredictEngagementRequest,
    pipeline: Pipeline = Depends(get_pipeline)
):
    """
    Predict engagement probability for a list of emails

    Returns a score between 0 and 1 for each email, where higher means
    more likely to engage (open, click).
    """
    try:
        # Get predictions
        predictions = pipeline.predict_engagement(request.email_ids)

        # Get model info
        model_info = pipeline.model_registry.get_active_model(ModelType.ENGAGEMENT_PREDICTION)
        if not model_info:
            raise HTTPException(status_code=500, detail="No active engagement prediction model found")

        return PredictEngagementResponse(
            predictions=predictions,
            model_version=f"{model_info['name']}@{model_info['version']}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-subject", response_model=OptimizeSubjectResponse)
async def optimize_subject(
    request: OptimizeSubjectRequest,
    pipeline: Pipeline = Depends(get_pipeline)
):
    """
    Optimize subject lines for a given audience segment

    Returns a score for each subject line and identifies the best one.
    """
    try:
        # Get predictions
        scores = pipeline.optimize_subject_line(
            request.subject_lines,
            request.audience_segment
        )

        # Find best subject
        best_subject = max(scores.items(), key=lambda x: x[1])[0]

        # Get model info
        model_info = pipeline.model_registry.get_active_model(ModelType.SUBJECT_OPTIMIZATION)
        if not model_info:
            raise HTTPException(status_code=500, detail="No active subject optimization model found")

        return OptimizeSubjectResponse(
            scores=scores,
            best_subject=best_subject,
            model_version=f"{model_info['name']}@{model_info['version']}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-tests", response_model=ABTestResponse)
async def create_ab_test(
    request: CreateABTestRequest,
    pipeline: Pipeline = Depends(get_pipeline)
):
    """
    Create a new A/B test experiment

    Sets up an experiment with the specified variants and metrics.
    """
    try:
        # Create test
        test_id = pipeline.setup_ab_test(
            name=request.name,
            variants=request.variants,
            metrics=request.metrics,
            duration_days=request.duration_days
        )

        # Get test info
        session = pipeline.ab_test_framework.Session()
        test = session.query(pipeline.ab_test_framework.ABTest).filter_by(id=test_id).first()
        session.close()

        if not test:
            raise HTTPException(status_code=500, detail="Failed to create A/B test")

        return ABTestResponse(
            test_id=test.id,
            name=test.name,
            status=test.status,
            start_date=test.start_date,
            end_date=test.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-tests/{test_id}", response_model=Dict[str, Any])
async def get_ab_test_results(
    test_id: int,
    pipeline: Pipeline = Depends(get_pipeline)
):
    """
    Get the results of an A/B test

    Returns the current status, metrics, and winner (if determined).
    """
    try:
        # Get test info
        session = pipeline.ab_test_framework.Session()
        test = session.query(pipeline.ab_test_framework.ABTest).filter_by(id=test_id).first()
        session.close()

        if not test:
            raise HTTPException(status_code=404, detail=f"A/B test with ID {test_id} not found")

        # Analyze results if running
        if test.status == "running":
            results = pipeline.ab_test_framework.analyze_results(test.name)
        else:
            # Just return stored results
            results = {
                "name": test.name,
                "status": test.status,
                "results": test.results,
                "winner": test.winner
            }

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train", response_model=ModelInfoResponse)
async def train_model(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks,
    pipeline: Pipeline = Depends(get_pipeline)
):
    """
    Train a new model

    This is a long-running operation that runs in the background.
    Returns immediately with the task status.
    """
    try:
        # Calculate training date range
        end_date = datetime.utcnow() - timedelta(days=1)
        start_date = end_date - timedelta(days=request.training_days)

        if request.model_type == ModelType.ENGAGEMENT_PREDICTION:
            # Start training in background
            background_tasks.add_task(
                pipeline.train_engagement_model,
                request.feature_set_name,
                start_date,
                end_date
            )

            # Return current model info
            model_info = pipeline.model_registry.get_active_model(ModelType.ENGAGEMENT_PREDICTION)
            if not model_info:
                return ModelInfoResponse(
                    name=ModelType.ENGAGEMENT_PREDICTION,
                    version="training_first_version",
                    metrics={},
                    created_at=datetime.utcnow().isoformat()
                )

            return ModelInfoResponse(
                name=model_info["name"],
                version=model_info["version"],
                metrics=model_info["metrics"],
                created_at=model_info["created_at"]
            )
        else:
            # Other model types not implemented yet
            raise HTTPException(
                status_code=400,
                detail=f"Training for model type {request.model_type} not implemented yet"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_type}", response_model=ModelInfoResponse)
async def get_model_info(
    model_type: ModelType,
    pipeline: Pipeline = Depends(get_pipeline)
):
    """
    Get information about the currently active model of a given type
    """
    try:
        model_info = pipeline.model_registry.get_active_model(model_type)
        if not model_info:
            raise HTTPException(
                status_code=404,
                detail=f"No active model found for type {model_type}"
            )

        return ModelInfoResponse(
            name=model_info["name"],
            version=model_info["version"],
            metrics=model_info["metrics"],
            created_at=model_info["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
