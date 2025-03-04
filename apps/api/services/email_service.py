"""
Email service for sending emails and tracking analytics.
"""

import logging
import os
import time
import uuid
from typing import Dict, Any, Optional

import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Email provider API keys
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "mg.example.com")

# Default email provider
DEFAULT_PROVIDER = os.getenv("DEFAULT_EMAIL_PROVIDER", "sendgrid")


class EmailService:
    """Service for sending emails and tracking analytics."""

    def __init__(self, provider: Optional[str] = None):
        """Initialize the email service."""
        self.provider = provider or DEFAULT_PROVIDER
        self.api_keys = {
            "sendgrid": SENDGRID_API_KEY,
            "mailgun": MAILGUN_API_KEY,
        }

    def send_email(
        self, to_email: str, subject: str, content: str, from_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an email using the configured provider."""
        from_email = from_email or "noreply@justmaily.com"
        message_id = str(uuid.uuid4())

        # Add tracking pixel for open tracking
        tracking_pixel = f'<img src="https://justmaily.com/api/tracking/open/{message_id}" width="1" height="1" />'
        html_content = content + tracking_pixel

        # Track clicks by replacing links
        html_content = self._add_click_tracking(html_content, message_id)

        if self.provider == "sendgrid":
            return self._send_with_sendgrid(
                to_email, from_email, subject, html_content, message_id
            )
        elif self.provider == "mailgun":
            return self._send_with_mailgun(
                to_email, from_email, subject, html_content, message_id
            )
        else:
            logger.error(f"Unsupported email provider: {self.provider}")
            return {
                "status": "error",
                "error": f"Unsupported email provider: {self.provider}",
                "message_id": message_id,
            }

    def _send_with_sendgrid(
        self, to_email: str, from_email: str, subject: str, html_content: str, message_id: str
    ) -> Dict[str, Any]:
        """Send an email using SendGrid."""
        if not self.api_keys.get("sendgrid"):
            logger.error("SendGrid API key not configured")
            return {
                "status": "error",
                "error": "SendGrid API key not configured",
                "message_id": message_id,
            }

        try:
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.api_keys['sendgrid']}",
                "Content-Type": "application/json",
            }
            data = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": from_email},
                "subject": subject,
                "content": [{"type": "text/html", "value": html_content}],
                "custom_args": {"message_id": message_id},
            }

            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()

            return {
                "status": "sent",
                "message_id": message_id,
                "provider": "sendgrid",
                "provider_response": response.status_code,
            }
        except RequestException as e:
            logger.error(f"SendGrid API error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message_id": message_id,
                "provider": "sendgrid",
            }

    def _send_with_mailgun(
        self, to_email: str, from_email: str, subject: str, html_content: str, message_id: str
    ) -> Dict[str, Any]:
        """Send an email using Mailgun."""
        if not self.api_keys.get("mailgun"):
            logger.error("Mailgun API key not configured")
            return {
                "status": "error",
                "error": "Mailgun API key not configured",
                "message_id": message_id,
            }

        try:
            url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
            auth = ("api", self.api_keys["mailgun"])
            data = {
                "from": from_email,
                "to": to_email,
                "subject": subject,
                "html": html_content,
                "v:message_id": message_id,
            }

            response = requests.post(url, auth=auth, data=data, timeout=10)
            response.raise_for_status()
            response_data = response.json()

            return {
                "status": "sent",
                "message_id": message_id,
                "provider": "mailgun",
                "provider_response": response_data,
            }
        except RequestException as e:
            logger.error(f"Mailgun API error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message_id": message_id,
                "provider": "mailgun",
            }

    def _add_click_tracking(self, html_content: str, message_id: str) -> str:
        """Add click tracking to links in the HTML content."""
        import re

        def replace_link(match):
            original_url = match.group(2)
            tracking_url = f"https://justmaily.com/api/tracking/click/{message_id}?url={original_url}"
            return f'{match.group(1)}{tracking_url}{match.group(3)}'

        # Find and replace href attributes
        pattern = r'(href=["\'])([^"\']*)(["\'])'
        return re.sub(pattern, replace_link, html_content)

    def get_analytics(self, message_id: str) -> Dict[str, Any]:
        """Get analytics for a specific email."""
        # In a real implementation, this would query the email provider's API
        # For now, we'll return mock data
        return {
            "message_id": message_id,
            "opens": 0,
            "clicks": 0,
            "bounces": 0,
            "delivered": True,
            "delivery_time": time.time(),
        }
