#!/usr/bin/env python3
"""
Main adapter application that integrates the fixed and router implementations.

This module serves as the entry point for the adapter service in compatibility mode.
It applies the adapter pattern to both implementations and provides a unified API interface.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, Request, Response, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Python path
# Add current directory and services directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import adapter service
sys.path.insert(0, os.path.join(current_dir, 'services'))
from api_adapter_service import (
    AuthAdapter,
    ModelAdapter,
    ResponseAdapter,
    AuthMiddleware
)

# Define apply_standardization function if api_standardization module cannot be imported
def apply_standardization(app, campaign_service=None, ai_service=None):
    logger.warning("Using mock apply_standardization function")
    return None

# Define create_adapter_app function if adapter_bridge module cannot be imported
def create_adapter_app():
    return FastAPI()

def create_unified_app():
    """
    Create a unified FastAPI application that implements the adapter pattern.

    Returns:
        FastAPI: A unified FastAPI application
    """

    # Try to import dependencies now that sys.path is set up
    try:
        from api_standardization import apply_standardization as real_apply_standardization
        logger.info("Successfully imported api_standardization module")
        globals()['apply_standardization'] = real_apply_standardization
    except ImportError as e:
        logger.warning(f"Could not import api_standardization module: {e}")

    try:
        from adapter_bridge import create_adapter_app as real_create_adapter_app
        logger.info("Successfully imported adapter_bridge module")
        globals()['create_adapter_app'] = real_create_adapter_app
    except ImportError as e:
        logger.warning(f"Could not import adapter_bridge module: {e}")
    # Create a new FastAPI app
    app = FastAPI(
        title="Maily Campaign API",
        description="Unified API for email campaign management with compatibility for both implementations",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
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

    # Add auth middleware
    app.add_middleware(
        AuthMiddleware,
        auth_adapter=auth_adapter
    )

    # Load fixed implementation
    from main_fixed import app as fixed_app, campaign_service, ai_service

    # Apply standardization to fixed app
    standardization = apply_standardization(fixed_app, campaign_service, ai_service)

    # Import application components
    adapter_app = create_adapter_app()

    # Define authentication function for routes
    async def get_authenticated_user(request: Request):
        """
        Get the authenticated user from request state.
        """
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        return user

    # Mount standardized fixed app on /api/fixed
    @app.route("/api/fixed{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def fixed_app_route(request: Request, path: str):
        """
        Route requests to fixed implementation.
        """
        # Adjust path to remove the prefix
        # This is needed because we're not using the FastAPI's mount feature
        # which would normally adjust the path
        path = path or "/"
        if not path.startswith("/"):
            path = "/" + path

        # Create a new scope with the adjusted path
        scope = request.scope.copy()
        scope["path"] = path
        scope["raw_path"] = path.encode("utf-8")

        # Call the fixed app
        return await fixed_app(scope, request.receive, request.send)

    # Router implementation routes (for compatibility in case router app is available)
    @app.route("/api/router{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def router_app_route(request: Request, path: str):
        """
        Route requests to router implementation.

        Note: This is for compatibility, but we're using the adapter bridge
        since we can't directly import the router implementation due to relative imports.
        """
        # Adjust path to remove the prefix
        path = path or "/"
        if not path.startswith("/"):
            path = "/" + path

        # Use the adapter bridge for router implementation
        scope = request.scope.copy()
        scope["path"] = path
        scope["raw_path"] = path.encode("utf-8")

        # Call the adapter app
        return await adapter_app(scope, request.receive, request.send)

    # Add unified API endpoints that use the adapter pattern
    # These endpoints can work with both authentication methods and data formats

    # The following endpoints are from the adapter_bridge.py file
    # but are registered here directly for cleaner organization

    # Campaign list endpoint
    @app.get("/api/v1/campaigns", tags=["Campaigns"])
    async def list_campaigns(
        request: Request,
        page: int = 1,
        limit: int = 10,
        status: Optional[str] = None,
        user = Depends(get_authenticated_user)
    ):
        """
        List campaigns with optional filtering and pagination.
        """
        # Use adapter_app implementation
        # Create a modified request to forwarded_app
        scope = request.scope.copy()
        scope["path"] = "/api/v1/campaigns"
        scope["query_string"] = f"page={page}&limit={limit}".encode("utf-8")
        if status:
            scope["query_string"] += f"&status={status}".encode("utf-8")

        # Use the fixed implementation via standardization
        standard_response = await fixed_app(scope, request.receive, request.send)

        # Since we're already returning the standard response,
        # we just need to return it
        return standard_response

    # Campaign creation endpoint
    @app.post("/api/v1/campaigns", tags=["Campaigns"])
    async def create_campaign(
        request: Request,
        background_tasks: BackgroundTasks,
        user = Depends(get_authenticated_user)
    ):
        """
        Create a new campaign.
        Compatible with both fixed and router formats.
        """
        try:
            # Parse request body
            body = await request.json()

            # Detect request format
            is_fixed_format = "task" in body

            # Process based on format
            if is_fixed_format:
                # Use fixed implementation directly
                campaign_id = await campaign_service.create_campaign(body)

                # Schedule content generation
                background_tasks.add_task(
                    ai_service.generate_campaign_content,
                    campaign_id=campaign_id,
                    task=body.get("task", ""),
                    model_name=body.get("model_name", "gpt-4"),
                )

                # Get estimated audience size
                audience = body.get("audience", {})
                estimated_audience = await campaign_service.estimate_audience_size(
                    audience.get("segments", []) if audience else None,
                    audience.get("exclusions", []) if audience else None,
                )

                # Prepare response in fixed format
                fixed_response = {
                    "campaign_id": campaign_id,
                    "status": "draft",
                    "preview_url": f"http://localhost:3000/preview/{campaign_id}",
                    "estimated_audience": estimated_audience,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                # Convert to standard format
                standard_response = model_adapter.fixed_to_standard(fixed_response)
            else:
                # Convert from router to fixed format
                fixed_format = model_adapter.router_request_to_fixed(body)

                # Use fixed implementation
                campaign_id = await campaign_service.create_campaign(fixed_format)

                # Schedule content generation
                background_tasks.add_task(
                    ai_service.generate_campaign_content,
                    campaign_id=campaign_id,
                    task=fixed_format.get("task", ""),
                    model_name=fixed_format.get("model_name", "gpt-4"),
                )

                # Get estimated audience size
                audience = fixed_format.get("audience", {})
                estimated_audience = await campaign_service.estimate_audience_size(
                    audience.get("segments", []) if audience else None,
                    audience.get("exclusions", []) if audience else None,
                )

                # Prepare response in fixed format
                fixed_response = {
                    "campaign_id": campaign_id,
                    "status": "draft",
                    "preview_url": f"http://localhost:3000/preview/{campaign_id}",
                    "estimated_audience": estimated_audience,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                # Convert to standard format
                standard_response = model_adapter.fixed_to_standard(fixed_response)

            # Return standardized response
            return response_adapter.standardize_response(standard_response, 201)
        except Exception as e:
            logger.exception(f"Error creating campaign: {e}")
            return response_adapter.standardize_error(f"Error creating campaign: {str(e)}", 500)

    # Compatibility endpoint for fixed implementation
    @app.post("/create_campaign", tags=["Compatibility"])
    async def create_campaign_fixed_compat(
        request: Request,
        background_tasks: BackgroundTasks,
        user = Depends(get_authenticated_user)
    ):
        """
        Compatibility endpoint for fixed implementation.
        Redirects to the standardized endpoint.
        """
        return await create_campaign(request, background_tasks, user)

    # Add more endpoints based on the ones in adapter_bridge.py
    # Each endpoint should use the appropriate adapter patterns

    # Customize OpenAPI documentation
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description + "\n\n"
                      + "This API provides compatibility between the fixed and router implementations.",
            routes=app.routes,
        )

        # Add authentication schemes
        openapi_schema["components"] = {
            "securitySchemes": {
                "ApiKey": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                },
                "BearerToken": {
                    "type": "http",
                    "scheme": "bearer"
                }
            }
        }

        # Add security requirement to all operations
        if "paths" in openapi_schema:
            for path in openapi_schema["paths"].values():
                for operation in path.values():
                    operation["security"] = [
                        {"ApiKey": []},
                        {"BearerToken": []}
                    ]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Add startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting unified adapter application")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down unified adapter application")

    logger.info("Unified adapter application initialized")
    return app

# Create the unified app
app = create_unified_app()

if __name__ == "__main__":
    import uvicorn

    # Run the adapter app
    logger.info("Starting unified adapter server")
    uvicorn.run(app, host="0.0.0.0", port=8002)
