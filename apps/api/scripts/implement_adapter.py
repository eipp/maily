#!/usr/bin/env python3
"""
Implementation script for API adapter integration.

This script demonstrates how to use the adapter service to bridge
between the fixed and router implementations. It serves as a practical
starting point for the first phase of the implementation plan.
"""

import sys
import os
import asyncio
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Setup Python path to the root of the project
script_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(script_dir)
root_dir = os.path.dirname(api_dir)
sys.path.insert(0, root_dir)
sys.path.append(api_dir)

# Import the adapter service directly from the file path
# This bypasses the problematic __init__.py file
sys.path.insert(0, os.path.join(api_dir, 'services'))
api_adapter_service_path = os.path.join(api_dir, 'services', 'api_adapter_service.py')
sys.path.insert(0, os.path.dirname(api_adapter_service_path))
from api_adapter_service import (
    AuthAdapter,
    ModelAdapter,
    ResponseAdapter,
    EndpointAdapter,
    setup_api_adapter
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Create a simplified version of both apps for demonstration
def create_fixed_app():
    """Create a simplified version of the fixed app."""
    from main_fixed import app as fixed_app
    return fixed_app


def create_router_app():
    """Create a simplified version of the router app."""
    from main import app as router_app
    return router_app


# Create a new app that will use the adapter
app = FastAPI(title="Campaign API Adapter Integration")


async def test_authentication_bridge():
    """Test the authentication bridge between implementations."""
    logger.info("Testing authentication bridge...")

    # Create auth adapter
    auth_adapter = AuthAdapter()

    # Sample API key and Bearer token
    api_key = "test-api-key"
    bearer_token = "test_token"

    # Convert API key to token
    token = auth_adapter.api_key_to_token(api_key)
    logger.info(f"Converted API key to token: {token}")

    # Convert token to API key
    api_key_result = auth_adapter.token_to_api_key(bearer_token)
    logger.info(f"Converted token to API key: {api_key_result}")

    # Create mock request with API key
    api_key_request = Request(
        scope={
            "type": "http",
            "headers": [(b"x-api-key", api_key.encode())]
        }
    )

    # Create mock request with Bearer token
    bearer_request = Request(
        scope={
            "type": "http",
            "headers": [(b"authorization", f"Bearer {bearer_token}".encode())]
        }
    )

    # Verify authentication for both request types
    api_key_user = await auth_adapter.verify_authentication(api_key_request)
    bearer_user = await auth_adapter.verify_authentication(bearer_request)

    logger.info(f"API key auth result: {api_key_user}")
    logger.info(f"Bearer auth result: {bearer_user}")

    return api_key_user is not None and bearer_user is not None


async def test_model_conversion():
    """Test model conversion between implementations."""
    logger.info("Testing model conversion...")

    # Create model adapter
    model_adapter = ModelAdapter()

    # Sample fixed format campaign data
    fixed_data = {
        "campaign_id": "campaign-123",
        "task": "Test Campaign",
        "status": "draft",
        "preview_url": "http://localhost:3000/preview/campaign-123",
        "estimated_audience": 1000
    }

    # Sample router format campaign data
    router_data = {
        "id": "campaign-456",
        "name": "Router Campaign",
        "subject": "Test Subject",
        "content": "Test Content",
        "status": "DRAFT",
        "user_id": 1,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }

    # Convert fixed to standard
    standard_from_fixed = model_adapter.fixed_to_standard(fixed_data)
    logger.info(f"Converted fixed to standard: {standard_from_fixed}")

    # Convert router to standard
    standard_from_router = model_adapter.router_to_standard(router_data)
    logger.info(f"Converted router to standard: {standard_from_router}")

    # Convert standard to fixed
    fixed_from_standard = model_adapter.standard_to_fixed(standard_from_router)
    logger.info(f"Converted standard to fixed: {fixed_from_standard}")

    # Convert standard to router
    router_from_standard = model_adapter.standard_to_router(standard_from_fixed)
    logger.info(f"Converted standard to router: {router_from_standard}")

    # Convert request formats
    fixed_request = {
        "task": "Create campaign",
        "model_name": "gpt-4",
        "audience": {
            "segments": ["customers"],
            "exclusions": []
        }
    }

    router_request = {
        "name": "New Campaign",
        "subject": "Welcome",
        "content": "Hello",
        "segments": ["customers"],
        "exclusions": []
    }

    # Convert fixed request to router
    router_from_fixed_request = model_adapter.fixed_request_to_router(fixed_request)
    logger.info(f"Converted fixed request to router: {router_from_fixed_request}")

    # Convert router request to fixed
    fixed_from_router_request = model_adapter.router_request_to_fixed(router_request)
    logger.info(f"Converted router request to fixed: {fixed_from_router_request}")

    return True


def implement_adapter_routes():
    """Implement adapter routes on the new app."""
    logger.info("Implementing adapter routes...")

    # Create a new instance of the adapter
    adapter = setup_api_adapter(app)

    # Implement a new endpoint that demonstrates the adapter
    @app.post("/api/v1/campaigns")
    async def create_campaign_unified(request: Request):
        """Unified endpoint that works with both authentication methods and data formats."""
        # Get authorization
        auth_adapter = AuthAdapter()
        user = await auth_adapter.verify_authentication(request)
        if not user:
            return ResponseAdapter.standardize_error("Invalid authentication", 401)

        # Get request body
        try:
            body = await request.json()
        except ValueError:
            return ResponseAdapter.standardize_error("Invalid request body", 400)

        # Detect request format (simplified)
        is_fixed_format = "task" in body

        # Process based on format
        model_adapter = ModelAdapter()

        if is_fixed_format:
            # Convert to router format for internal standardization
            router_format = model_adapter.fixed_request_to_router(body)

            # Process with router logic
            # In a real implementation, you would call the router endpoint
            campaign_id = "campaign-" + str(hash(str(router_format)))[:8]

            # Create standardized response
            standard_response = model_adapter.router_to_standard({
                "id": campaign_id,
                "name": router_format.get("name"),
                "status": "DRAFT",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            })

            # Convert back to fixed format
            response_data = model_adapter.standard_to_fixed(standard_response)
        else:
            # Process with router logic directly
            campaign_id = "campaign-" + str(hash(str(body)))[:8]

            # Create standardized response
            standard_response = model_adapter.router_to_standard({
                "id": campaign_id,
                "name": body.get("name"),
                "subject": body.get("subject"),
                "content": body.get("content"),
                "status": "DRAFT",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            })

            # Use router format for response
            response_data = model_adapter.standard_to_router(standard_response)

        # Return standardized response
        return ResponseAdapter.standardize_response(response_data)

    return app


async def test_adapter_integration():
    """Test the complete adapter integration."""
    logger.info("Testing adapter integration...")

    # Implement the adapter routes
    app_with_adapter = implement_adapter_routes()

    # Create test client
    client = TestClient(app_with_adapter)

    # Test with fixed format and API key
    fixed_response = client.post(
        "/api/v1/campaigns",
        headers={"X-API-Key": "test-api-key"},
        json={
            "task": "Test Fixed Campaign",
            "model_name": "gpt-4",
            "audience": {
                "segments": ["customers"],
                "exclusions": []
            }
        }
    )

    logger.info(f"Fixed format response: {fixed_response.status_code}")
    logger.info(fixed_response.json())

    # Test with router format and Bearer token
    router_response = client.post(
        "/api/v1/campaigns",
        headers={"Authorization": "Bearer test_token"},
        json={
            "name": "Test Router Campaign",
            "subject": "Test Subject",
            "content": "Test Content"
        }
    )

    logger.info(f"Router format response: {router_response.status_code}")
    logger.info(router_response.json())

    return fixed_response.status_code == 200 and router_response.status_code == 200


async def run_implementation_tests():
    """Run all implementation tests."""
    auth_test = await test_authentication_bridge()
    logger.info(f"Authentication bridge test: {'PASSED' if auth_test else 'FAILED'}")

    model_test = await test_model_conversion()
    logger.info(f"Model conversion test: {'PASSED' if model_test else 'FAILED'}")

    adapter_test = await test_adapter_integration()
    logger.info(f"Adapter integration test: {'PASSED' if adapter_test else 'FAILED'}")

    return auth_test and model_test and adapter_test


def main():
    """Main function."""
    logger.info("Starting adapter implementation script...")

    # Run implementation tests
    result = asyncio.run(run_implementation_tests())

    if result:
        logger.info("All tests PASSED!")
        logger.info("\nNext implementation steps:")
        logger.info("1. Apply the adapter to both fixed and router apps")
        logger.info("2. Monitor usage and collect metrics on endpoint usage")
        logger.info("3. Implement authentication standardization")
        logger.info("4. Begin model and response standardization")
        logger.info("5. Run the test suite to verify progress")
    else:
        logger.error("Some tests FAILED!")

    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
