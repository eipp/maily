class ModelError(Exception):
    """Base class for model-related errors."""
    pass

class ModelInitializationError(ModelError):
    """Error raised when model initialization fails."""
    pass

class ModelGenerationError(ModelError):
    """Error raised when model generation fails."""
    pass

class ModelAdapter:
    """Base class for model adapters."""
    def generate(self, prompt: str, **kwargs):
        """Generate a response from the model."""
        raise NotImplementedError 