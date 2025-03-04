#!/usr/bin/env python3
"""
Adapter bridge module for integrating fixed and router implementations.

This module applies the adapter service to both implementations, providing:
1. Authentication compatibility between API key and Bearer token
2. Endpoint mapping between fixed and router implementations
3. Data model conversion between different formats
4. Response format standardization
"""

import os
import sys
import logging
from fastapi import FastAPI, Request, Depends, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Python path and import the adapter service
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(script_dir, 'services'))
from api_adapter_service import (
    AuthAdapter,
    ModelAdapter,
    ResponseAdapter,
    setup_api_adapter
)

# Import both implementations without initializing them
# We'll use their app instances and service instances
from main_fixed import app as fixed_app, campaign_service as fixed_campaign_service, ai_service as fixed_ai_service
try:
    # This may fail if relative imports are used in main.py
    # If it fails, we'll handle it in the compatibility mode
    from main import app as router_app
    router_app_available = True
except ImportError:
    logger.warning("Router app could not be imported directly. Running in fixed-only mode.")
    router_app_available = False

def create_adapter_app():
    """
    Create a FastAPI app with adapter service integrated for both implementations.

    Returns:
        FastAPI: A new FastAPI app with adapter service configured
    """
    adapter_app = FastAPI(
        title="Campaign API Adapter Bridge",
        description="Unified API for email campaign management with compatibility for both implementations",
        version="1.0.0",
    )

    # Add CORS middleware
    adapter_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create adapter instances
    auth_adapter = AuthAdapter()
    model_adapter = ModelAdapter()
    response_adapter = ResponseAdapter()

    # Register authentication middleware for unified auth
    @adapter_app.middleware("http")
    async def unified_auth_middleware(request: Request, call_next):
        # Verify authentication using either method
        user = await auth_adapter.verify_authentication(request)
        if user:
            # Store user in request state
            request.state.user = user
            # Continue with the request
            return await call_next(request)

        # If both authentication methods fail, return 401
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid authentication credentials"}
        )

    # Create standardized API endpoints
    # Campaign creation endpoint - accepts both formats
    @adapter_app.post("/api/v1/campaigns", tags=["Campaigns"])
    async def create_campaign_unified(request: Request, background_tasks: BackgroundTasks):
        """
        Unified endpoint for campaign creation that works with both formats.
        """
        # Get user from request state (set by middleware)
        user = getattr(request.state, "user", None)
        if not user:
            return response_adapter.standardize_error("Authentication required", 401)

        # Parse request body
        try:
            body = await request.json()
        except ValueError:
            return response_adapter.standardize_error("Invalid request body", 400)

        # Detect request format
        is_fixed_format = "task" in body

        # Process based on format
        try:
            if is_fixed_format:
                # Use fixed implementation directly
                campaign_id = await fixed_campaign_service.create_campaign(body)

                # Schedule content generation
                background_tasks.add_task(
                    fixed_ai_service.generate_campaign_content,
                    campaign_id=campaign_id,
                    task=body.get("task", ""),
                    model_name=body.get("model_name", "gpt-4"),
                )

                # Get estimated audience size
                audience = body.get("audience", {})
                estimated_audience = await fixed_campaign_service.estimate_audience_size(
                    audience.get("segments", []) if audience else None,
                    audience.get("exclusions", []) if audience else None,
                )

                # Prepare response in fixed format
                campaign_response = {
                    "campaign_id": campaign_id,
                    "status": "draft",
                    "preview_url": f"https://preview.justmaily.com/preview/{campaign_id}",
                    "estimated_audience": estimated_audience,
                }

                # Convert to standard format and then to router format
                standard_response = model_adapter.fixed_to_standard(campaign_response)
                router_response = model_adapter.standard_to_router(standard_response)

                # Return standardized response
                return response_adapter.standardize_response(router_response, status_code=201)
            else:
                # Convert from router to fixed format
                fixed_format = model_adapter.router_request_to_fixed(body)

                # Use fixed implementation
                campaign_id = await fixed_campaign_service.create_campaign(fixed_format)

                # Schedule content generation
                background_tasks.add_task(
                    fixed_ai_service.generate_campaign_content,
                    campaign_id=campaign_id,
                    task=fixed_format.get("task", ""),
                    model_name=fixed_format.get("model_name", "gpt-4"),
                )

                # Get estimated audience size
                audience = fixed_format.get("audience", {})
                estimated_audience = await fixed_campaign_service.estimate_audience_size(
                    audience.get("segments", []) if audience else None,
                    audience.get("exclusions", []) if audience else None,
                )

                # Prepare response in fixed format
                fixed_response = {
                    "campaign_id": campaign_id,
                    "status": "draft",
                    "preview_url": f"https://preview.justmaily.com/preview/{campaign_id}",
                    "estimated_audience": estimated_audience,
                }

                # Convert to standard format and then to router format
                standard_response = model_adapter.fixed_to_standard(fixed_response)

                # Return standardized response
                return response_adapter.standardize_response(standard_response, status_code=201)
        except ValueError as e:
            return response_adapter.standardize_error(str(e), 400)
        except Exception as e:
            logger.exception(f"Error creating campaign: {e}")
            return response_adapter.standardize_error("Internal server error", 500)

    # Compatibility endpoint for fixed implementation
    @adapter_app.post("/create_campaign", tags=["Compatibility"])
    async def create_campaign_fixed_compat(request: Request, background_tasks: BackgroundTasks):
        """
        Compatibility endpoint for fixed implementation.
        Redirects to the standardized endpoint.
        """
        return await create_campaign_unified(request, background_tasks)

    # Campaign retrieval endpoint
    @adapter_app.get("/api/v1/campaigns/{campaign_id}", tags=["Campaigns"])
    async def get_campaign(campaign_id: str, request: Request):
        """
        Get campaign details.
        """
        # Get user from request state (set by middleware)
        user = getattr(request.state, "user", None)
        if not user:
            return response_adapter.standardize_error("Authentication required", 401)

        # Use fixed implementation for now
        # In a complete implementation, this would query the database directly

        # Mock response for demonstration
        fixed_response = {
            "campaign_id": campaign_id,
            "task": "Campaign Task",
            "status": "draft",
            "preview_url": f"https://preview.justmaily.com/preview/{campaign_id}",
            "estimated_audience": 1000,
        }

        # Convert to standard format
        standard_response = model_adapter.fixed_to_standard(fixed_response)

        # Return standardized response
        return response_adapter.standardize_response(standard_response)

    # Campaign update endpoint
    @adapter_app.put("/api/v1/campaigns/{campaign_id}", tags=["Campaigns"])
    async def update_campaign(campaign_id: str, request: Request):
        """
        Update campaign details.
        """
        # Get user from request state (set by middleware)
        user = getattr(request.state, "user", None)
        if not user:
            return response_adapter.standardize_error("Authentication required", 401)

        # Parse request body
        try:
            body = await request.json()
        except ValueError:
            return response_adapter.standardize_error("Invalid request body", 400)

        # Implementation would update the campaign in the database
        # Mock response for demonstration
        fixed_response = {
            "campaign_id": campaign_id,
            "task": body.get("name", "Updated Campaign"),
            "status": "draft",
            "preview_url": f"https://preview.justmaily.com/preview/{campaign_id}",
            "estimated_audience": 1000,
        }

        # Convert to standard format
        standard_response = model_adapter.fixed_to_standard(fixed_response)

        # Return standardized response
        return response_adapter.standardize_response(standard_response)

    # Campaign deletion endpoint
    @adapter_app.delete("/api/v1/campaigns/{campaign_id}", tags=["Campaigns"])
    async def delete_campaign(campaign_id: str, request: Request):
        """
        Delete a campaign.
        """
        # Get user from request state (set by middleware)
        user = getattr(request.state, "user", None)
        if not user:
            return response_adapter.standardize_error("Authentication required", 401)

        # Implementation would delete the campaign from the database
        # Return success response
        return response_adapter.standardize_response(
            {"message": f"Campaign {campaign_id} deleted successfully"},
            status_code=200
        )

    # Campaign sending endpoint
    @adapter_app.post("/api/v1/campaigns/{campaign_id}/send", tags=["Campaigns"])
    async def send_campaign(campaign_id: str, request: Request, background_tasks: BackgroundTasks):
        """
        Send a campaign.
        """
        # Get user from request state (set by middleware)
        user = getattr(request.state, "user", None)
        if not user:
            return response_adapter.standardize_error("Authentication required", 401)

        # Implementation would initiate sending the campaign
        # Mock response for demonstration
        fixed_response = {
            "campaign_id": campaign_id,
            "task": "Campaign Task",
            "status": "sending",
            "preview_url": f"https://preview.justmaily.com/preview/{campaign_id}",
            "estimated_audience": 1000,
        }

        # Convert to standard format
        standard_response = model_adapter.fixed_to_standard(fixed_response)

        # Return standardized response
        return response_adapter.standardize_response(standard_response)

    # Campaign analytics endpoint
    @adapter_app.get("/api/v1/campaigns/{campaign_id}/analytics", tags=["Campaigns"])
    async def get_campaign_analytics(campaign_id: str, request: Request):
        """
        Get campaign analytics.
        """
        # Get user from request state (set by middleware)
        user = getattr(request.state, "user", None)
        if not user:
            return response_adapter.standardize_error("Authentication required", 401)

        # Implementation would fetch analytics data
        # Mock response for demonstration
        analytics_data = {
            "campaign_id": campaign_id,
            "sent": 1000,
            "delivered": 950,
            "opened": 500,
            "clicked": 200,
            "open_rate": 0.5,
            "click_rate": 0.2,
            "bounced": 50,
            "unsubscribed": 5,
        }

        # Return standardized response
        return response_adapter.standardize_response(analytics_data)

    # Health endpoints (compatible with both implementations)
    @adapter_app.get("/health", tags=["System"])
    async def health_check():
        """
        Check system health.
        """
        # Forward to fixed implementation
        response = await fixed_app.routes[12].endpoint()
        return response_adapter.standardize_response(response)

    @adapter_app.get("/health/ready", tags=["System"])
    async def readiness_check():
        """
        Check if the system is ready to serve requests.
        """
        # Forward to fixed implementation
        response = await fixed_app.routes[13].endpoint()
        return response_adapter.standardize_response(response)

    @adapter_app.get("/health/live", tags=["System"])
    async def liveness_check():
        """
        Check if the system is alive.
        """
        # Forward to fixed implementation
        response = await fixed_app.routes[14].endpoint()
        return response_adapter.standardize_response(response)

    # Metrics endpoint
    @adapter_app.get("/metrics", tags=["System"])
    async def metrics(request: Request):
        """
        Get system metrics.
        Requires authentication with either method.
        """
        # Get user from request state (set by middleware)
        user = getattr(request.state, "user", None)
        if not user:
            return response_adapter.standardize_error("Authentication required", 401)

        # Forward to fixed implementation
        response = await fixed_app.routes[15].endpoint(api_key="test-api-key")
        return response_adapter.standardize_response(response)

    # Model configuration endpoint
    @adapter_app.post("/configure_model", tags=["AI Models"])
    async def configure_model(request: Request):
        """
        Configure an AI model.
        Compatible with both implementations.
        """
        # Get user from request state (set by middleware)
        user = getattr(request.state, "user", None)
        if not user:
            return response_adapter.standardize_error("Authentication required", 401)

        # Parse request body
        try:
            body = await request.json()
        except ValueError:
            return response_adapter.standardize_error("Invalid request body", 400)

        # Forward to fixed implementation
        from main_fixed import configure_model as fixed_configure_model
        from main_fixed import ModelConfig

        # Create ModelConfig instance
        config = ModelConfig(
            model_name=body.get("model_name"),
            api_key=body.get("api_key"),
            temperature=body.get("temperature", 0.7),
            max_tokens=body.get("max_tokens", 1000)
        )

        # Call fixed implementation
        try:
            response = await fixed_configure_model(config, api_key="test-api-key")
            return response_adapter.standardize_response(response)
        except Exception as e:
            logger.exception(f"Error configuring model: {e}")
            return response_adapter.standardize_error("Error configuring model", 500)

    # Add more endpoints as needed

    logger.info("Adapter bridge initialized with standardized endpoints")
    return adapter_app

# Create the adapter app
adapter_app = create_adapter_app()

if __name__ == "__main__":
    import uvicorn

    # Run the adapter app
    logger.info("Starting adapter bridge server")
    uvicorn.run(adapter_app, host="0.0.0.0", port=8001)
