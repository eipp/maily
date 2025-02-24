import requests
import logging
from typing import List, Optional, Dict
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config import Settings
from ..models.email import EmailTemplate, EmailMessage, EmailStatus
from ..utils.encryption import EncryptionManager

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.encryption = EncryptionManager(settings)
        self.mailgun_api_key = settings.MAILGUN_API_KEY
        self.mailgun_domain = settings.MAILGUN_DOMAIN
        self.mailgun_base_url = f"https://api.mailgun.net/v3/{self.mailgun_domain}"
        self.from_email = f"JustMaily <noreply@{self.mailgun_domain}>"
        self.max_batch_size = 1000  # Mailgun's recommended batch size

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tracking_enabled: bool = True,
        custom_variables: Optional[Dict] = None
    ) -> EmailStatus:
        """
        Send a single email using Mailgun.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of the email
            text_content: Plain text version (auto-generated if None)
            reply_to: Reply-to email address
            tags: List of tags for tracking
            tracking_enabled: Whether to enable email tracking
            custom_variables: Custom variables for tracking
            
        Returns:
            EmailStatus: Status of the sent email
        """
        try:
            data = {
                "from": self.from_email,
                "to": to_email,
                "subject": subject,
                "html": html_content,
                "text": text_content or self._html_to_text(html_content),
                "o:tracking": str(tracking_enabled).lower(),
                "o:tag": tags or [],
                "v:variables": custom_variables or {}
            }

            if reply_to:
                data["h:Reply-To"] = reply_to

            response = requests.post(
                f"{self.mailgun_base_url}/messages",
                auth=("api", self.mailgun_api_key),
                data=data
            )
            
            response.raise_for_status()
            
            return EmailStatus(
                message_id=response.json()["id"],
                status="sent",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise

    async def send_batch(
        self,
        recipients: List[Dict],
        template: EmailTemplate,
        tags: Optional[List[str]] = None,
        tracking_enabled: bool = True
    ) -> List[EmailStatus]:
        """
        Send batch emails using Mailgun's batch sending API.
        
        Args:
            recipients: List of recipient data (email, variables)
            template: Email template to use
            tags: List of tags for tracking
            tracking_enabled: Whether to enable email tracking
            
        Returns:
            List[EmailStatus]: Status of each sent email
        """
        try:
            statuses = []
            
            # Process in batches of max_batch_size
            for i in range(0, len(recipients), self.max_batch_size):
                batch = recipients[i:i + self.max_batch_size]
                
                # Prepare recipient variables
                recipient_variables = {
                    recipient["email"]: recipient.get("variables", {})
                    for recipient in batch
                }
                
                data = {
                    "from": self.from_email,
                    "to": [r["email"] for r in batch],
                    "subject": template.subject,
                    "html": template.html_content,
                    "text": template.text_content,
                    "recipient-variables": recipient_variables,
                    "o:tracking": str(tracking_enabled).lower(),
                    "o:tag": tags or []
                }
                
                response = requests.post(
                    f"{self.mailgun_base_url}/messages",
                    auth=("api", self.mailgun_api_key),
                    data=data
                )
                
                response.raise_for_status()
                
                # Add status for each recipient in the batch
                for recipient in batch:
                    statuses.append(EmailStatus(
                        message_id=f"{response.json()['id']}_{recipient['email']}",
                        status="sent",
                        timestamp=datetime.utcnow()
                    ))
            
            return statuses
        except Exception as e:
            logger.error(f"Failed to send batch emails: {str(e)}")
            raise

    async def get_email_status(self, message_id: str) -> EmailStatus:
        """
        Get the status of a sent email.
        
        Args:
            message_id: The Mailgun message ID
            
        Returns:
            EmailStatus: Current status of the email
        """
        try:
            response = requests.get(
                f"{self.mailgun_base_url}/events/{message_id}",
                auth=("api", self.mailgun_api_key)
            )
            
            response.raise_for_status()
            data = response.json()
            
            return EmailStatus(
                message_id=message_id,
                status=data["event"],
                timestamp=datetime.fromtimestamp(data["timestamp"])
            )
        except Exception as e:
            logger.error(f"Failed to get email status: {str(e)}")
            raise

    async def validate_email(self, email: str) -> bool:
        """
        Validate an email address using Mailgun's validation API.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: Whether the email is valid
        """
        try:
            response = requests.get(
                "https://api.mailgun.net/v4/address/validate",
                auth=("api", self.mailgun_api_key),
                params={"address": email}
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data["is_valid"]
        except Exception as e:
            logger.error(f"Failed to validate email: {str(e)}")
            return False

    async def get_stats(
        self,
        start_date: datetime,
        end_date: datetime,
        event: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Get email statistics from Mailgun.
        
        Args:
            start_date: Start date for stats
            end_date: End date for stats
            event: Specific event to filter (e.g., "delivered", "opened")
            tags: Filter by specific tags
            
        Returns:
            Dict: Email statistics
        """
        try:
            params = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
            
            if event:
                params["event"] = event
            if tags:
                params["tags"] = tags

            response = requests.get(
                f"{self.mailgun_base_url}/stats/total",
                auth=("api", self.mailgun_api_key),
                params=params
            )
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get email stats: {str(e)}")
            raise

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text."""
        # Simple HTML to text conversion
        # In production, use a proper HTML to text converter
        text = html_content.replace('<br>', '\n')
        text = text.replace('</p>', '\n\n')
        text = text.replace('</div>', '\n')
        # Remove other HTML tags
        while '<' in text and '>' in text:
            start = text.find('<')
            end = text.find('>', start)
            if end == -1:
                break
            text = text[:start] + text[end + 1:]
        return text.strip() 