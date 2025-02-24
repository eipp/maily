from .base import ModelAdapter, ModelInitializationError, ModelGenerationError
from loguru import logger

class AnthropicAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("Anthropic adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize Anthropic client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "claude-3-opus-20240229")
            response = self.client.messages.create(
                model=model,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with Anthropic model: {str(e)}") 