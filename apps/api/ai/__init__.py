"""
Maily AI Service

This module provides a unified AI service for the Maily platform, including:
- Text generation with multiple model providers
- Email campaign creation and management
- Contact discovery and audience segmentation
- Monitoring and observability
"""

from .consolidated_service import ConsolidatedAIService as AIService
from .adapters.base import (
    EnhancedModelAdapter,
    EnhancedModelRequest,
    EnhancedModelResponse,
    ModelProvider,
    ModelCapability,
    ValidationResult
)
from .adapters.base import (
    BaseModelAdapter,
    ModelRequest,
    ModelResponse
)
from .utils.token_counter import count_tokens, estimate_cost

__all__ = [
    # Core service
    'AIService',

    # Model adapters
    'BaseModelAdapter',
    'ModelRequest',
    'ModelResponse',
    'EnhancedModelAdapter',
    'EnhancedModelRequest',
    'EnhancedModelResponse',
    'ModelProvider',
    'ModelCapability',
    'ValidationResult',

    # Utilities
    'count_tokens',
    'estimate_cost',
]
