from .base import ModelAdapter, ModelInitializationError, ModelGenerationError
from loguru import logger

class TogetherAIAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import together
            together.api_key = api_key
            self.together = together
            logger.info("Together AI adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize Together AI client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "togethercomputer/llama-2-70b-chat")
            response = self.together.Complete.create(
                prompt=prompt,
                model=model,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response['output']['choices'][0]['text']
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with Together AI model: {str(e)}") 