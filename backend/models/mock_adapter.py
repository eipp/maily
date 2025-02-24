import json
from .base import ModelAdapter, ModelGenerationError
from loguru import logger

class MockAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str, **kwargs):
        try:
            if "email content" in prompt.lower():
                return json.dumps({
                    "subject": "Exciting New Product Launch",
                    "body": "We're thrilled to announce our latest innovation..."
                })
            elif "design theme" in prompt.lower():
                return "Modern minimalist design with a blue and white color scheme"
            elif "personalization" in prompt.lower():
                return "Segment users by industry and insert company name in subject line"
            elif "delivery time" in prompt.lower():
                return "Tuesday at 10 AM in recipient's local timezone"
            elif "compliance" in prompt.lower():
                return "Email content complies with GDPR and CAN-SPAM requirements"
            else:
                return f"Generated response for: {prompt}"
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate mock response: {str(e)}") 