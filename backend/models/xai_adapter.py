from .base import ModelAdapter, ModelInitializationError, ModelGenerationError
from loguru import logger

class XAIAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import xai
            self.client = xai.Client(api_key=api_key)
            logger.info("x.ai adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize x.ai client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "grok-1")
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with x.ai model: {str(e)}") 