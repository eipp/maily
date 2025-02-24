from .base import ModelAdapter, ModelInitializationError, ModelGenerationError
from loguru import logger

class ReplicateAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import replicate
            self.client = replicate.Client(api_token=api_key)
            logger.info("Replicate adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize Replicate client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            # You can specify different models via kwargs
            model = kwargs.get("model", "meta/llama-2-70b-chat")
            output = self.client.run(
                model,
                input={
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_length": kwargs.get("max_tokens", 2048)
                }
            )
            return "".join(output)  # Replicate returns a generator
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with Replicate model: {str(e)}") 