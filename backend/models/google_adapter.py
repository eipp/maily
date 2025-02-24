from .base import ModelAdapter, ModelInitializationError, ModelGenerationError
from loguru import logger

class GoogleAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.genai = genai
            logger.info("Google adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize Google client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "gemini-pro")
            model = self.genai.GenerativeModel(model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with Google model: {str(e)}") 