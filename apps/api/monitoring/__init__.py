"""Monitoring package for Maily.

This package provides monitoring and observability tools for tracking system
performance, AI model behavior, and user interactions within the Maily platform.
"""

from .metrics import (
    CACHE_HITS,
    CACHE_MISSES,
    MODEL_LATENCY,
    REQUEST_COUNT,
    REQUEST_LATENCY,
)

__all__ = [
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "MODEL_LATENCY",
    "CACHE_HITS",
    "CACHE_MISSES",
]
