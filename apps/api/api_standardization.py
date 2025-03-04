#!/usr/bin/env python3
"""
API Standardization module for implementing the standardized API structure.

This module applies the endpoint structure, authentication, and response standardization
to the fixed implementation, implementing missing endpoints to complete the API coverage.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Path, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
import os
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
sys.path.insert(0, os.path.join(script_dir, 'services'))

# Import the adapter service
from api_adapter_service import (
    AuthAdapter,
    ModelAdapter,
    ResponseAdapter,
    CampaignStatus
)

class APIStandardization:
    """
    API Standardization implementation that adds router-style endpoints
    to the fixed implementation and provides compatibility.
    """

    def __init__(self, app: FastAPI, campaign_service=None, ai_service=None):
        """
        Initialize the API standardization.

        Args:
            app: FastAPI app to apply standardization to
            campaign_service: Campaign service instance
            ai_service: AI service instance
        """
        self.app = app
        self.campaign_service = campaign_service
        self.ai_service = ai_service

        # Initialize adapters
        self.auth_adapter = AuthAdapter()
        self.model_adapter = ModelAdapter()
        self.response_adapter = ResponseAdapter()

        # Apply standardization
        self._apply_standard_auth()
        self._apply_standard_endpoints()

        logger.info("API standardization applied")

    def _apply_standard_auth(self):
        """Apply standardized authentication."""

        # Add unified authentication middleware
        @self.app.middleware("http")
        async def unified_auth_middleware(request: Request, call_next):
            # Skip authentication for health endpoints
            if request.url.path.startswith("/health"):
                return await call_next(request)

            # Skip authentication for docs
            if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
                return await call_next(request)

            # Verify authentication using either method
            user = await self.auth_adapter.verify_authentication(request)
            if user:
                # Store user in request state
                request.state.user = user
                # Continue with the request
                return await call_next(request)

            # If both authentication methods fail, return 401
            if request.url.path != "/metrics":  # Don't wrap metrics failures
                return JSONResponse(
                    status_code=401,
                    content={"status": "error", "error": {"detail": "Invalid authentication credentials"}}
                )

            # For metrics endpoint, let it handle auth failure itself
            return await call_next(request)

        logger.info("Standardized authentication middleware added")

    def _apply_standard_endpoints(self):
        """Apply standardized endpoint structure and add missing endpoints."""

        # Campaign list endpoint (new)
        @self.app.get("/api/v1/campaigns", tags=["Campaigns"])
        async def list_campaigns(
            page: int = Query(1, ge=1, description="Page number"),
            limit: int = Query(10, ge=1, le=100, description="Items per page"),
            status: Optional[str] = Query(None, description="Filter by status"),
            request: Request = None
        ):
            """
            List campaigns with optional filtering and pagination.
            """
            # Get user from request state
            user = getattr(request.state, "user", None)
            if not user:
                return self.response_adapter.standardize_error("Authentication required", 401)

            # Mock implementation
            campaigns = [
                {
                    "campaign_id": f"campaign-{i}",
                    "task": f"Campaign {i}",
                    "status": "draft",
                    "preview_url": f"https://preview.justmaily.com/preview/campaign-{i}",
                    "estimated_audience": 1000,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                for i in range(1, limit + 1)
            ]

            # Filter by status if provided
            if status:
                campaigns = [c for c in campaigns if c["status"] == status.lower()]

            # Convert to standard format
            standard_campaigns = [
                self.model_adapter.fixed_to_standard(campaign)
                for campaign in campaigns
            ]

            # Return with pagination info
            return self.response_adapter.standardize_response({
                "data": standard_campaigns,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": 100,  # Mock total
                    "pages": 10    # Mock pages
                }
            })

        # Campaign creation endpoint (standardized)
        @self.app.post("/api/v1/campaigns", tags=["Campaigns"])
        async def create_campaign(
            request: Request,
            background_tasks: BackgroundTasks
        ):
            """
            Create a new campaign.
            Compatible with both fixed and router formats.
            """
            # Get user from request state
            user = getattr(request.state, "user", None)
            if not user:
                return self.response_adapter.standardize_error("Authentication required", 401)

            # Parse request body
            try:
                body = await request.json()
            except ValueError:
                return self.response_adapter.standardize_error("Invalid request body", 400)

            # Detect request format
            is_fixed_format = "task" in body

            # Import the create_campaign endpoint from fixed implementation
            from main_fixed import create_campaign as fixed_create_campaign
            from main_fixed import CampaignRequest

            try:
                if is_fixed_format:
                    # Create request object
                    campaign_req = CampaignRequest(**body)

                    # Call fixed implementation
                    response = await fixed_create_campaign(campaign_req, background_tasks, api_key="test-api-key")

                    # Convert to standard format
                    standard_response = self.model_adapter.fixed_to_standard({
                        "campaign_id": response["campaign_id"],
                        "task": body.get("task", ""),
                        "status": response["status"],
                        "preview_url": response["preview_url"],
                        "estimated_audience": response["estimated_audience"],
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    })
                else:
                    # Convert router format to fixed format
                    fixed_format = self.model_adapter.router_request_to_fixed(body)

                    # Create request object
                    campaign_req = CampaignRequest(**fixed_format)

                    # Call fixed implementation
                    response = await fixed_create_campaign(campaign_req, background_tasks, api_key="test-api-key")

                    # Convert to standard format
                    standard_response = self.model_adapter.fixed_to_standard({
                        "campaign_id": response["campaign_id"],
                        "task": fixed_format.get("task", ""),
                        "status": response["status"],
                        "preview_url": response["preview_url"],
                        "estimated_audience": response["estimated_audience"],
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    })

                # Return standardized response
                return self.response_adapter.standardize_response(standard_response, 201)
            except ValidationError as e:
                return self.response_adapter.standardize_error(f"Validation error: {str(e)}", 400)
            except Exception as e:
                logger.exception(f"Error creating campaign: {e}")
                return self.response_adapter.standardize_error(f"Error creating campaign: {str(e)}", 500)

        # Campaign retrieval endpoint (new)
        @self.app.get("/api/v1/campaigns/{campaign_id}", tags=["Campaigns"])
        async def get_campaign(
            campaign_id: str = Path(..., description="Campaign ID"),
            request: Request = None
        ):
            """
            Get campaign details.
            """
            # Get user from request state
            user = getattr(request.state, "user", None)
            if not user:
                return self.response_adapter.standardize_error("Authentication required", 401)

            # Mock implementation
            fixed_response = {
                "campaign_id": campaign_id,
                "task": "Campaign Task",
                "status": "draft",
                "preview_url": f"https://preview.justmaily.com/preview/{campaign_id}",
                "estimated_audience": 1000,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Convert to standard format
            standard_response = self.model_adapter.fixed_to_standard(fixed_response)

            # Return standardized response
            return self.response_adapter.standardize_response(standard_response)

        # Campaign update endpoint (new)
        @self.app.put("/api/v1/campaigns/{campaign_id}", tags=["Campaigns"])
        async def update_campaign(
            campaign_id: str = Path(..., description="Campaign ID"),
            request: Request = None
        ):
            """
            Update campaign details.
            """
            # Get user from request state
            user = getattr(request.state, "user", None)
            if not user:
                return self.response_adapter.standardize_error("Authentication required", 401)

            # Parse request body
            try:
                body = await request.json()
            except ValueError:
                return self.response_adapter.standardize_error("Invalid request body", 400)

            # Mock implementation
            fixed_response = {
                "campaign_id": campaign_id,
                "task": body.get("name", "Updated Campaign"),
                "status": "draft",
                "preview_url": f"https://preview.justmaily.com/preview/{campaign_id}",
                "estimated_audience": 1000,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Convert to standard format
            standard_response = self.model_adapter.fixed_to_standard(fixed_response)

            # Return standardized response
            return self.response_adapter.standardize_response(standard_response)

        # Campaign deletion endpoint (new)
        @self.app.delete("/api/v1/campaigns/{campaign_id}", tags=["Campaigns"])
        async def delete_campaign(
            campaign_id: str = Path(..., description="Campaign ID"),
            request: Request = None
        ):
            """
            Delete a campaign.
            """
            # Get user from request state
            user = getattr(request.state, "user", None)
            if not user:
                return self.response_adapter.standardize_error("Authentication required", 401)

            # Return success response
            return self.response_adapter.standardize_response(
                {"message": f"Campaign {campaign_id} deleted successfully"},
                status_code=200
            )

        # Campaign sending endpoint (new)
        @self.app.post("/api/v1/campaigns/{campaign_id}/send", tags=["Campaigns"])
        async def send_campaign(
            campaign_id: str = Path(..., description="Campaign ID"),
            request: Request = None,
            background_tasks: BackgroundTasks = None
        ):
            """
            Send a campaign.
            """
            # Get user from request state
            user = getattr(request.state, "user", None)
            if not user:
                return self.response_adapter.standardize_error("Authentication required", 401)

            # Mock implementation
            fixed_response = {
                "campaign_id": campaign_id,
                "task": "Campaign Task",
                "status": "sending",
                "preview_url": f"https://preview.justmaily.com/preview/{campaign_id}",
                "estimated_audience": 1000,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Convert to standard format
            standard_response = self.model_adapter.fixed_to_standard(fixed_response)

            # Return standardized response
            return self.response_adapter.standardize_response(standard_response)

        # Campaign analytics endpoint (new)
        @self.app.get("/api/v1/campaigns/{campaign_id}/analytics", tags=["Campaigns"])
        async def get_campaign_analytics(
            campaign_id: str = Path(..., description="Campaign ID"),
            request: Request = None
        ):
            """
            Get campaign analytics.
            """
            # Get user from request state
            user = getattr(request.state, "user", None)
            if not user:
                return self.response_adapter.standardize_error("Authentication required", 401)

            # Mock implementation
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
                "status": "SENT",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Return standardized response
            return self.response_adapter.standardize_response(analytics_data)

        # Background tasks endpoint (new)
        @self.app.get("/api/v1/tasks/{task_id}", tags=["Background Tasks"])
        async def get_task_status(
            task_id: str = Path(..., description="Task ID"),
            request: Request = None
        ):
            """
            Get background task status.
            """
            # Get user from request state
            user = getattr(request.state, "user", None)
            if not user:
                return self.response_adapter.standardize_error("Authentication required", 401)

            # Mock implementation
            task_data = {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "result": {
                    "success": True,
                    "message": "Task completed successfully"
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat()
            }

            # Return standardized response
            return self.response_adapter.standardize_response(task_data)

        # Wrap existing health endpoints for standardized responses
        existing_health_endpoint = next(
            (route.endpoint for route in self.app.routes if getattr(route, "path", None) == "/health"),
            None
        )

        if existing_health_endpoint:
            @self.app.get("/api/v1/health", tags=["System"])
            async def standardized_health():
                """
                Check system health with standardized response.
                """
                response = await existing_health_endpoint()
                return self.response_adapter.standardize_response(response)

        logger.info("Standardized endpoints added to fixed implementation")

# Usage:
# from main_fixed import app as fixed_app, campaign_service, ai_service
# standardization = APIStandardization(fixed_app, campaign_service, ai_service)

def apply_standardization(app, campaign_service=None, ai_service=None):
    """
    Apply API standardization to the given app.

    Args:
        app: FastAPI app to standardize
        campaign_service: Campaign service instance
        ai_service: AI service instance

    Returns:
        APIStandardization: The standardization instance
    """
    return APIStandardization(app, campaign_service, ai_service)

if __name__ == "__main__":
    # Import and apply to fixed implementation
    from main_fixed import app as fixed_app, campaign_service, ai_service

    standardization = APIStandardization(fixed_app, campaign_service, ai_service)

    # Run the app
    import uvicorn
    logger.info("Starting standardized fixed implementation")
    uvicorn.run(fixed_app, host="0.0.0.0", port=8001)
