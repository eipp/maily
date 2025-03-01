"""Attachment generation tool for OctoTools."""

import logging
import asyncio
import os
import time
import json
import uuid
from typing import Dict, Any, List, Optional

from octotools import ToolCard

from ai.config import ATTACHMENT_TOOL_CONFIG

logger = logging.getLogger(__name__)

class AttachmentGeneratorTool(ToolCard):
    """Tool for generating various types of attachments for email campaigns."""

    def __init__(self):
        """Initialize the attachment generator tool."""
        super().__init__(
            tool_name="Attachment_Generator",
            tool_description="Generates various types of attachments for email campaigns.",
            input_types={
                "type": "str - The type of attachment to generate (pdf, pptx, xlsx, docx)",
                "content": "dict - Content to include in the attachment",
                "template": "str - Optional template name to use",
                "output_path": "str - Optional path to save the attachment",
                "metadata": "dict - Optional metadata to include in the attachment"
            },
            output_type="dict - Contains information about the generated attachment",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(type="pdf", content={"title": "Monthly Report", "sections": [{"heading": "Summary", "text": "This is a summary."}]})',
                    "description": "Generate a PDF report with a title and summary section"
                }
            ],
            user_metadata={
                "limitations": [
                    "Generated attachments use basic templates",
                    "Complex formatting may not be supported",
                    "Image inclusion requires local file paths"
                ],
                "best_practices": [
                    "Provide structured content with clear sections",
                    "Use templates for consistent formatting",
                    "Keep attachments concise and focused"
                ]
            }
        )

        # Initialize configuration
        self.config = ATTACHMENT_TOOL_CONFIG

        # Ensure storage path exists
        os.makedirs(self.config["storage_path"], exist_ok=True)

    async def execute(
        self,
        type: str,
        content: Dict[str, Any],
        template: str = None,
        output_path: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate an attachment based on the specified type and content.

        Args:
            type: The type of attachment to generate (pdf, pptx, xlsx, docx)
            content: Content to include in the attachment
            template: Optional template name to use
            output_path: Optional path to save the attachment
            metadata: Optional metadata to include in the attachment

        Returns:
            Dictionary containing information about the generated attachment
        """
        logger.info(f"Generating {type} attachment")

        try:
            # Validate inputs
            self._validate_inputs(type, content, template, output_path)

            # Determine output path
            if not output_path:
                filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}.{type}"
                output_path = os.path.join(self.config["storage_path"], filename)

            # In a real implementation, this would generate the actual file
            # For now, we'll simulate file generation
            await asyncio.sleep(1.0)  # Simulate file generation

            # Create a placeholder file
            self._create_placeholder_file(output_path, type, content, metadata)

            # Get file size
            file_size = os.path.getsize(output_path)

            return {
                "status": "success",
                "path": output_path,
                "type": type,
                "size": file_size,
                "filename": os.path.basename(output_path),
                "template": template,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "metadata": metadata or {}
            }
        except Exception as e:
            logger.error(f"Attachment generation failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "type": type
            }

    def _validate_inputs(self, type, content, template, output_path):
        """Validate input parameters."""
        if type not in self.config["allowed_types"]:
            raise ValueError(f"Type must be one of: {', '.join(self.config['allowed_types'])}")

        if not content or not isinstance(content, dict):
            raise ValueError("Content must be a non-empty dictionary")

        if output_path:
            # Check if directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.isdir(output_dir):
                raise ValueError(f"Output directory does not exist: {output_dir}")

            # Check file extension
            _, ext = os.path.splitext(output_path)
            if ext[1:] != type:
                raise ValueError(f"Output path extension ({ext}) does not match type ({type})")

    def _create_placeholder_file(self, output_path, type, content, metadata):
        """Create a placeholder file for demonstration purposes."""
        # Create a JSON representation of the content
        placeholder_content = {
            "type": type,
            "content": content,
            "metadata": metadata or {},
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": "This is a placeholder file for demonstration purposes"
        }

        # Write to file
        with open(output_path, "w") as f:
            json.dump(placeholder_content, f, indent=2)
