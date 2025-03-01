"""
Model Fallback Module

This module provides services for handling model failures gracefully,
automatically falling back to alternative models when primary models fail.
"""

from .fallback_service import ModelFallbackService, FallbackChain, fallback_service

__all__ = ["ModelFallbackService", "FallbackChain", "fallback_service"]
