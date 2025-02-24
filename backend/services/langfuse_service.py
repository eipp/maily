import time
from loguru import logger
from ..models import MODEL_REGISTRY
from .database import get_db_connection
from cryptography.fernet import Fernet

# Initialize encryption
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

class LangfuseLLM:
    def __init__(self, langfuse_client, user_id):
        self.langfuse = langfuse_client
        self.user_id = user_id
        self._config_list = None

    @property
    def config_list(self):
        if self._config_list is None:
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT model_name, api_key FROM user_configs WHERE user_id = %s", (self.user_id,))
                result = cur.fetchone()
                cur.close()
                conn.close()

                if result:
                    model_name, encrypted_key = result
                    api_key = cipher_suite.decrypt(encrypted_key.encode()).decode()
                    if model_name == "r1-1776":
                        self._config_list = [{
                            "model": model_name,
                            "api_key": api_key,
                            "base_url": "https://api.perplexity.ai",
                            "api_type": "perplexity"
                        }]
                    elif model_name == "openai":
                        self._config_list = [{
                            "model": "gpt-3.5-turbo",
                            "api_key": api_key,
                            "api_type": "openai"
                        }]
                    else:
                        self._config_list = [{
                            "model": model_name,
                            "api_key": api_key
                        }]
                else:
                    model_name = "mock"
                    api_key = "test-api-key"
                    self._config_list = [{
                        "model": model_name,
                        "api_key": api_key
                    }]
            except Exception as e:
                logger.error(f"Failed to get config list: {e}")
                self._config_list = [{"model": "mock", "api_key": "test-api-key"}]
        return self._config_list

    def create(self, **kwargs):
        span = None
        if self.langfuse:
            span = self.langfuse.span(name="llm_generate", input=kwargs)
        for attempt in range(3):
            try:
                config = self.config_list[0]
                adapter = MODEL_REGISTRY[config["model"]](config["api_key"])
                messages = kwargs.get("messages", [])
                prompt = messages[-1]["content"] if messages else kwargs.get("prompt", "")
                start_time = time.time()
                response = adapter.generate(prompt)
                if span:
                    span.end(output={"response": response})
                return {
                    "choices": [{
                        "message": {
                            "content": response,
                            "role": "assistant"
                        }
                    }]
                }
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < 2:
                    time.sleep(1)
                else:
                    if span:
                        span.end(error=str(e))
                    raise 