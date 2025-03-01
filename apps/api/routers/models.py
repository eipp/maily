"""Model management routes for the Maily API.

This module provides routes for interacting with AI models, including
model selection, inference, and configuration.
"""

import os
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from pydantic import BaseModel
from typing import List, Optional

from ..ai.config import OCTOTOOLS_CONFIG
from ..services import cipher_suite, get_db_connection
from ..services.user_service import get_current_user
from .schemas import BaseResponse

router = APIRouter()


class ConfigRequest(BaseModel):
    """Schema for model configuration requests.

    Attributes:
        model_name: Name of the model to configure
        api_key: API key for the model
        provider: Provider of the model (e.g., openai, anthropic)
    """

    model_name: str
    api_key: str
    provider: str


class SupportedModelsResponse(BaseModel):
    """Response schema for supported models."""

    providers: List[str]
    models: dict


@router.get("/supported_models", tags=["Models"], summary="Get supported models")
async def get_supported_models():
    """Get a list of supported models.

    Returns:
        SupportedModelsResponse: Response containing supported models
    """
    try:
        # In a real implementation, this would be dynamically generated
        # based on the OctoTools configuration
        supported_providers = ["openai", "anthropic", "google"]
        supported_models = {
            "openai": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "google": ["gemini-pro", "gemini-ultra"]
        }

        return SupportedModelsResponse(
            providers=supported_providers,
            models=supported_models
        )
    except Exception as e:
        logger.error(f"Failed to get supported models: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/configure_model", tags=["Models"], summary="Configure AI model")
async def configure_model(config: ConfigRequest, current_user = Depends(get_current_user)):
    """Configure an AI model.

    This endpoint allows you to configure an AI model by providing its name, provider, and API key.

    Args:
        config: Configuration details for the model
        current_user: Current authenticated user

    Returns:
        BaseResponse: Response indicating the success of the configuration
    """
    try:
        # Validate provider and model
        supported_providers = ["openai", "anthropic", "google", "resend", "sendgrid", "mailgun"]

        if config.provider not in supported_providers:
            raise HTTPException(
                status_code=400, detail=f"Provider {config.provider} not supported"
            )

        # Encrypt API key
        encrypted_key = cipher_suite.encrypt(config.api_key.encode()).decode()

        # Save to database
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO user_configs (user_id, provider, model_name, api_key)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, provider) DO UPDATE
            SET model_name = EXCLUDED.model_name, api_key = EXCLUDED.api_key
        """,
            (current_user.id, config.provider, config.model_name, encrypted_key),
        )

        conn.commit()
        cur.close()
        conn.close()

        # Update environment variable for the current session
        # Note: This is just for the current process, not persistent across restarts
        if config.provider in OCTOTOOLS_CONFIG["api_keys"]:
            os.environ[f"{config.provider.upper()}_API_KEY"] = config.api_key

        return BaseResponse(status="success")
    except Exception as e:
        logger.error(f"Failed to configure model: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
