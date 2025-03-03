"""Test configuration and fixtures using the fixed main module."""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the fixed main file
from main_fixed import app, Settings, AIService, CampaignService, RateLimiter, MetricsCollector

@pytest.fixture
def test_client():
    """Create a test client for the app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def test_settings():
    """Create test settings."""
    settings = Settings()
    # Configure test settings
    settings.ENVIRONMENT = "test"
    settings.API_KEY = "test-api-key"
    return settings

@pytest.fixture
def test_ai_service(test_settings):
    """Create a test AI service."""
    return AIService(test_settings)

@pytest.fixture
def test_campaign_service(test_settings):
    """Create a test campaign service."""
    return CampaignService(test_settings)

@pytest.fixture
def test_rate_limiter(test_settings):
    """Create a test rate limiter."""
    return RateLimiter(test_settings)

@pytest.fixture
def test_metrics_collector(test_settings):
    """Create a test metrics collector."""
    return MetricsCollector(test_settings)

@pytest.fixture
def test_api_key():
    """Return a test API key."""
    return "test-api-key"

@pytest.fixture
def test_db():
    """Mock database connection for testing."""
    class MockDB:
        def execute(self, query):
            return [(1,)]

        def close(self):
            pass

    return MockDB()

@pytest.fixture
def test_redis():
    """Mock Redis client for testing."""
    class MockRedis:
        def __init__(self):
            self.data = {}

        def get(self, key):
            return self.data.get(key)

        def set(self, key, value, ex=None):
            self.data[key] = value

        def delete(self, *keys):
            for key in keys:
                if key in self.data:
                    del self.data[key]

        def ping(self):
            return True

    return MockRedis()

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("APP_NAME", "Maily API Test")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("API_KEY", "test-api-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
