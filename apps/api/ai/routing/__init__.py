"""
Model Routing Module

This module provides services for intelligently routing AI requests to appropriate
model adapters based on task characteristics, performance metrics, and routing strategies.
"""

from .model_routing_service import (
    ModelRoutingService,
    TaskComplexity,
    ModelTier,
    RoutingStrategy
)

__all__ = [
    "ModelRoutingService",
    "TaskComplexity",
    "ModelTier",
    "RoutingStrategy"
]
