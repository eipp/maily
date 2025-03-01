"""
AI Model Evaluation Module

This module provides services for evaluating and comparing AI models
on various tasks and metrics.
"""

from .model_evaluator import (
    ModelEvaluator,
    EvaluationTask,
    ModelEvaluation,
    ModelComparison,
    model_evaluator
)

__all__ = [
    "ModelEvaluator",
    "EvaluationTask",
    "ModelEvaluation",
    "ModelComparison",
    "model_evaluator"
]
