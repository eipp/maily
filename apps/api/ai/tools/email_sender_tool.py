"""Email sender tool for OctoTools."""

import logging
import asyncio
import time
import os
from typing import Dict, Any, List, Optional

from octotools import ToolCard

from ai.config import EMAIL_TOOL_CONFIG

logger = logging.getLogger(__name__)

class EmailSenderTool(ToolCard):
    """Tool for sending emails through configured email providers."""

    def __init__(self):
        """Initialize the email sender tool."""
        super().__init__(
            tool_name="Email_Sender",
            tool_description="Sends emails through configured email providers.",
            input_types={
                "from_email": "str - The sender's email address",
                "to_emails": "list - List of recipient email addresses",
                "subject": "str - The email subject",
                "html_content": "str - The HTML content of the email",
                "plain_text": "str - The plain text content of the email",
                "attachments": "list - Optional list of attachment file paths",
                "provider": "str - Optional email provider to use (default: auto-select)",
                "metadata": "dict - Optional metadata for tracking and analytics"
            },
            output_type="dict - Contains information about the sent email",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(from_email="sender@example.com", to_emails=["recipient@example.com"], subject="Test Email", html_content="<p>Hello World</p>", plain_text="Hello World")',
                    "description": "Send a simple email to a single recipient"
                }
            ],
            user_metadata={
                "limitations": [
                    "Email delivery is subject to provider rate limits",
                    "Attachments must be accessible on the local filesystem",
                    "Total attachment size is limited by the provider"
                ],
                "best_practices": [
                    "Always provide both HTML and plain text versions",
                    "Keep attachment sizes reasonable",
                    "Include proper unsubscribe links in marketing emails",
                    "Test emails before sending to large lists"
                ]
            }
        )

        # Initialize configuration
        self.config = EMAIL_TOOL_CONFIG

    async def execute(
        self,
        from_email: str,
        to_emails: List[str],
        subject: str,
        html_content: str,
        plain_text: str,
        attachments: List[str] = None,
        provider: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send an email through the configured provider.

        Args:
            from_email: The sender's email address
            to_emails: List of recipient email addresses
            subject: The email subject
            html_content: The HTML content of the email
            plain_text: The plain text content of the email
            attachments: Optional list of attachment file paths
            provider: Optional email provider to use (default: auto-select)
            metadata: Optional metadata for tracking and analytics

        Returns:
            Dictionary containing information about the sent email
        """
        logger.info(f"Sending email to {len(to_emails)} recipients with subject: {subject}")

        try:
            # Validate inputs
            self._validate_inputs(from_email, to_emails, subject, html_content, plain_text, attachments, provider)

            # Select provider if not specified
            selected_provider = provider or self._select_provider(to_emails)

            # Validate attachments if provided
            if attachments:
                await self._validate_attachments(attachments)

            # In a real implementation, this would call the email provider's API
            # For now, we'll simulate sending the email
            await asyncio.sleep(0.5)  # Simulate API call

            # Generate a message ID
            message_id = f"{selected_provider}_{int(time.time())}_{hash(str(to_emails))}"

            # Log the email send
            logger.info(f"Email sent via {selected_provider} with message ID: {message_id}")

            return {
                "status": "success",
                "provider": selected_provider,
                "message_id": message_id,
                "from_email": from_email,
                "to_count": len(to_emails),
                "subject": subject,
                "has_attachments": bool(attachments),
                "attachment_count": len(attachments) if attachments else 0,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "metadata": metadata or {}
            }
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "provider": provider,
                "from_email": from_email,
                "to_count": len(to_emails),
                "subject": subject
            }

    def _validate_inputs(self, from_email, to_emails, subject, html_content, plain_text, attachments, provider):
        """Validate input parameters."""
        if not from_email or "@" not in from_email:
            raise ValueError("Invalid from_email address")

        if not to_emails or not isinstance(to_emails, list) or not all("@" in email for email in to_emails):
            raise ValueError("Invalid to_emails list")

        if not subject:
            raise ValueError("Subject is required")

        if not html_content and not plain_text:
            raise ValueError("Either html_content or plain_text is required")

        if provider and provider not in self.config["providers"]:
            raise ValueError(f"Provider must be one of: {', '.join(self.config['providers'])}")

    def _select_provider(self, to_emails):
        """Select the best provider based on the recipient list."""
        # In a real implementation, this would use logic to select the best provider
        # For now, we'll just use the first configured provider
        return self.config["providers"][0]

    async def _validate_attachments(self, attachments):
        """Validate attachment files."""
        total_size = 0

        for attachment_path in attachments:
            # Check if file exists
            if not os.path.isfile(attachment_path):
                raise ValueError(f"Attachment file not found: {attachment_path}")

            # Check file size
            file_size = os.path.getsize(attachment_path)
            total_size += file_size

            # Check file extension
            _, ext = os.path.splitext(attachment_path)
            if ext.lower() not in [".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".csv", ".png", ".jpg", ".jpeg", ".gif"]:
                logger.warning(f"Attachment has uncommon extension: {ext}")

        # Check total size
        if total_size > self.config.get("max_attachment_size", 25 * 1024 * 1024):  # Default: 25MB
            raise ValueError(f"Total attachment size ({total_size / (1024 * 1024):.2f}MB) exceeds maximum allowed")
