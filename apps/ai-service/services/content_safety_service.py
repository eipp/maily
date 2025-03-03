"""
Content Safety Service for AI-generated content.

This module provides content filtering, toxicity detection, and content moderation
workflows for all AI-generated content in the platform.
"""

import os
import json
import time
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Union, Any

import httpx
from fastapi import HTTPException, status

from ai_service.utils.logger import get_logger
from ai_service.utils.retry import retry_with_backoff
from ai_service.models.content_safety import (
    ContentSafetyCheck,
    ContentSafetyResult,
    ContentSafetyCategory,
    ContentSafetyLevel,
    ContentSafetyAction,
)
from ai_service.utils.database import get_session

# Configure logging
logger = get_logger(__name__)

# Environment variables
CONTENT_SAFETY_API_KEY = os.getenv("CONTENT_SAFETY_API_KEY", "")
CONTENT_SAFETY_ENDPOINT = os.getenv("CONTENT_SAFETY_ENDPOINT", "https://api.contentsafety.example.com/v1/analyze")
CONTENT_SAFETY_TIMEOUT = int(os.getenv("CONTENT_SAFETY_TIMEOUT", "5"))  # seconds
CONTENT_SAFETY_ENABLED = os.getenv("CONTENT_SAFETY_ENABLED", "true").lower() == "true"
CONTENT_SAFETY_THRESHOLD = float(os.getenv("CONTENT_SAFETY_THRESHOLD", "0.7"))  # 0.0 to 1.0
CONTENT_SAFETY_CACHE_TTL = int(os.getenv("CONTENT_SAFETY_CACHE_TTL", "3600"))  # 1 hour

# In-memory cache for content safety results
# This is a simple cache that will be cleared when the service restarts
# For production, consider using Redis or another distributed cache
_content_safety_cache: Dict[str, Tuple[ContentSafetyResult, float]] = {}

class ContentSafetyService:
    """
    Service for content safety checks and moderation.
    
    This service provides methods for checking content safety, filtering unsafe content,
    and implementing content moderation workflows.
    """
    
    def __init__(self):
        """Initialize the content safety service."""
        self.api_key = CONTENT_SAFETY_API_KEY
        self.endpoint = CONTENT_SAFETY_ENDPOINT
        self.timeout = CONTENT_SAFETY_TIMEOUT
        self.enabled = CONTENT_SAFETY_ENABLED
        self.threshold = CONTENT_SAFETY_THRESHOLD
        self.cache_ttl = CONTENT_SAFETY_CACHE_TTL
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(timeout=self.timeout)
        
        logger.info(f"Content Safety Service initialized (enabled={self.enabled})")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _get_content_hash(self, content: str) -> str:
        """
        Generate a hash for the content to use as a cache key.
        
        Args:
            content (str): The content to hash
            
        Returns:
            str: SHA-256 hash of the content
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def _get_cached_result(self, content_hash: str) -> Optional[ContentSafetyResult]:
        """
        Get a cached content safety result if available and not expired.
        
        Args:
            content_hash (str): The content hash to look up
            
        Returns:
            Optional[ContentSafetyResult]: The cached result or None if not found or expired
        """
        if content_hash in _content_safety_cache:
            result, timestamp = _content_safety_cache[content_hash]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for content hash {content_hash}")
                return result
            else:
                logger.debug(f"Cache expired for content hash {content_hash}")
                del _content_safety_cache[content_hash]
        
        return None
    
    def _cache_result(self, content_hash: str, result: ContentSafetyResult):
        """
        Cache a content safety result.
        
        Args:
            content_hash (str): The content hash to use as a key
            result (ContentSafetyResult): The result to cache
        """
        _content_safety_cache[content_hash] = (result, time.time())
        logger.debug(f"Cached result for content hash {content_hash}")
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    async def _call_content_safety_api(self, content: str) -> Dict[str, Any]:
        """
        Call the content safety API to analyze content.
        
        Args:
            content (str): The content to analyze
            
        Returns:
            Dict[str, Any]: The API response
            
        Raises:
            HTTPException: If the API call fails
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            
            payload = {
                "text": content,
                "categories": [
                    "hate",
                    "harassment",
                    "self_harm",
                    "sexual",
                    "violence",
                    "child_abuse",
                    "terrorism",
                ],
                "threshold": self.threshold,
            }
            
            response = await self.client.post(
                self.endpoint,
                headers=headers,
                json=payload,
            )
            
            if response.status_code != 200:
                logger.error(f"Content safety API error: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Content safety check failed",
                )
            
            return response.json()
        
        except httpx.RequestError as e:
            logger.error(f"Content safety API request error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Content safety check failed",
            )
    
    def _parse_api_response(self, response: Dict[str, Any]) -> ContentSafetyResult:
        """
        Parse the content safety API response into a ContentSafetyResult.
        
        Args:
            response (Dict[str, Any]): The API response
            
        Returns:
            ContentSafetyResult: The parsed result
        """
        categories = []
        
        # Extract categories from the response
        for category_name, category_data in response.get("categories", {}).items():
            category = ContentSafetyCategory(
                name=category_name,
                score=category_data.get("score", 0.0),
                flagged=category_data.get("flagged", False),
            )
            categories.append(category)
        
        # Determine overall safety level
        if any(c.flagged for c in categories):
            if any(c.score > 0.9 for c in categories):
                safety_level = ContentSafetyLevel.HIGH_RISK
            else:
                safety_level = ContentSafetyLevel.MEDIUM_RISK
        else:
            safety_level = ContentSafetyLevel.SAFE
        
        # Determine recommended action
        if safety_level == ContentSafetyLevel.HIGH_RISK:
            action = ContentSafetyAction.BLOCK
        elif safety_level == ContentSafetyLevel.MEDIUM_RISK:
            action = ContentSafetyAction.FLAG_FOR_REVIEW
        else:
            action = ContentSafetyAction.ALLOW
        
        return ContentSafetyResult(
            id=response.get("id", ""),
            timestamp=response.get("timestamp", time.time()),
            content_hash=response.get("content_hash", ""),
            safety_level=safety_level,
            categories=categories,
            recommended_action=action,
        )
    
    async def check_content_safety(self, content: str) -> ContentSafetyResult:
        """
        Check content for safety issues.
        
        This method analyzes the provided content for safety issues such as
        hate speech, harassment, self-harm, sexual content, violence, etc.
        It returns a ContentSafetyResult with details about any detected issues.
        
        Args:
            content (str): The content to check
            
        Returns:
            ContentSafetyResult: The safety check result
            
        Raises:
            HTTPException: If the safety check fails
        """
        # If content safety is disabled, return a safe result
        if not self.enabled:
            logger.warning("Content safety checks are disabled")
            return ContentSafetyResult(
                id="disabled",
                timestamp=time.time(),
                content_hash="",
                safety_level=ContentSafetyLevel.SAFE,
                categories=[],
                recommended_action=ContentSafetyAction.ALLOW,
            )
        
        # Generate content hash for caching
        content_hash = self._get_content_hash(content)
        
        # Check cache first
        cached_result = self._get_cached_result(content_hash)
        if cached_result:
            return cached_result
        
        # Call the content safety API
        api_response = await self._call_content_safety_api(content)
        
        # Parse the response
        result = self._parse_api_response(api_response)
        result.content_hash = content_hash
        
        # Cache the result
        self._cache_result(content_hash, result)
        
        # Log the result
        if result.safety_level != ContentSafetyLevel.SAFE:
            logger.warning(
                f"Content safety issues detected: {result.safety_level.value}, "
                f"action: {result.recommended_action.value}"
            )
        
        # Store the check in the database
        await self._store_safety_check(content, result)
        
        return result
    
    async def filter_content(self, content: str) -> Tuple[str, ContentSafetyResult]:
        """
        Filter content for safety issues.
        
        This method checks the content for safety issues and, if issues are found,
        filters or modifies the content to remove or reduce the problematic parts.
        
        Args:
            content (str): The content to filter
            
        Returns:
            Tuple[str, ContentSafetyResult]: The filtered content and safety result
            
        Raises:
            HTTPException: If the content filtering fails
        """
        # Check content safety
        result = await self.check_content_safety(content)
        
        # If content is safe, return it unchanged
        if result.safety_level == ContentSafetyLevel.SAFE:
            return content, result
        
        # If content is high risk, replace it with a message
        if result.safety_level == ContentSafetyLevel.HIGH_RISK:
            return (
                "[Content removed due to safety concerns]",
                result,
            )
        
        # If content is medium risk, try to filter it
        # This is a simple implementation - in a real system, you would use
        # more sophisticated filtering techniques
        filtered_content = content
        for category in result.categories:
            if category.flagged:
                # Add a warning message
                filtered_content = (
                    f"[Warning: This content may contain {category.name} content]\n\n"
                    f"{filtered_content}"
                )
        
        return filtered_content, result
    
    async def _store_safety_check(self, content: str, result: ContentSafetyResult):
        """
        Store a content safety check in the database.
        
        Args:
            content (str): The content that was checked
            result (ContentSafetyResult): The safety check result
        """
        try:
            # Create a new ContentSafetyCheck record
            check = ContentSafetyCheck(
                content_hash=result.content_hash,
                content_snippet=content[:100] + "..." if len(content) > 100 else content,
                safety_level=result.safety_level.value,
                categories=json.dumps([c.dict() for c in result.categories]),
                action_taken=result.recommended_action.value,
                timestamp=result.timestamp,
            )
            
            # Store in database
            async with get_session() as session:
                session.add(check)
                await session.commit()
            
            logger.debug(f"Stored content safety check: {check.id}")
        
        except Exception as e:
            logger.error(f"Error storing content safety check: {str(e)}")
    
    async def get_safety_checks(
        self,
        limit: int = 100,
        offset: int = 0,
        safety_level: Optional[str] = None,
    ) -> List[ContentSafetyCheck]:
        """
        Get content safety checks from the database.
        
        Args:
            limit (int): Maximum number of checks to return
            offset (int): Offset for pagination
            safety_level (Optional[str]): Filter by safety level
            
        Returns:
            List[ContentSafetyCheck]: List of content safety checks
        """
        try:
            async with get_session() as session:
                query = session.query(ContentSafetyCheck)
                
                if safety_level:
                    query = query.filter(ContentSafetyCheck.safety_level == safety_level)
                
                query = query.order_by(ContentSafetyCheck.timestamp.desc())
                query = query.limit(limit).offset(offset)
                
                return await query.all()
        
        except Exception as e:
            logger.error(f"Error getting content safety checks: {str(e)}")
            return []
    
    async def get_safety_stats(self) -> Dict[str, Any]:
        """
        Get content safety statistics.
        
        Returns:
            Dict[str, Any]: Statistics about content safety checks
        """
        try:
            async with get_session() as session:
                # Total checks
                total_checks = await session.query(ContentSafetyCheck).count()
                
                # Checks by safety level
                safe_checks = await session.query(ContentSafetyCheck).filter(
                    ContentSafetyCheck.safety_level == ContentSafetyLevel.SAFE.value
                ).count()
                
                medium_risk_checks = await session.query(ContentSafetyCheck).filter(
                    ContentSafetyCheck.safety_level == ContentSafetyLevel.MEDIUM_RISK.value
                ).count()
                
                high_risk_checks = await session.query(ContentSafetyCheck).filter(
                    ContentSafetyCheck.safety_level == ContentSafetyLevel.HIGH_RISK.value
                ).count()
                
                # Checks by action taken
                allow_actions = await session.query(ContentSafetyCheck).filter(
                    ContentSafetyCheck.action_taken == ContentSafetyAction.ALLOW.value
                ).count()
                
                flag_actions = await session.query(ContentSafetyCheck).filter(
                    ContentSafetyCheck.action_taken == ContentSafetyAction.FLAG_FOR_REVIEW.value
                ).count()
                
                block_actions = await session.query(ContentSafetyCheck).filter(
                    ContentSafetyCheck.action_taken == ContentSafetyAction.BLOCK.value
                ).count()
                
                return {
                    "total_checks": total_checks,
                    "safety_levels": {
                        "safe": safe_checks,
                        "medium_risk": medium_risk_checks,
                        "high_risk": high_risk_checks,
                    },
                    "actions_taken": {
                        "allow": allow_actions,
                        "flag_for_review": flag_actions,
                        "block": block_actions,
                    },
                }
        
        except Exception as e:
            logger.error(f"Error getting content safety stats: {str(e)}")
            return {
                "total_checks": 0,
                "safety_levels": {
                    "safe": 0,
                    "medium_risk": 0,
                    "high_risk": 0,
                },
                "actions_taken": {
                    "allow": 0,
                    "flag_for_review": 0,
                    "block": 0,
                },
            }

# Create a singleton instance
content_safety_service = ContentSafetyService()
