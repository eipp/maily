#!/usr/bin/env python3
"""
Test configuration for adapter implementation tests.

This module provides test fixtures and configuration for testing the adapter implementation
with both fixed and router authentication methods and data formats.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'services'))

# Create a mock adapter app for testing when imports fail
from fastapi import FastAPI
mock_app = FastAPI()

# Import adapter implementation
try:
    from main_adapter import app as adapter_app
    print("Successfully imported adapter_app from main_adapter")
except ImportError as e:
    print(f"Failed to import adapter_app: {e}")
    # Create a mock adapter app
    adapter_app = mock_app

# Force test client to use mock app when needed
def get_test_client():
    return TestClient(adapter_app)

@pytest.fixture
def test_client():
    """Create a test client for the adapter app."""
    with TestClient(adapter_app) as client:
        yield client

@pytest.fixture
def fixed_auth_headers():
    """Authentication headers for the fixed implementation."""
    return {"X-API-Key": "test-api-key"}

@pytest.fixture
def router_auth_headers():
    """Authentication headers for the router implementation."""
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def fixed_campaign_data():
    """Sample campaign data in fixed format."""
    return {
        "task": "Test Fixed Campaign",
        "model_name": "gpt-4",
        "audience": {
            "segments": ["customers"],
            "exclusions": []
        }
    }

@pytest.fixture
def router_campaign_data():
    """Sample campaign data in router format."""
    return {
        "name": "Test Router Campaign",
        "subject": "Test Subject",
        "content": "Test Content",
        "segments": ["customers"],
        "exclusions": []
    }

# Test utility functions
def test_with_fixed_auth(test_client, endpoint, method="GET", data=None):
    """Test an endpoint with fixed authentication."""
    headers = {"X-API-Key": "test-api-key"}
    if method.upper() == "GET":
        return test_client.get(endpoint, headers=headers)
    elif method.upper() == "POST":
        return test_client.post(endpoint, headers=headers, json=data)
    elif method.upper() == "PUT":
        return test_client.put(endpoint, headers=headers, json=data)
    elif method.upper() == "DELETE":
        return test_client.delete(endpoint, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

def test_with_router_auth(test_client, endpoint, method="GET", data=None):
    """Test an endpoint with router authentication."""
    headers = {"Authorization": "Bearer test_token"}
    if method.upper() == "GET":
        return test_client.get(endpoint, headers=headers)
    elif method.upper() == "POST":
        return test_client.post(endpoint, headers=headers, json=data)
    elif method.upper() == "PUT":
        return test_client.put(endpoint, headers=headers, json=data)
    elif method.upper() == "DELETE":
        return test_client.delete(endpoint, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
