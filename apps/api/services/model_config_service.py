"""
Model Configuration Service

This service provides CRUD operations for managing AI model configurations.
It includes caching, security measures for API key storage, and validation.
"""

import uuid
import time
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from pydantic import ValidationError

from ..database.models import ModelConfig
from ..database.connection import get_cursor, execute_read, execute_write
from ..api.schemas import ModelConfig as ModelConfigSchema
from ..utils.encryption import encrypt_data, decrypt_data
from ..cache.redis_client import get_redis_client
from ..config.settings import settings

# Initialize logging
logger = logging.getLogger(__name__)

# Cache constants
CACHE_TTL = 3600  # 1 hour
CACHE_PREFIX = "model_config:"

class ModelConfigService:
    """Service for managing model configurations"""

    def __init__(self):
        self.redis = get_redis_client()
        self.cache_enabled = settings.CACHE_ENABLED

    async def create_model_config(
        self, 
        model_name: str, 
        provider: str,
        api_key: str, 
        user_id: Optional[int] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        parameters: Optional[Dict[str, Any]] = None,
        is_default: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new model configuration.
        
        Args:
            model_name: Name of the AI model
            provider: Provider of the AI model (e.g., openai, anthropic)
            api_key: API key for the model
            user_id: ID of the user who owns this config (None for global)
            temperature: Temperature setting for generation
            max_tokens: Maximum tokens for generation
            parameters: Additional parameters
            is_default: Whether this is the default config for this model
            
        Returns:
            Created model configuration
        """
        try:
            # Generate a unique ID for the config
            config_id = f"config_{uuid.uuid4().hex[:8]}_{int(time.time())}"
            
            # Encrypt the API key before storing
            encrypted_api_key = encrypt_data(api_key)
            
            # Handle default model logic
            if is_default:
                # If setting as default, unset any existing defaults for this model/provider/user combo
                await self._unset_existing_defaults(model_name, provider, user_id)
            
            # Prepare the INSERT query
            query = """
            INSERT INTO model_configs (
                id, user_id, model_name, provider, api_key, 
                temperature, max_tokens, parameters, 
                is_active, is_default, created_at, updated_at
            ) VALUES (
                %(id)s, %(user_id)s, %(model_name)s, %(provider)s, %(api_key)s,
                %(temperature)s, %(max_tokens)s, %(parameters)s,
                %(is_active)s, %(is_default)s, %(created_at)s, %(updated_at)s
            ) RETURNING id, model_name, provider, temperature, max_tokens, is_default, created_at
            """
            
            now = datetime.utcnow()
            params = {
                "id": config_id,
                "user_id": user_id,
                "model_name": model_name,
                "provider": provider,
                "api_key": encrypted_api_key,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "parameters": json.dumps(parameters) if parameters else "{}",
                "is_active": True,
                "is_default": is_default,
                "created_at": now,
                "updated_at": now
            }
            
            # Execute the query
            with get_cursor(for_write=True) as cursor:
                cursor.execute(query, params)
                result = dict(cursor.fetchone())
            
            # Add to cache
            if self.cache_enabled:
                cache_key = f"{CACHE_PREFIX}{config_id}"
                await self.redis.set(cache_key, json.dumps(result), expire=CACHE_TTL)
                
                # Update model list cache
                await self._invalidate_model_list_cache(user_id)
            
            logger.info(f"Created model config: {config_id} for model {model_name} (provider: {provider})")
            return result
            
        except Exception as e:
            logger.error(f"Error creating model config: {str(e)}")
            raise
    
    async def _unset_existing_defaults(self, model_name: str, provider: str, user_id: Optional[int]) -> None:
        """
        Unset any existing default configs for this model/provider/user combo.
        
        Args:
            model_name: Model name
            provider: Provider name
            user_id: User ID (None for global)
        """
        try:
            # Prepare query to unset defaults
            query = """
            UPDATE model_configs
            SET is_default = FALSE, updated_at = %(now)s
            WHERE model_name = %(model_name)s 
            AND provider = %(provider)s
            """
            
            # Add user ID condition if provided
            if user_id is not None:
                query += " AND user_id = %(user_id)s"
            else:
                query += " AND user_id IS NULL"
                
            params = {
                "model_name": model_name,
                "provider": provider,
                "user_id": user_id,
                "now": datetime.utcnow()
            }
            
            # Execute the query
            execute_write(query, params)
            
            # Invalidate cache for affected configs
            if self.cache_enabled:
                await self._invalidate_model_list_cache(user_id)
                
        except Exception as e:
            logger.error(f"Error unsetting existing defaults: {str(e)}")
            raise
    
    async def get_model_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a model configuration by ID.
        
        Args:
            config_id: ID of the configuration
            
        Returns:
            Model configuration or None if not found
        """
        try:
            # Check cache first
            if self.cache_enabled:
                cache_key = f"{CACHE_PREFIX}{config_id}"
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            
            # If not in cache, query the database
            query = """
            SELECT 
                id, user_id, model_name, provider, api_key, 
                temperature, max_tokens, parameters, 
                is_active, is_default, created_at, updated_at, last_used_at, usage_count
            FROM model_configs
            WHERE id = %(config_id)s
            """
            
            params = {"config_id": config_id}
            
            # Execute the query
            results = execute_read(query, params)
            
            if not results:
                return None
                
            config = dict(results[0])
            
            # Decrypt API key if requested
            if "api_key" in config:
                config["api_key"] = decrypt_data(config["api_key"])
            
            # Add to cache
            if self.cache_enabled:
                # Don't cache the decrypted API key
                cache_config = config.copy()
                cache_config.pop("api_key", None)
                
                cache_key = f"{CACHE_PREFIX}{config_id}"
                await self.redis.set(cache_key, json.dumps(cache_config), expire=CACHE_TTL)
            
            return config
            
        except Exception as e:
            logger.error(f"Error getting model config {config_id}: {str(e)}")
            raise
    
    async def update_model_config(
        self, 
        config_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a model configuration.
        
        Args:
            config_id: ID of the configuration to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated model configuration or None if not found
        """
        try:
            # Get current config to check if it exists
            current_config = await self.get_model_config(config_id)
            if not current_config:
                return None
            
            # Build the SET clause for the UPDATE query
            set_clauses = []
            params = {"config_id": config_id, "updated_at": datetime.utcnow()}
            
            for field, value in updates.items():
                if field in ["id", "created_at"]:
                    # Skip immutable fields
                    continue
                    
                if field == "api_key" and value:
                    # Encrypt API key
                    value = encrypt_data(value)
                
                if field == "parameters" and isinstance(value, dict):
                    # Convert parameters dict to JSON string
                    value = json.dumps(value)
                
                set_clauses.append(f"{field} = %({field})s")
                params[field] = value
            
            # Handle case where is_default is being set to True
            if updates.get("is_default") is True:
                await self._unset_existing_defaults(
                    current_config["model_name"], 
                    current_config["provider"], 
                    current_config.get("user_id")
                )
            
            # Add updated_at to SET clause
            set_clauses.append("updated_at = %(updated_at)s")
            
            if not set_clauses:
                # No valid fields to update
                return current_config
            
            # Prepare the UPDATE query
            query = f"""
            UPDATE model_configs
            SET {", ".join(set_clauses)}
            WHERE id = %(config_id)s
            RETURNING id, user_id, model_name, provider, temperature, max_tokens, 
                      parameters, is_active, is_default, created_at, updated_at, 
                      last_used_at, usage_count
            """
            
            # Execute the query
            with get_cursor(for_write=True) as cursor:
                cursor.execute(query, params)
                if cursor.rowcount == 0:
                    return None
                updated_config = dict(cursor.fetchone())
            
            # Update cache
            if self.cache_enabled:
                cache_key = f"{CACHE_PREFIX}{config_id}"
                await self.redis.set(cache_key, json.dumps(updated_config), expire=CACHE_TTL)
                
                # Invalidate model list cache
                await self._invalidate_model_list_cache(current_config.get("user_id"))
            
            logger.info(f"Updated model config: {config_id}")
            return updated_config
            
        except Exception as e:
            logger.error(f"Error updating model config {config_id}: {str(e)}")
            raise
    
    async def delete_model_config(self, config_id: str) -> bool:
        """
        Delete a model configuration.
        
        Args:
            config_id: ID of the configuration to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Get the config first to get user_id for cache invalidation
            config = await self.get_model_config(config_id)
            if not config:
                return False
            
            # Prepare the DELETE query
            query = "DELETE FROM model_configs WHERE id = %(config_id)s"
            params = {"config_id": config_id}
            
            # Execute the query
            rows_deleted = execute_write(query, params)
            
            if rows_deleted == 0:
                return False
            
            # Remove from cache
            if self.cache_enabled:
                cache_key = f"{CACHE_PREFIX}{config_id}"
                await self.redis.delete(cache_key)
                
                # Invalidate model list cache
                await self._invalidate_model_list_cache(config.get("user_id"))
            
            logger.info(f"Deleted model config: {config_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting model config {config_id}: {str(e)}")
            raise
    
    async def list_model_configs(
        self, 
        user_id: Optional[int] = None, 
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List model configurations with optional filtering.
        
        Args:
            user_id: Filter by user ID (None for global)
            model_name: Filter by model name
            provider: Filter by provider
            active_only: Only return active configurations
            
        Returns:
            List of model configurations
        """
        try:
            # Check cache for the list
            if self.cache_enabled:
                cache_key = self._get_model_list_cache_key(user_id, model_name, provider, active_only)
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            
            # Build the query with appropriate filters
            query = """
            SELECT 
                id, user_id, model_name, provider, 
                temperature, max_tokens, parameters, 
                is_active, is_default, created_at, updated_at, last_used_at, usage_count
            FROM model_configs
            WHERE 1=1
            """
            
            params = {}
            
            # Add filters
            if user_id is not None:
                query += " AND (user_id = %(user_id)s OR user_id IS NULL)"
                params["user_id"] = user_id
            
            if model_name:
                query += " AND model_name = %(model_name)s"
                params["model_name"] = model_name
            
            if provider:
                query += " AND provider = %(provider)s"
                params["provider"] = provider
            
            if active_only:
                query += " AND is_active = TRUE"
            
            # Add ordering
            query += """
            ORDER BY is_default DESC, 
                     CASE WHEN user_id IS NULL THEN 0 ELSE 1 END, 
                     updated_at DESC
            """
            
            # Execute the query
            results = execute_read(query, params)
            configs = [dict(row) for row in results]
            
            # Store in cache
            if self.cache_enabled:
                cache_key = self._get_model_list_cache_key(user_id, model_name, provider, active_only)
                await self.redis.set(cache_key, json.dumps(configs), expire=CACHE_TTL)
            
            return configs
            
        except Exception as e:
            logger.error(f"Error listing model configs: {str(e)}")
            raise
    
    async def get_default_model_config(
        self, 
        model_name: str,
        provider: str,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the default model configuration for a specific model and provider.
        
        Args:
            model_name: Model name
            provider: Provider name
            user_id: User ID (None for global)
            
        Returns:
            Default model configuration or None if not found
        """
        try:
            # Try to find a user-specific default first
            query = """
            SELECT 
                id, user_id, model_name, provider, api_key,
                temperature, max_tokens, parameters, 
                is_active, is_default, created_at, updated_at, last_used_at, usage_count
            FROM model_configs
            WHERE model_name = %(model_name)s
            AND provider = %(provider)s
            AND is_active = TRUE
            """
            
            params = {
                "model_name": model_name,
                "provider": provider
            }
            
            if user_id is not None:
                # If user_id provided, look for user configs first, then fall back to global
                query += """
                AND (
                    (user_id = %(user_id)s AND is_default = TRUE)
                    OR
                    (user_id IS NULL AND is_default = TRUE)
                )
                ORDER BY user_id DESC NULLS LAST
                """
                params["user_id"] = user_id
            else:
                # Just look for global default
                query += " AND user_id IS NULL AND is_default = TRUE"
            
            query += " LIMIT 1"
            
            # Execute the query
            results = execute_read(query, params)
            
            if not results:
                return None
                
            config = dict(results[0])
            
            # Decrypt API key
            if "api_key" in config:
                config["api_key"] = decrypt_data(config["api_key"])
            
            return config
            
        except Exception as e:
            logger.error(f"Error getting default model config: {str(e)}")
            raise
    
    async def update_usage_statistics(self, config_id: str) -> bool:
        """
        Update usage statistics for a model configuration.
        
        Args:
            config_id: ID of the configuration
            
        Returns:
            True if updated, False if not found
        """
        try:
            # Prepare the UPDATE query
            query = """
            UPDATE model_configs
            SET 
                usage_count = usage_count + 1,
                last_used_at = %(now)s,
                updated_at = %(now)s
            WHERE id = %(config_id)s
            """
            
            params = {
                "config_id": config_id,
                "now": datetime.utcnow()
            }
            
            # Execute the query
            rows_updated = execute_write(query, params)
            
            if rows_updated == 0:
                return False
            
            # Invalidate cache
            if self.cache_enabled:
                cache_key = f"{CACHE_PREFIX}{config_id}"
                await self.redis.delete(cache_key)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating usage statistics for config {config_id}: {str(e)}")
            raise
    
    def _get_model_list_cache_key(
        self, 
        user_id: Optional[int], 
        model_name: Optional[str],
        provider: Optional[str],
        active_only: bool
    ) -> str:
        """
        Generate a cache key for a model list query.
        
        Args:
            user_id: User ID filter
            model_name: Model name filter
            provider: Provider filter
            active_only: Active only filter
            
        Returns:
            Cache key
        """
        key_parts = ["model_list"]
        
        if user_id is not None:
            key_parts.append(f"user_{user_id}")
        else:
            key_parts.append("all_users")
            
        if model_name:
            key_parts.append(f"model_{model_name}")
            
        if provider:
            key_parts.append(f"provider_{provider}")
            
        if active_only:
            key_parts.append("active_only")
            
        return f"{CACHE_PREFIX}{'_'.join(key_parts)}"
    
    async def _invalidate_model_list_cache(self, user_id: Optional[int] = None) -> None:
        """
        Invalidate model list cache for a specific user or all users.
        
        Args:
            user_id: User ID to invalidate (None for all)
        """
        if not self.cache_enabled:
            return
            
        # Pattern to match all model list cache keys
        if user_id is not None:
            # Just invalidate for this user
            pattern = f"{CACHE_PREFIX}model_list_user_{user_id}_*"
            # Also invalidate all_users cache
            pattern2 = f"{CACHE_PREFIX}model_list_all_users_*"
            keys = await self.redis.keys(pattern)
            keys2 = await self.redis.keys(pattern2)
            keys.extend(keys2)
        else:
            # Invalidate all model list cache keys
            pattern = f"{CACHE_PREFIX}model_list_*"
            keys = await self.redis.keys(pattern)
        
        # Delete all matching keys
        for key in keys:
            await self.redis.delete(key)

# Singleton instance
_instance = None

def get_model_config_service() -> ModelConfigService:
    """Get singleton instance of ModelConfigService"""
    global _instance
    if _instance is None:
        _instance = ModelConfigService()
    return _instance