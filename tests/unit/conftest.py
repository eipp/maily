"""Test configuration and fixtures."""

import os
import sys
from typing import Dict, Any

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Ensure the parent directory is in the Python path
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, api_dir)

# Import app from main
from main_fixed import app

# Simple test database URL that works with SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture
def test_client():
    """Create a test client for the app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_api_key():
    """Return a mock API key for testing."""
    return "test-api-key"

@pytest.fixture
def mock_env(monkeypatch):
    """Set mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("LANGFUSE_API_KEY", "test-langfuse-key")
    monkeypatch.setenv("DATABASE_URL", SQLALCHEMY_DATABASE_URL)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("ENVIRONMENT", "test")

# Define MockRedis class outside of fixture
class MockRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ex=None):
        self.data[key] = value

    def setex(self, key, ex, value):
        self.data[key] = value

    def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)

    def scan(self, cursor, pattern):
        matching = [k for k in self.data.keys() if k.startswith(pattern.replace('*', ''))]
        return 0, matching

    def ping(self):
        return True

@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis connection for testing."""
    monkeypatch.setattr(redis, "Redis", MockRedis)
    return MockRedis()

@pytest.fixture
def test_cache():
    """Return a mock Redis client for testing."""
    mock = MockRedis()
    return mock

@pytest.fixture
def test_db():
    """Return a SQLite in-memory connection for testing."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()

@pytest.fixture
def test_redis():
    """Return a mock Redis client for testing."""
    mock = MockRedis()
    return mock

@pytest.fixture
def test_api_key():
    """Test API key fixture."""
    return "test-api-key"
