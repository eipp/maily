"""Base document generator."""

import os
import logging
import shutil
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class BaseGenerator:
    """Base class for document generators."""

    def __init__(self, document_base_path: str, document_base_url: str):
        """Initialize the base generator.

        Args:
            document_base_path: Base path for document storage
            document_base_url: Base URL for document access
        """
        self.document_base_path = document_base_path
        self.document_base_url = document_base_url
        
        # Ensure base directories exist
        self.ensure_directories(document_base_path)
        self.ensure_directories(os.path.join(document_base_path, "previews"))
        self.ensure_directories(os.path.join(document_base_path, "templates"))

    async def generate(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate a document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        raise NotImplementedError("Subclasses must implement generate()")

    def ensure_directories(self, directory_path: str) -> None:
        """Ensure directories exist.

        Args:
            directory_path: Directory path to ensure exists
        """
        os.makedirs(directory_path, exist_ok=True)

    def create_preview_placeholder(self, document_id: str) -> None:
        """Create a placeholder preview image.

        Args:
            document_id: Document ID
        """
        # Create previews directory if it doesn't exist
        previews_dir = os.path.join(self.document_base_path, "previews")
        self.ensure_directories(previews_dir)
        
        # Path to placeholder image
        placeholder_path = os.path.join(os.path.dirname(__file__), "..", "..", "static", "images", "preview_placeholder.png")
        
        # If placeholder exists, copy it
        if os.path.exists(placeholder_path):
            preview_path = os.path.join(previews_dir, f"{document_id}_preview.png")
            shutil.copy(placeholder_path, preview_path)
        else:
            logger.warning(f"Preview placeholder image not found at {placeholder_path}")

    def create_preview(self, file_path: str, document_id: str) -> None:
        """Create a preview image for a document.

        Args:
            file_path: Path to document file
            document_id: Document ID
        """
        # For now, just create a placeholder
        # In a real implementation, this would generate a preview image
        # using libraries like pdf2image, wand, or similar
        self.create_preview_placeholder(document_id)

    def track_metrics(
        self,
        file_path: str,
        document_type: str,
        template: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track metrics for document generation.

        Args:
            file_path: Path to generated file
            document_type: Type of document
            template: Optional template data
        """
        try:
            # Get file size
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            # Log metrics
            logger.info(
                f"Document generated: type={document_type}, size={file_size} bytes, "
                f"template={'yes' if template else 'no'}"
            )
            
            # In a real implementation, this would send metrics to a monitoring system
            # For example, using Prometheus, StatsD, or a custom metrics service
        except Exception as e:
            logger.error(f"Error tracking metrics: {e}")
