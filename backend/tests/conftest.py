"""Test configuration and fixtures."""

import os
import pytest
from typing import Dict, Any
import redis
from fastapi.testclient import TestClient

from backend.ai.adapters import (
    ModelFactory,
    R11776Adapter,
    OpenAIAdapter,
    GeminiAdapter,
    ClaudeAdapter
)
from backend.ai.monitoring import AIMonitoring
from backend.ai.cache import AICache
from ..main import app
from ..models import MockAdapter
from ..cache.redis import redis_client
from ..services.database import get_db_connection

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("LANGFUSE_API_KEY", "test-langfuse-key")
    
@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis connection for testing."""
    class MockRedis:
        def __init__(self):
            self.data = {}
            
        def get(self, key):
            return self.data.get(key)
            
        def set(self, key, value, ex=None):
            self.data[key] = value
            
        def delete(self, *keys):
            for key in keys:
                self.data.pop(key, None)
                
        def scan(self, cursor, pattern):
            matching = [k for k in self.data.keys() if k.startswith(pattern)]
            return 0, matching
            
        def ping(self):
            return True
            
    monkeypatch.setattr(redis, "Redis", MockRedis)
    
@pytest.fixture
def test_prompts() -> Dict[str, Any]:
    """Test prompts and expected patterns."""
    return {
        "email_subject": {
            "prompt": """Generate a compelling email subject line for:
            Purpose: Product launch
            Target Audience: Enterprise customers
            Key Message: New AI features
            Tone: Professional""",
            "patterns": [
                r"AI|Artificial Intelligence",
                r"Launch|Introducing|Announcing",
                r"Enterprise|Business"
            ]
        },
        "email_body": {
            "prompt": """Generate an email body with the following requirements:
            Subject: Introducing AI-Powered Email Generation
            Purpose: Product launch
            Target Audience: Enterprise customers
            Key Message: New AI features
            Tone: Professional
            Call to Action: Schedule demo""",
            "patterns": [
                r"Dear|Hello|Hi",
                r"AI|Artificial Intelligence",
                r"demo|demonstration",
                r"schedule|book|contact",
                r"Best|Regards|Sincerely"
            ]
        }
    }
    
@pytest.fixture
def mock_model_responses(monkeypatch):
    """Mock model responses for testing."""
    def mock_generate(*args, **kwargs):
        return "Test response from mock model"
        
    for adapter in [R11776Adapter, OpenAIAdapter, GeminiAdapter, ClaudeAdapter]:
        monkeypatch.setattr(
            adapter,
            "generate",
            mock_generate
        )
        
@pytest.fixture
def mock_monitoring(monkeypatch):
    """Mock Langfuse monitoring for testing."""
    class MockMonitoring:
        def log_generation(self, *args, **kwargs):
            pass
            
        def register_model(self, *args, **kwargs):
            pass
            
    monkeypatch.setattr(AIMonitoring, "__init__", lambda x: None)
    monkeypatch.setattr(AIMonitoring, "log_generation", lambda *args, **kwargs: None)
    
@pytest.fixture
def test_cache():
    """Create a test cache instance."""
    return AICache(
        host="localhost",
        port=6379,
        db=15  # Use a separate DB for testing
    )

@pytest.fixture
def test_client():
    """Test client fixture."""
    return TestClient(app)

@pytest.fixture
def mock_model():
    """Mock model adapter fixture."""
    return MockAdapter("test-api-key")

@pytest.fixture
def test_db():
    """Test database fixture."""
    conn = get_db_connection()
    yield conn
    conn.close()

@pytest.fixture
def test_redis():
    """Test Redis fixture."""
    if not redis_client:
        pytest.skip("Redis not available")
    return redis_client

@pytest.fixture
def test_api_key():
    """Test API key fixture."""
    return "mock-api-key"
