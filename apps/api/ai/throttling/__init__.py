"""
AI Throttling Module

This module provides throttling mechanisms for AI operations to prevent
overloading AI services and manage costs effectively.
"""

from .throttling_service import ThrottlingService, throttling_service

__all__ = ["ThrottlingService", "throttling_service"]
