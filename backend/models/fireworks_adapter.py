from .base import ModelAdapter, ModelInitializationError, ModelGenerationError
from loguru import logger

class FireworksAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import fireworks.client
            self.client = fireworks.client.Client(api_key=api_key)
            logger.info("Fireworks adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize Fireworks client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "accounts/fireworks/models/llama-v2-70b-chat")
            response = self.client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response.choices[0].text
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with Fireworks model: {str(e)}") 