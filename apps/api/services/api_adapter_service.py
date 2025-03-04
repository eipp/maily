"""API Adapter Service for bridging fixed and router implementations.

This service provides adapter functions that enable:
1. Authentication compatibility between API key and Bearer token
2. Endpoint mapping between fixed and router implementations
3. Data model conversion between different formats
4. Response format standardization
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CampaignStatus(str, Enum):
    """Standardized campaign status enum."""
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    SENDING = "SENDING"
    SENT = "SENT"
    ERROR = "ERROR"


class StandardCampaignResponse(BaseModel):
    """Standardized campaign response model."""
    id: str
    name: str
    subject: Optional[str] = None
    content: Optional[str] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    user_id: Optional[int] = None
    created_at: str
    updated_at: str
    scheduled_time: Optional[str] = None
    open_rate: Optional[float] = 0.0
    click_rate: Optional[float] = 0.0
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AuthAdapter:
    """Authentication adapter between API key and Bearer token."""

    def __init__(self, api_key_header="X-API-Key", token_secret="your-token-secret"):
        """Initialize the auth adapter.

        Args:
            api_key_header: Header name for API key authentication
            token_secret: Secret for validating/generating JWT tokens
        """
        self.api_key_header = api_key_header
        self.token_secret = token_secret
        # In a real implementation, you would load mappings from a database
        self.api_key_to_user = {
            "test-api-key": {"id": 1, "name": "Test User", "email": "test@example.com"}
        }
        self.user_to_api_key = {1: "test-api-key"}

    async def verify_authentication(self, request: Request) -> Optional[Dict]:
        """Verify authentication using either API key or Bearer token.

        Args:
            request: FastAPI request object

        Returns:
            User dict if authentication is valid, None otherwise
        """
        # Try API key first
        api_key = request.headers.get(self.api_key_header)
        if api_key and api_key in self.api_key_to_user:
            return self.api_key_to_user[api_key]

        # Then try Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                # In a real implementation, you would validate JWT token
                # and extract user information from it
                if token == "test_token":  # Simplified for example
                    return {"id": 1, "name": "Test User", "email": "test@example.com"}

            except Exception as e:
                logger.error(f"Token validation error: {str(e)}")

        return None

    def api_key_to_token(self, api_key: str) -> Optional[str]:
        """Convert API key to Bearer token.

        Args:
            api_key: API key to convert

        Returns:
            Bearer token if conversion is successful, None otherwise
        """
        if api_key in self.api_key_to_user:
            user = self.api_key_to_user[api_key]
            # In a real implementation, you would generate a JWT token
            # with the user information
            return "test_token"  # Simplified for example

        return None

    def token_to_api_key(self, token: str) -> Optional[str]:
        """Convert Bearer token to API key.

        Args:
            token: Bearer token to convert

        Returns:
            API key if conversion is successful, None otherwise
        """
        try:
            # In a real implementation, you would validate JWT token
            # and extract user information from it
            if token == "test_token":  # Simplified for example
                user_id = 1  # Would normally extract from token
                return self.user_to_api_key.get(user_id)
        except Exception as e:
            logger.error(f"Token to API key conversion error: {str(e)}")

        return None


class ModelAdapter:
    """Model adapter between fixed and router implementations."""

    @staticmethod
    def fixed_to_standard(fixed_data: Dict) -> StandardCampaignResponse:
        """Convert fixed format to standardized format.

        Args:
            fixed_data: Campaign data in fixed format

        Returns:
            Standardized campaign response
        """
        # Extract and normalize fields
        campaign_id = fixed_data.get("campaign_id", "")
        status = fixed_data.get("status", "draft").upper()

        # Create timestamps if not present
        now = datetime.now().isoformat()

        # Build standardized response
        return StandardCampaignResponse(
            id=campaign_id,
            name=fixed_data.get("task", "Unnamed Campaign"),
            subject=fixed_data.get("subject", ""),
            content=fixed_data.get("content", ""),
            status=getattr(CampaignStatus, status.upper(), CampaignStatus.DRAFT),
            user_id=fixed_data.get("user_id", None),
            created_at=fixed_data.get("created_at", now),
            updated_at=fixed_data.get("updated_at", now),
            scheduled_time=fixed_data.get("scheduled_time", None),
            open_rate=fixed_data.get("open_rate", 0.0),
            click_rate=fixed_data.get("click_rate", 0.0),
            metadata=fixed_data.get("metadata", {})
        )

    @staticmethod
    def router_to_standard(router_data: Dict) -> StandardCampaignResponse:
        """Convert router format to standardized format.

        Args:
            router_data: Campaign data in router format

        Returns:
            Standardized campaign response
        """
        # Extract and normalize fields
        campaign_id = str(router_data.get("id", ""))
        status = router_data.get("status", "DRAFT")

        # Build standardized response
        return StandardCampaignResponse(
            id=campaign_id,
            name=router_data.get("name", ""),
            subject=router_data.get("subject", ""),
            content=router_data.get("content", ""),
            status=getattr(CampaignStatus, status, CampaignStatus.DRAFT),
            user_id=router_data.get("user_id", None),
            created_at=router_data.get("created_at", datetime.now().isoformat()),
            updated_at=router_data.get("updated_at", datetime.now().isoformat()),
            scheduled_time=router_data.get("schedule_time", None),
            open_rate=router_data.get("open_rate", 0.0),
            click_rate=router_data.get("click_rate", 0.0),
            metadata=router_data.get("metadata", {})
        )

    @staticmethod
    def standard_to_fixed(standard_data: StandardCampaignResponse) -> Dict:
        """Convert standardized format to fixed format.

        Args:
            standard_data: Standardized campaign response

        Returns:
            Campaign data in fixed format
        """
        # Convert to dict format
        if isinstance(standard_data, BaseModel):
            standard_data = standard_data.dict()

        # Map to fixed format
        return {
            "campaign_id": standard_data.get("id", ""),
            "task": standard_data.get("name", ""),
            "status": standard_data.get("status", "DRAFT").lower(),
            "preview_url": f"https://preview.justmaily.com/preview/{standard_data.get('id', '')}",
            "estimated_audience": standard_data.get("metadata", {}).get("estimated_audience", 0),
            "subject": standard_data.get("subject", ""),
            "content": standard_data.get("content", ""),
            "created_at": standard_data.get("created_at", ""),
            "updated_at": standard_data.get("updated_at", ""),
            "scheduled_time": standard_data.get("scheduled_time", None),
            "metadata": standard_data.get("metadata", {})
        }

    @staticmethod
    def standard_to_router(standard_data: StandardCampaignResponse) -> Dict:
        """Convert standardized format to router format.

        Args:
            standard_data: Standardized campaign response

        Returns:
            Campaign data in router format
        """
        # Convert to dict format
        if isinstance(standard_data, BaseModel):
            standard_data = standard_data.dict()

        # Map to router format
        return {
            "id": standard_data.get("id", ""),
            "name": standard_data.get("name", ""),
            "subject": standard_data.get("subject", ""),
            "content": standard_data.get("content", ""),
            "status": standard_data.get("status", "DRAFT"),
            "user_id": standard_data.get("user_id", None),
            "created_at": standard_data.get("created_at", ""),
            "updated_at": standard_data.get("updated_at", ""),
            "schedule_time": standard_data.get("scheduled_time", None),
            "open_rate": standard_data.get("open_rate", 0.0),
            "click_rate": standard_data.get("click_rate", 0.0),
            "metadata": standard_data.get("metadata", {})
        }

    @staticmethod
    def fixed_request_to_router(fixed_request: Dict) -> Dict:
        """Convert fixed request format to router request format.

        Args:
            fixed_request: Campaign request in fixed format

        Returns:
            Campaign request in router format
        """
        # Extract fields
        task = fixed_request.get("task", "")
        model_name = fixed_request.get("model_name", "gpt-4")
        audience = fixed_request.get("audience", {})

        # Convert to router format
        return {
            "name": task,
            "subject": f"Generated: {task}",  # Default subject based on task
            "content": "",  # Will be populated by AI
            "model_name": model_name,
            "segments": audience.get("segments", []),
            "exclusions": audience.get("exclusions", [])
        }

    @staticmethod
    def router_request_to_fixed(router_request: Dict) -> Dict:
        """Convert router request format to fixed request format.

        Args:
            router_request: Campaign request in router format

        Returns:
            Campaign request in fixed format
        """
        # Extract fields
        name = router_request.get("name", "")
        segments = router_request.get("segments", [])
        exclusions = router_request.get("exclusions", [])
        model_name = router_request.get("model_name", "gpt-4")

        # Convert to fixed format
        return {
            "task": name,
            "model_name": model_name,
            "audience": {
                "segments": segments,
                "exclusions": exclusions
            }
        }


class ResponseAdapter:
    """Response adapter for standardizing response formats."""

    @staticmethod
    def standardize_response(
        data: Any,
        status_code: int = 200,
        message: Optional[str] = None
    ) -> JSONResponse:
        """Create standardized response.

        Args:
            data: Response data
            status_code: HTTP status code
            message: Optional message

        Returns:
            Standardized JSON response
        """
        response_body = {
            "data": data,
            "status": "success" if status_code < 400 else "error"
        }

        if message:
            response_body["message"] = message

        return JSONResponse(
            status_code=status_code,
            content=response_body
        )

    @staticmethod
    def standardize_error(
        detail: str,
        status_code: int = 400,
        error_code: Optional[str] = None
    ) -> JSONResponse:
        """Create standardized error response.

        Args:
            detail: Error detail
            status_code: HTTP status code
            error_code: Optional error code

        Returns:
            Standardized JSON error response
        """
        response_body = {
            "status": "error",
            "error": {
                "detail": detail
            }
        }

        if error_code:
            response_body["error"]["code"] = error_code

        return JSONResponse(
            status_code=status_code,
            content=response_body
        )


class EndpointAdapter:
    """Adapter for mapping between endpoints."""

    def __init__(
        self,
        app: FastAPI,
        fixed_app_routes: Optional[Dict] = None,
        router_app_routes: Optional[Dict] = None,
        auth_adapter: Optional[AuthAdapter] = None,
        model_adapter: Optional[ModelAdapter] = None,
        response_adapter: Optional[ResponseAdapter] = None
    ):
        """Initialize the endpoint adapter.

        Args:
            app: FastAPI app to attach routes to
            fixed_app_routes: Dict mapping fixed app route patterns to handlers
            router_app_routes: Dict mapping router app route patterns to handlers
            auth_adapter: Authentication adapter
            model_adapter: Model adapter
            response_adapter: Response adapter
        """
        self.app = app
        self.fixed_app_routes = fixed_app_routes or {}
        self.router_app_routes = router_app_routes or {}
        self.auth_adapter = auth_adapter or AuthAdapter()
        self.model_adapter = model_adapter or ModelAdapter()
        self.response_adapter = response_adapter or ResponseAdapter()

    def add_fixed_to_router_adapter(self, path_pattern: str):
        """Add adapter for fixed to router endpoint.

        Args:
            path_pattern: Path pattern to match
        """
        # This is a simplified example - in a real implementation,
        # you would use more sophisticated path matching
        path_parts = path_pattern.split('/')

        if path_parts[1] == "create_campaign":
            # Map /create_campaign to /campaigns/
            @self.app.post("/campaigns/", status_code=201)
            async def adapter_create_campaign(request: Request):
                # Authenticate
                user = await self.auth_adapter.verify_authentication(request)
                if not user:
                    return self.response_adapter.standardize_error(
                        "Invalid authentication credentials", 401)

                # Get request body
                try:
                    body = await request.json()
                except ValueError:
                    return self.response_adapter.standardize_error(
                        "Invalid request body", 400)

                # Convert router format to fixed format
                fixed_format = self.model_adapter.router_request_to_fixed(body)

                # Get API key for fixed app
                api_key = self.auth_adapter.token_to_api_key("test_token")

                # Call fixed app endpoint
                # In a real implementation, you would use HTTP client to call the endpoint
                fixed_response = self.fixed_app_routes["/create_campaign"](
                    fixed_format, api_key)

                # Convert fixed response to standardized format
                standard_response = self.model_adapter.fixed_to_standard(fixed_response)

                # Convert to router format
                router_response = self.model_adapter.standard_to_router(standard_response)

                # Return standardized response
                return self.response_adapter.standardize_response(router_response, 201)

    def add_router_to_fixed_adapter(self, path_pattern: str):
        """Add adapter for router to fixed endpoint.

        Args:
            path_pattern: Path pattern to match
        """
        # This is a simplified example - in a real implementation,
        # you would use more sophisticated path matching
        path_parts = path_pattern.split('/')

        if len(path_parts) >= 2 and path_parts[1] == "campaigns":
            if len(path_parts) == 2 and path_parts[-1] == "campaigns":
                # Map /campaigns/ to /create_campaign
                @self.app.post("/create_campaign")
                async def adapter_router_create_campaign(request: Request):
                    # Authenticate
                    user = await self.auth_adapter.verify_authentication(request)
                    if not user:
                        return self.response_adapter.standardize_error(
                            "Invalid authentication credentials", 401)

                    # Get request body
                    try:
                        body = await request.json()
                    except ValueError:
                        return self.response_adapter.standardize_error(
                            "Invalid request body", 400)

                    # Convert fixed format to router format
                    router_format = self.model_adapter.fixed_request_to_router(body)

                    # Get Bearer token for router app
                    token = self.auth_adapter.api_key_to_token(
                        request.headers.get("X-API-Key", ""))

                    # Call router app endpoint
                    # In a real implementation, you would use HTTP client to call the endpoint
                    router_response = self.router_app_routes["/campaigns/"](
                        router_format, token)

                    # Convert router response to standardized format
                    standard_response = self.model_adapter.router_to_standard(router_response)

                    # Convert to fixed format
                    fixed_response = self.model_adapter.standard_to_fixed(standard_response)

                    # Return standardized response
                    return self.response_adapter.standardize_response(fixed_response)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for unified authentication."""

    def __init__(self, app: ASGIApp, auth_adapter: AuthAdapter):
        """Initialize the middleware.

        Args:
            app: ASGI app
            auth_adapter: Authentication adapter
        """
        super().__init__(app)
        self.auth_adapter = auth_adapter

    async def dispatch(self, request: Request, call_next):
        """Process the request.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Verify authentication
        user = await self.auth_adapter.verify_authentication(request)

        # If authentication is valid, continue
        if user:
            # Set user in request state
            request.state.user = user
            return await call_next(request)

        # Otherwise, return 401 Unauthorized
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid authentication credentials"}
        )


# Function to setup the adapter
def setup_api_adapter(app: FastAPI):
    """Setup API adapter.

    Args:
        app: FastAPI app
    """
    # Initialize adapters
    auth_adapter = AuthAdapter()
    model_adapter = ModelAdapter()
    response_adapter = ResponseAdapter()

    # Create middleware
    app.add_middleware(
        BaseHTTPMiddleware,
        dispatch=AuthMiddleware(app, auth_adapter).dispatch
    )

    # Initialize endpoint adapter
    endpoint_adapter = EndpointAdapter(
        app=app,
        auth_adapter=auth_adapter,
        model_adapter=model_adapter,
        response_adapter=response_adapter
    )

    # Add fixed to router adapters
    endpoint_adapter.add_fixed_to_router_adapter("/create_campaign")

    # Add router to fixed adapters
    endpoint_adapter.add_router_to_fixed_adapter("/campaigns/")
    endpoint_adapter.add_router_to_fixed_adapter("/campaigns/{campaign_id}")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return endpoint_adapter


# Example usage
if __name__ == "__main__":
    from fastapi import FastAPI

    app = FastAPI(title="API Adapter Example")

    # Setup API adapter
    adapter = setup_api_adapter(app)

    # Run the app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
