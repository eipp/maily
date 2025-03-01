"""
CDN Manager for Maily.

This module provides utilities for working with CDN for static assets,
including URL generation and cache invalidation.
"""
import json
import logging
import os
import time
import hashlib
import re
from typing import Dict, Any, Optional, List, Set
from urllib.parse import urljoin, urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

# CDN configuration
CDN_ENABLED = os.environ.get("CDN_ENABLED", "true").lower() == "true"
CDN_PROVIDER = os.environ.get("CDN_PROVIDER", "cloudfront")
CDN_MAIN_DOMAIN = os.environ.get("CDN_MAIN_DOMAIN", "assets.maily.app")
CDN_ASSETS_DOMAIN = os.environ.get("CDN_ASSETS_DOMAIN", "static.maily.app")
CDN_IMAGES_DOMAIN = os.environ.get("CDN_IMAGES_DOMAIN", "images.maily.app")

# CDN paths
STATIC_PATH = "/static"
IMAGES_PATH = "/images"
TEMPLATES_PATH = "/templates"
USER_UPLOADS_PATH = "/uploads"

# Cache-Control headers for different asset types
CACHE_CONTROL = {
    "static": "public, max-age=86400",  # 24 hours
    "images": "public, max-age=604800",  # 1 week
    "templates": "public, max-age=3600",  # 1 hour
    "user_uploads": "public, max-age=7200",  # 2 hours
}

class CDNManager:
    """
    Manager for CDN operations.

    Features:
    - CDN URL generation for different asset types
    - Cache invalidation for updated assets
    - Configurable cache control for different asset types
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(CDNManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the CDN manager."""
        if self._initialized:
            return

        self._initialized = True
        self.enabled = CDN_ENABLED
        self.provider = CDN_PROVIDER
        self.main_domain = CDN_MAIN_DOMAIN
        self.assets_domain = CDN_ASSETS_DOMAIN
        self.images_domain = CDN_IMAGES_DOMAIN

        # Internal tracking of invalidation requests
        self._invalidation_batch: Set[str] = set()
        self._last_invalidation_time = 0

        # Provider-specific clients
        self._provider_client = self._create_provider_client()

        logger.info(f"CDN Manager initialized with provider: {self.provider}")

    def _create_provider_client(self) -> Any:
        """Create a client for the CDN provider."""
        if not self.enabled:
            return None

        if self.provider == "cloudfront":
            try:
                import boto3
                return boto3.client('cloudfront')
            except (ImportError, Exception) as e:
                logger.error(f"Failed to create CloudFront client: {e}")
                return None
        elif self.provider == "fastly":
            try:
                # Fastly API client would be initialized here
                pass
            except Exception as e:
                logger.error(f"Failed to create Fastly client: {e}")
                return None
        elif self.provider == "cloudflare":
            try:
                # Cloudflare API client would be initialized here
                pass
            except Exception as e:
                logger.error(f"Failed to create Cloudflare client: {e}")
                return None
        else:
            logger.warning(f"Unsupported CDN provider: {self.provider}")
            return None

    def get_static_url(self, path: str) -> str:
        """
        Get CDN URL for a static asset.

        Args:
            path: Path to the static asset

        Returns:
            CDN URL for the asset
        """
        if not self.enabled:
            # Return the local path if CDN is disabled
            return path

        # Remove leading slash if present
        if path.startswith("/"):
            path = path[1:]

        # Add cache buster parameter if the path doesn't already have one
        if not re.search(r'[?&]v=', path):
            # Calculate hash of the file for cache busting
            # In a real implementation, you might want to use a file hash or version timestamp
            cache_buster = int(time.time() / 3600)  # Change every hour

            # Add cache buster parameter
            if "?" in path:
                path += f"&v={cache_buster}"
            else:
                path += f"?v={cache_buster}"

        # Construct the full URL with the CDN domain
        return f"https://{self.assets_domain}{STATIC_PATH}/{path}"

    def get_image_url(self, path: str, width: Optional[int] = None, height: Optional[int] = None, format: Optional[str] = None) -> str:
        """
        Get CDN URL for an image with optional resizing.

        Args:
            path: Path to the image
            width: Optional width for resizing
            height: Optional height for resizing
            format: Optional format conversion (e.g., webp, jpeg)

        Returns:
            CDN URL for the image
        """
        if not self.enabled:
            # Return the local path if CDN is disabled
            return path

        # Remove leading slash if present
        if path.startswith("/"):
            path = path[1:]

        # Construct the transformation parameters
        transform_params = []
        if width:
            transform_params.append(f"width={width}")
        if height:
            transform_params.append(f"height={height}")
        if format:
            transform_params.append(f"format={format}")

        # Add transformation parameters to the URL
        transform_string = ""
        if transform_params:
            transform_string = "?" + "&".join(transform_params)

        # Construct the full URL with the CDN domain
        return f"https://{self.images_domain}{IMAGES_PATH}/{path}{transform_string}"

    def get_template_url(self, template_id: int) -> str:
        """
        Get CDN URL for an email template.

        Args:
            template_id: ID of the template

        Returns:
            CDN URL for the template
        """
        if not self.enabled:
            # Return a local URL if CDN is disabled
            return f"/api/templates/{template_id}"

        # Construct the full URL with the CDN domain
        return f"https://{self.main_domain}{TEMPLATES_PATH}/{template_id}"

    def get_upload_url(self, user_id: int, filename: str) -> str:
        """
        Get CDN URL for a user upload.

        Args:
            user_id: ID of the user
            filename: Name of the uploaded file

        Returns:
            CDN URL for the uploaded file
        """
        if not self.enabled:
            # Return a local URL if CDN is disabled
            return f"/api/uploads/{user_id}/{filename}"

        # Create a user-specific path
        upload_path = f"{user_id}/{filename}"

        # Construct the full URL with the CDN domain
        return f"https://{self.main_domain}{USER_UPLOADS_PATH}/{upload_path}"

    def invalidate(self, paths: List[str], wait: bool = False) -> bool:
        """
        Invalidate CDN cache for specified paths.

        Args:
            paths: List of paths to invalidate
            wait: Whether to wait for the invalidation to complete

        Returns:
            True if invalidation was successful, False otherwise
        """
        if not self.enabled or not self._provider_client:
            return True  # No-op if CDN is disabled or client isn't available

        try:
            # Add paths to the batch
            self._invalidation_batch.update(paths)

            # Check if we should send the batch now
            current_time = time.time()
            should_send = len(self._invalidation_batch) >= 100 or current_time - self._last_invalidation_time > 300

            if not should_send:
                logger.debug(f"Added {len(paths)} paths to invalidation batch (total: {len(self._invalidation_batch)})")
                return True

            # Send invalidation batch
            paths_to_send = list(self._invalidation_batch)
            self._invalidation_batch.clear()
            self._last_invalidation_time = current_time

            return self._send_invalidation(paths_to_send, wait)
        except Exception as e:
            logger.error(f"Error invalidating CDN cache: {e}")
            return False

    def _send_invalidation(self, paths: List[str], wait: bool = False) -> bool:
        """
        Send invalidation request to the CDN provider.

        Args:
            paths: List of paths to invalidate
            wait: Whether to wait for the invalidation to complete

        Returns:
            True if invalidation was successful, False otherwise
        """
        try:
            logger.info(f"Sending invalidation request for {len(paths)} paths to {self.provider}")

            if self.provider == "cloudfront":
                # CloudFront invalidation
                if not self._provider_client:
                    return False

                # Get distribution ID from environment variable
                distribution_id = os.environ.get("CLOUDFRONT_DISTRIBUTION_ID")
                if not distribution_id:
                    logger.error("CloudFront distribution ID not configured")
                    return False

                # Create invalidation
                response = self._provider_client.create_invalidation(
                    DistributionId=distribution_id,
                    InvalidationBatch={
                        'Paths': {
                            'Quantity': len(paths),
                            'Items': paths
                        },
                        'CallerReference': str(int(time.time()))
                    }
                )

                invalidation_id = response.get('Invalidation', {}).get('Id')

                if not invalidation_id:
                    logger.error("Failed to get invalidation ID from response")
                    return False

                logger.info(f"Invalidation created with ID: {invalidation_id}")

                # Wait for invalidation to complete if requested
                if wait:
                    logger.info(f"Waiting for invalidation {invalidation_id} to complete...")
                    waiter = self._provider_client.get_waiter('invalidation_completed')
                    waiter.wait(
                        DistributionId=distribution_id,
                        Id=invalidation_id
                    )
                    logger.info(f"Invalidation {invalidation_id} completed")

                return True
            elif self.provider == "fastly":
                # Fastly invalidation would be implemented here
                logger.warning("Fastly invalidation not implemented")
                return False
            elif self.provider == "cloudflare":
                # Cloudflare invalidation would be implemented here
                logger.warning("Cloudflare invalidation not implemented")
                return False
            else:
                logger.warning(f"Invalidation not supported for provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"Error sending invalidation request: {e}")
            return False

    def get_cache_control(self, asset_type: str) -> str:
        """
        Get Cache-Control header for a specific asset type.

        Args:
            asset_type: Type of asset (static, images, templates, user_uploads)

        Returns:
            Cache-Control header value
        """
        return CACHE_CONTROL.get(asset_type, CACHE_CONTROL["static"])

# Create a singleton instance
cdn_manager = CDNManager()

# Helper functions for common operations
def get_static_url(path: str) -> str:
    """
    Get CDN URL for a static asset.

    Args:
        path: Path to the static asset

    Returns:
        CDN URL for the asset
    """
    return cdn_manager.get_static_url(path)

def get_image_url(path: str, width: Optional[int] = None, height: Optional[int] = None, format: Optional[str] = None) -> str:
    """
    Get CDN URL for an image with optional resizing.

    Args:
        path: Path to the image
        width: Optional width for resizing
        height: Optional height for resizing
        format: Optional format conversion (e.g., webp, jpeg)

    Returns:
        CDN URL for the image
    """
    return cdn_manager.get_image_url(path, width, height, format)

def get_template_url(template_id: int) -> str:
    """
    Get CDN URL for an email template.

    Args:
        template_id: ID of the template

    Returns:
        CDN URL for the template
    """
    return cdn_manager.get_template_url(template_id)

def get_upload_url(user_id: int, filename: str) -> str:
    """
    Get CDN URL for a user upload.

    Args:
        user_id: ID of the user
        filename: Name of the uploaded file

    Returns:
        CDN URL for the uploaded file
    """
    return cdn_manager.get_upload_url(user_id, filename)

def invalidate_paths(paths: List[str], wait: bool = False) -> bool:
    """
    Invalidate CDN cache for specified paths.

    Args:
        paths: List of paths to invalidate
        wait: Whether to wait for the invalidation to complete

    Returns:
        True if invalidation was successful, False otherwise
    """
    return cdn_manager.invalidate(paths, wait)
