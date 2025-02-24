from .base import ModelAdapter, ModelInitializationError, ModelGenerationError
from loguru import logger

class HuggingFaceAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(token=api_key)
            logger.info("HuggingFace adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize HuggingFace client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "meta-llama/Llama-2-70b-chat-hf")
            response = self.client.text_generation(
                prompt,
                model=model,
                max_new_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with HuggingFace model: {str(e)}") 