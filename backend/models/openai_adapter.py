from .base import ModelAdapter, ModelInitializationError, ModelGenerationError
from loguru import logger

class OpenAIAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize OpenAI client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with OpenAI model: {str(e)}") 