"""Custom exceptions for AI operations."""

class AIError(Exception):
    """Base exception for AI-related errors."""
    pass

class ModelError(AIError):
    """Errors related to model operations."""
    pass

class TokenizationError(ModelError):
    """Errors during text tokenization."""
    pass

class InferenceError(ModelError):
    """Errors during model inference."""
    pass

class MonitoringError(AIError):
    """Errors related to monitoring operations."""
    pass

class AgentError(AIError):
    """Errors related to agent operations."""
    pass

class CacheError(AIError):
    """Errors related to caching operations."""
    pass 