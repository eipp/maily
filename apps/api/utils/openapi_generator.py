"""
OpenAPI 3.1 documentation generator for the API service.

This module provides utilities for generating OpenAPI 3.1 documentation for the API service.
"""

import inspect
import logging
import re
from typing import Any, Dict, List, Optional, Set, Type, Union, get_type_hints
from enum import Enum

from fastapi import APIRouter, Depends, FastAPI, Path, Query, Body, Header, Cookie, Form, File, UploadFile
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field, create_model

logger = logging.getLogger(__name__)

class OpenAPIGenerator:
    """
    OpenAPI 3.1 documentation generator for the API service.
    
    This class provides methods for generating OpenAPI 3.1 documentation for the API service.
    """
    
    def __init__(self, app: FastAPI):
        """
        Initialize the OpenAPI generator.
        
        Args:
            app: The FastAPI application
        """
        self.app = app
        self.title = app.title
        self.description = app.description
        self.version = app.version
        self.routes = app.routes
        
        # Set of models that have been processed
        self.processed_models: Set[Type[BaseModel]] = set()
        
        # Cache for model schemas
        self.model_schemas: Dict[str, Dict[str, Any]] = {}
    
    def generate_openapi_schema(self) -> Dict[str, Any]:
        """
        Generate the OpenAPI schema for the application.
        
        Returns:
            The OpenAPI schema
        """
        # Start with the basic OpenAPI schema
        openapi_schema = get_openapi(
            title=self.title,
            version=self.version,
            description=self.description,
            routes=self.routes,
            servers=self._get_servers(),
        )
        
        # Update to OpenAPI 3.1
        openapi_schema["openapi"] = "3.1.0"
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = self._get_security_schemes()
        
        # Add examples to request bodies and responses
        self._add_examples(openapi_schema)
        
        # Add additional metadata
        openapi_schema["info"]["contact"] = {
            "name": "API Support",
            "url": "https://maily.example.com/support",
            "email": "api-support@maily.example.com"
        }
        
        openapi_schema["info"]["license"] = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
        
        openapi_schema["info"]["termsOfService"] = "https://maily.example.com/terms"
        
        return openapi_schema
    
    def _get_servers(self) -> List[Dict[str, Any]]:
        """
        Get the servers for the OpenAPI schema.
        
        Returns:
            List of server objects
        """
        return [
            {
                "url": "/",
                "description": "Current server"
            },
            {
                "url": "https://api.maily.example.com",
                "description": "Production server"
            },
            {
                "url": "https://api-staging.maily.example.com",
                "description": "Staging server"
            },
            {
                "url": "https://api-dev.maily.example.com",
                "description": "Development server"
            }
        ]
    
    def _get_security_schemes(self) -> Dict[str, Any]:
        """
        Get the security schemes for the OpenAPI schema.
        
        Returns:
            Dictionary of security schemes
        """
        return {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key authentication"
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT authentication"
            },
            "OAuth2": {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "https://auth.maily.example.com/oauth/authorize",
                        "tokenUrl": "https://auth.maily.example.com/oauth/token",
                        "scopes": {
                            "read": "Read access",
                            "write": "Write access",
                            "admin": "Admin access"
                        }
                    }
                }
            }
        }
    
    def _add_examples(self, openapi_schema: Dict[str, Any]) -> None:
        """
        Add examples to request bodies and responses.
        
        Args:
            openapi_schema: The OpenAPI schema to modify
        """
        paths = openapi_schema.get("paths", {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    # Add examples to request body
                    if "requestBody" in operation:
                        content = operation["requestBody"].get("content", {})
                        for media_type, media_item in content.items():
                            if "schema" in media_item:
                                schema_ref = media_item["schema"].get("$ref")
                                if schema_ref:
                                    schema_name = schema_ref.split("/")[-1]
                                    example = self._generate_example_for_schema(schema_name, openapi_schema)
                                    if example:
                                        media_item["example"] = example
                    
                    # Add examples to responses
                    if "responses" in operation:
                        for status_code, response in operation["responses"].items():
                            content = response.get("content", {})
                            for media_type, media_item in content.items():
                                if "schema" in media_item:
                                    schema_ref = media_item["schema"].get("$ref")
                                    if schema_ref:
                                        schema_name = schema_ref.split("/")[-1]
                                        example = self._generate_example_for_schema(schema_name, openapi_schema)
                                        if example:
                                            media_item["example"] = example
    
    def _generate_example_for_schema(self, schema_name: str, openapi_schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate an example for a schema.
        
        Args:
            schema_name: The name of the schema
            openapi_schema: The OpenAPI schema
            
        Returns:
            An example for the schema, or None if no example could be generated
        """
        schema = openapi_schema.get("components", {}).get("schemas", {}).get(schema_name)
        if not schema:
            return None
        
        example = {}
        
        for prop_name, prop_schema in schema.get("properties", {}).items():
            example[prop_name] = self._generate_example_value(prop_schema)
        
        return example
    
    def _generate_example_value(self, schema: Dict[str, Any]) -> Any:
        """
        Generate an example value for a schema.
        
        Args:
            schema: The schema to generate an example for
            
        Returns:
            An example value for the schema
        """
        if "example" in schema:
            return schema["example"]
        
        schema_type = schema.get("type")
        
        if schema_type == "string":
            format_type = schema.get("format")
            if format_type == "date-time":
                return "2025-03-03T12:00:00Z"
            elif format_type == "date":
                return "2025-03-03"
            elif format_type == "email":
                return "user@example.com"
            elif format_type == "uuid":
                return "123e4567-e89b-12d3-a456-426614174000"
            elif format_type == "uri":
                return "https://example.com"
            elif format_type == "password":
                return "********"
            else:
                return "string"
        
        elif schema_type == "number":
            return 0.0
        
        elif schema_type == "integer":
            return 0
        
        elif schema_type == "boolean":
            return False
        
        elif schema_type == "array":
            items = schema.get("items", {})
            return [self._generate_example_value(items)]
        
        elif schema_type == "object":
            obj = {}
            for prop_name, prop_schema in schema.get("properties", {}).items():
                obj[prop_name] = self._generate_example_value(prop_schema)
            return obj
        
        elif "$ref" in schema:
            # Reference to another schema
            ref = schema["$ref"]
            schema_name = ref.split("/")[-1]
            # This would need to look up the schema in the components section
            # For simplicity, we'll just return a placeholder
            return f"<{schema_name}>"
        
        # Default
        return None


def generate_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate the OpenAPI schema for the application.
    
    Args:
        app: The FastAPI application
        
    Returns:
        The OpenAPI schema
    """
    generator = OpenAPIGenerator(app)
    return generator.generate_openapi_schema()


def setup_openapi_documentation(app: FastAPI) -> None:
    """
    Set up OpenAPI documentation for the application.
    
    Args:
        app: The FastAPI application
    """
    # Override the default OpenAPI schema generator
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        app.openapi_schema = generate_openapi_schema(app)
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    logger.info("OpenAPI 3.1 documentation set up")
