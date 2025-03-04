"""
Platform integration framework for cross-platform campaigns.
"""
from typing import Dict, List, Any, Optional, Union, Callable, Type
from enum import Enum
import asyncio
import json
import time
from datetime import datetime, timedelta
import structlog
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from ..errors.maily_error import ResourceNotFoundError, ValidationError, IntegrationError
from ..models.platform_model import PlatformAccount, PlatformPost, CrossPlatformCampaign
from ..monitoring.performance_metrics import MetricType
from ..cache.tiered_cache_service import CacheTier

logger = structlog.get_logger("justmaily.platforms.integration")

class PlatformType(str, Enum):
    """Supported platform types."""
    EMAIL = "email"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"

class PlatformAction(str, Enum):
    """Supported platform actions."""
    POST = "post"
    SEND = "send"
    SCHEDULE = "schedule"
    ANALYZE = "analyze"

class PlatformScope(str, Enum):
    """Permission scopes for platforms."""
    READ = "read"
    WRITE = "write"
    CONTENT = "content"
    ANALYTICS = "analytics"
    EMAIL = "email"
    PROFILE = "profile"

class PlatformCredentials(BaseModel):
    """Base model for platform credentials."""
    user_id: str
    platform: PlatformType
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    scopes: List[PlatformScope] = []

    class Config:
        orm_mode = True

class EmailCredentials(PlatformCredentials):
    """Credentials for email platforms."""
    api_key: str
    platform_name: str = "default"
    from_email: str
    from_name: Optional[str] = None
    reply_to: Optional[str] = None

class LinkedInCredentials(PlatformCredentials):
    """Credentials for LinkedIn."""
    access_token: str
    refresh_token: str
    profile_id: str
    company_id: Optional[str] = None

class TwitterCredentials(PlatformCredentials):
    """Credentials for Twitter."""
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str
    bearer_token: str

class FacebookCredentials(PlatformCredentials):
    """Credentials for Facebook."""
    access_token: str
    page_id: Optional[str] = None
    instagram_account_id: Optional[str] = None

class InstagramCredentials(PlatformCredentials):
    """Credentials for Instagram."""
    access_token: str
    instagram_account_id: str
    facebook_page_id: str

class PlatformContent(BaseModel):
    """Content for a platform post."""
    text: str
    media_urls: List[str] = []
    link_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    html_content: Optional[str] = None
    call_to_action: Optional[str] = None

    class Config:
        orm_mode = True

class PlatformAnalytics(BaseModel):
    """Analytics data for a platform post."""
    impressions: int = 0
    engagements: int = 0
    clicks: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    conversions: int = 0
    revenue: float = 0
    platform_specific: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True

class PlatformAdapter:
    """Base class for platform adapters."""

    def __init__(self, credentials: PlatformCredentials):
        """Initialize platform adapter with credentials.

        Args:
            credentials: Platform credentials
        """
        self.credentials = credentials
        self.platform_type = credentials.platform
        self.rate_limit_remaining = 100
        self.rate_limit_reset = 0

    async def post(self, content: PlatformContent, **kwargs) -> Dict[str, Any]:
        """Post content to the platform.

        Args:
            content: Content to post
            **kwargs: Additional platform-specific parameters

        Returns:
            Post result with platform-specific data

        Raises:
            NotImplementedError: Method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement post method")

    async def schedule(
        self,
        content: PlatformContent,
        schedule_time: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """Schedule content for future posting.

        Args:
            content: Content to post
            schedule_time: When to post the content
            **kwargs: Additional platform-specific parameters

        Returns:
            Schedule result with platform-specific data

        Raises:
            NotImplementedError: Method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement schedule method")

    async def analyze(self, post_id: str, **kwargs) -> PlatformAnalytics:
        """Get analytics data for a post.

        Args:
            post_id: ID of the post to analyze
            **kwargs: Additional platform-specific parameters

        Returns:
            Analytics data

        Raises:
            NotImplementedError: Method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement analyze method")

    async def get_account_info(self) -> Dict[str, Any]:
        """Get information about the connected account.

        Returns:
            Account information

        Raises:
            NotImplementedError: Method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement get_account_info method")

    async def verify_credentials(self) -> bool:
        """Verify that the credentials are valid.

        Returns:
            True if credentials are valid, False otherwise

        Raises:
            NotImplementedError: Method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement verify_credentials method")

    async def refresh_credentials(self) -> PlatformCredentials:
        """Refresh the credentials if possible.

        Returns:
            Updated credentials

        Raises:
            NotImplementedError: Method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement refresh_credentials method")

    def _check_rate_limits(self) -> bool:
        """Check if we're within rate limits.

        Returns:
            True if we can make more requests, False otherwise
        """
        if self.rate_limit_remaining <= 0 and time.time() < self.rate_limit_reset:
            reset_in = self.rate_limit_reset - time.time()
            logger.warning(
                "Rate limit exceeded",
                platform=self.platform_type,
                reset_in_seconds=reset_in
            )
            return False
        return True

    def _update_rate_limits(self, remaining: int, reset: int) -> None:
        """Update rate limit information.

        Args:
            remaining: Number of requests remaining
            reset: Timestamp when the rate limit resets
        """
        self.rate_limit_remaining = remaining
        self.rate_limit_reset = reset

class EmailAdapter(PlatformAdapter):
    """Adapter for email platforms."""

    def __init__(self, credentials: EmailCredentials):
        """Initialize email adapter.

        Args:
            credentials: Email credentials
        """
        super().__init__(credentials)
        self.credentials = credentials
        self.client = self._initialize_client()

    def _initialize_client(self) -> Any:
        """Initialize the email client based on the platform.

        Returns:
            Initialized email client
        """
        # This would initialize the appropriate email service client
        # based on the credentials.platform_name (e.g., Sendgrid, Mailgun)
        platform_name = self.credentials.platform_name.lower()

        if platform_name == "sendgrid":
            # Initialize SendGrid client
            try:
                import sendgrid
                return sendgrid.SendGridAPIClient(api_key=self.credentials.api_key)
            except ImportError:
                logger.error("SendGrid package not installed")
                raise IntegrationError("SendGrid package not installed")

        elif platform_name == "mailgun":
            # Initialize Mailgun client
            try:
                import httpx
                return {
                    "api_key": self.credentials.api_key,
                    "session": requests.Session(),
                    "domain": self.credentials.from_email.split("@")[1]
                }
            except ImportError:
                logger.error("Requests package not installed")
                raise IntegrationError("Requests package not installed")

        elif platform_name == "resend":
            # Initialize Resend client
            try:
                import resend
                resend.api_key = self.credentials.api_key
                return resend
            except ImportError:
                logger.error("Resend package not installed")
                raise IntegrationError("Resend package not installed")

        else:
            # Default to a generic SMTP client
            try:
                import smtplib
                return smtplib.SMTP(host="smtp.example.com", port=587)
            except ImportError:
                logger.error("SMTP library not available")
                raise IntegrationError("SMTP library not available")

    async def post(self, content: PlatformContent, **kwargs) -> Dict[str, Any]:
        """Send an email immediately.

        Args:
            content: Email content
            **kwargs: Additional parameters like recipients

        Returns:
            Send result

        Raises:
            IntegrationError: If sending fails
        """
        recipients = kwargs.get("recipients", [])
        subject = kwargs.get("subject", "")

        if not recipients:
            raise ValidationError("Recipients are required")

        if not subject:
            raise ValidationError("Subject is required")

        try:
            platform_name = self.credentials.platform_name.lower()
            result = {}

            if platform_name == "sendgrid":
                # Send with SendGrid
                from sendgrid.helpers.mail import Mail, Content, Email, To

                # Create the email
                mail = Mail(
                    from_email=Email(self.credentials.from_email, self.credentials.from_name),
                    subject=subject
                )

                # Add recipients
                for recipient in recipients:
                    mail.add_to(To(recipient))

                # Set content
                if content.html_content:
                    mail.add_content(Content("text/html", content.html_content))
                else:
                    mail.add_content(Content("text/plain", content.text))

                # Send the email
                response = self.client.send(mail)

                result = {
                    "status_code": response.status_code,
                    "body": response.body,
                    "headers": dict(response.headers)
                }

            elif platform_name == "mailgun":
                # Send with Mailgun
                import httpx

                domain = self.client["domain"]
                auth = ("api", self.client["api_key"])

                data = {
                    "from": f"{self.credentials.from_name or 'Maily'} <{self.credentials.from_email}>",
                    "to": recipients,
                    "subject": subject,
                    "text": content.text,
                }

                if content.html_content:
                    data["html"] = content.html_content

                response = requests.post(
                    f"https://api.mailgun.net/v3/{domain}/messages",
                    auth=auth,
                    data=data
                )

                response.raise_for_status()
                result = response.json()

            elif platform_name == "resend":
                # Send with Resend
                response = await self.client.emails.send({
                    "from": f"{self.credentials.from_name or 'Maily'} <{self.credentials.from_email}>",
                    "to": recipients,
                    "subject": subject,
                    "text": content.text,
                    "html": content.html_content or None
                })

                result = response

            else:
                # Generic SMTP implementation
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart

                # Create the email
                msg = MIMEMultipart("alternative")
                msg["From"] = f"{self.credentials.from_name or 'Maily'} <{self.credentials.from_email}>"
                msg["To"] = ", ".join(recipients)
                msg["Subject"] = subject

                # Add text part
                if content.text:
                    msg.attach(MIMEText(content.text, "plain"))

                # Add HTML part
                if content.html_content:
                    msg.attach(MIMEText(content.html_content, "html"))

                # Send the email
                self.client.starttls()
                self.client.login("username", "password")  # Replace with actual credentials
                self.client.send_message(msg)
                self.client.quit()

                result = {"status": "sent"}

            return {
                "platform": PlatformType.EMAIL,
                "provider": platform_name,
                "message_id": result.get("id", str(int(time.time()))),
                "recipient_count": len(recipients),
                "sent_at": datetime.now().isoformat(),
                "response": result
            }

        except Exception as e:
            logger.error(
                "Failed to send email",
                platform=self.credentials.platform_name,
                error=str(e),
                error_type=e.__class__.__name__
            )
            raise IntegrationError(f"Failed to send email: {str(e)}")

    async def schedule(
        self,
        content: PlatformContent,
        schedule_time: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """Schedule an email for future sending.

        Args:
            content: Email content
            schedule_time: When to send the email
            **kwargs: Additional parameters like recipients

        Returns:
            Schedule result

        Raises:
            IntegrationError: If scheduling fails
        """
        # For email, we'll assume scheduling is handled by the application,
        # not the email service itself. So we just return info to store.
        recipients = kwargs.get("recipients", [])
        subject = kwargs.get("subject", "")

        if not recipients:
            raise ValidationError("Recipients are required")

        if not subject:
            raise ValidationError("Subject is required")

        return {
            "platform": PlatformType.EMAIL,
            "provider": self.credentials.platform_name,
            "schedule_id": f"scheduled_{int(time.time())}",
            "scheduled_time": schedule_time.isoformat(),
            "subject": subject,
            "recipient_count": len(recipients),
            "scheduled_at": datetime.now().isoformat()
        }

    async def analyze(self, post_id: str, **kwargs) -> PlatformAnalytics:
        """Get analytics data for an email.

        Args:
            post_id: ID of the email to analyze
            **kwargs: Additional parameters

        Returns:
            Email analytics data

        Raises:
            IntegrationError: If analytics retrieval fails
        """
        try:
            platform_name = self.credentials.platform_name.lower()

            # In a real implementation, this would retrieve analytics from the
            # email service's API. For now, we'll return placeholder data.
            email_analytics = PlatformAnalytics(
                impressions=kwargs.get("opens", 50),
                clicks=kwargs.get("clicks", 10),
                engagements=kwargs.get("opens", 50) + kwargs.get("clicks", 10),
                platform_specific={
                    "opens": kwargs.get("opens", 50),
                    "unique_opens": kwargs.get("unique_opens", 40),
                    "clicks": kwargs.get("clicks", 10),
                    "unique_clicks": kwargs.get("unique_clicks", 8),
                    "bounces": kwargs.get("bounces", 2),
                    "complaints": kwargs.get("complaints", 0),
                    "unsubscribes": kwargs.get("unsubscribes", 1)
                }
            )

            return email_analytics

        except Exception as e:
            logger.error(
                "Failed to get email analytics",
                platform=self.credentials.platform_name,
                error=str(e),
                error_type=e.__class__.__name__
            )
            raise IntegrationError(f"Failed to get email analytics: {str(e)}")

    async def get_account_info(self) -> Dict[str, Any]:
        """Get information about the email account.

        Returns:
            Account information

        Raises:
            IntegrationError: If account info retrieval fails
        """
        # For email, this would typically just return the sender information
        return {
            "platform": PlatformType.EMAIL,
            "provider": self.credentials.platform_name,
            "email": self.credentials.from_email,
            "name": self.credentials.from_name,
            "reply_to": self.credentials.reply_to
        }

    async def verify_credentials(self) -> bool:
        """Verify that the email credentials are valid.

        Returns:
            True if credentials are valid, False otherwise

        Raises:
            IntegrationError: If verification fails
        """
        try:
            platform_name = self.credentials.platform_name.lower()

            if platform_name == "sendgrid":
                # Verify SendGrid credentials by making a simple API call
                response = self.client.client.api_keys.get()
                return response.status_code == 200

            elif platform_name == "mailgun":
                # Verify Mailgun credentials by making a simple API call
                import httpx

                domain = self.client["domain"]
                auth = ("api", self.client["api_key"])

                response = requests.get(
                    f"https://api.mailgun.net/v3/{domain}/events",
                    auth=auth
                )

                return response.status_code == 200

            elif platform_name == "resend":
                # Verify Resend credentials
                response = await self.client.domains.list()
                return "data" in response

            else:
                # Generic SMTP verification
                try:
                    self.client.noop()
                    return True
                except:
                    return False

        except Exception as e:
            logger.error(
                "Failed to verify email credentials",
                platform=self.credentials.platform_name,
                error=str(e),
                error_type=e.__class__.__name__
            )
            return False

    async def refresh_credentials(self) -> EmailCredentials:
        """Refresh the email credentials if needed.

        Returns:
            Updated credentials (not applicable for email)

        Raises:
            IntegrationError: If refresh fails
        """
        # Email credentials typically don't need refreshing
        return self.credentials

class LinkedInAdapter(PlatformAdapter):
    """Adapter for LinkedIn integration."""

    def __init__(self, credentials: LinkedInCredentials):
        """Initialize LinkedIn adapter.

        Args:
            credentials: LinkedIn credentials
        """
        super().__init__(credentials)
        self.credentials = credentials
        # In a real implementation, we would initialize a LinkedIn API client

    async def post(self, content: PlatformContent, **kwargs) -> Dict[str, Any]:
        """Post content to LinkedIn.

        Args:
            content: Content to post
            **kwargs: Additional LinkedIn-specific parameters

        Returns:
            Post result

        Raises:
            IntegrationError: If posting fails
        """
        try:
            if not self._check_rate_limits():
                raise IntegrationError("LinkedIn rate limit exceeded")

            # This would be a real LinkedIn API call in production
            # Here's a placeholder implementation

            post_data = {
                "author": f"urn:li:person:{self.credentials.profile_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content.text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            # Add media if present
            if content.media_urls:
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                    {
                        "status": "READY",
                        "description": {
                            "text": "Image"
                        },
                        "media": f"urn:li:image:{int(time.time())}",
                        "title": {
                            "text": content.title or "Image"
                        }
                    }
                ]

            # Add link if present
            if content.link_url:
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                    {
                        "status": "READY",
                        "originalUrl": content.link_url,
                        "title": {
                            "text": content.title or "Link"
                        },
                        "description": {
                            "text": content.description or ""
                        }
                    }
                ]

            # Simulate a successful post
            post_id = f"linkedin_post_{int(time.time())}"

            # Update rate limits (LinkedIn typically allows 100 requests per day)
            self._update_rate_limits(99, int(time.time()) + 86400)

            return {
                "platform": PlatformType.LINKEDIN,
                "post_id": post_id,
                "posted_at": datetime.now().isoformat(),
                "url": f"https://www.linkedin.com/feed/update/{post_id}",
                "response": {
                    "id": post_id,
                    "status": "PUBLISHED"
                }
            }

        except Exception as e:
            logger.error(
                "Failed to post to LinkedIn",
                error=str(e),
                error_type=e.__class__.__name__
            )
            raise IntegrationError(f"Failed to post to LinkedIn: {str(e)}")

    async def schedule(
        self,
        content: PlatformContent,
        schedule_time: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """Schedule content for future posting on LinkedIn.

        Note: LinkedIn doesn't support native scheduling through the API,
        so this would be implemented through a job scheduler in the application.

        Args:
            content: Content to post
            schedule_time: When to post the content
            **kwargs: Additional parameters

        Returns:
            Schedule result

        Raises:
            IntegrationError: If scheduling fails
        """
        # LinkedIn doesn't support scheduling via API directly,
        # so we'd store this for our application to post later
        schedule_id = f"linkedin_schedule_{int(time.time())}"

        return {
            "platform": PlatformType.LINKEDIN,
            "schedule_id": schedule_id,
            "scheduled_time": schedule_time.isoformat(),
            "scheduled_at": datetime.now().isoformat()
        }

    async def analyze(self, post_id: str, **kwargs) -> PlatformAnalytics:
        """Get analytics data for a LinkedIn post.

        Args:
            post_id: ID of the post to analyze
            **kwargs: Additional parameters

        Returns:
            Analytics data

        Raises:
            IntegrationError: If analytics retrieval fails
        """
        try:
            if not self._check_rate_limits():
                raise IntegrationError("LinkedIn rate limit exceeded")

            # This would be a real LinkedIn API call in production
            # Here's a placeholder implementation

            # Update rate limits
            self._update_rate_limits(98, int(time.time()) + 86400)

            # In a real implementation, we would fetch actual analytics
            # from LinkedIn's API. For now, we'll return placeholder data.
            return PlatformAnalytics(
                impressions=kwargs.get("impressions", 500),
                engagements=kwargs.get("engagements", 50),
                clicks=kwargs.get("clicks", 20),
                likes=kwargs.get("likes", 30),
                comments=kwargs.get("comments", 5),
                shares=kwargs.get("shares", 3),
                platform_specific={
                    "impressions_by_region": {
                        "us": 300,
                        "europe": 150,
                        "asia": 50
                    },
                    "clicks_by_device": {
                        "desktop": 15,
                        "mobile": 5
                    }
                }
            )

        except Exception as e:
            logger.error(
                "Failed to get LinkedIn analytics",
                post_id=post_id,
                error=str(e),
                error_type=e.__class__.__name__
            )
            raise IntegrationError(f"Failed to get LinkedIn analytics: {str(e)}")

    async def get_account_info(self) -> Dict[str, Any]:
        """Get information about the LinkedIn account.

        Returns:
            Account information

        Raises:
            IntegrationError: If account info retrieval fails
        """
        try:
            if not self._check_rate_limits():
                raise IntegrationError("LinkedIn rate limit exceeded")

            # This would be a real LinkedIn API call in production
            # Here's a placeholder implementation

            # Update rate limits
            self._update_rate_limits(97, int(time.time()) + 86400)

            return {
                "platform": PlatformType.LINKEDIN,
                "profile_id": self.credentials.profile_id,
                "name": "LinkedIn User",
                "headline": "Professional at Company",
                "company_id": self.credentials.company_id,
                "company_name": "Company Name" if self.credentials.company_id else None
            }

        except Exception as e:
            logger.error(
                "Failed to get LinkedIn account info",
                error=str(e),
                error_type=e.__class__.__name__
            )
            raise IntegrationError(f"Failed to get LinkedIn account info: {str(e)}")

    async def verify_credentials(self) -> bool:
        """Verify that the LinkedIn credentials are valid.

        Returns:
            True if credentials are valid, False otherwise

        Raises:
            IntegrationError: If verification fails
        """
        try:
            if not self._check_rate_limits():
                return False

            # This would be a real LinkedIn API call in production
            # Here's a placeholder implementation

            # Update rate limits
            self._update_rate_limits(96, int(time.time()) + 86400)

            # Check if the token is expired
            if self.credentials.expires_at and self.credentials.expires_at < datetime.now():
                # Try to refresh the token
                refreshed = await self.refresh_credentials()
                return refreshed != self.credentials

            return True

        except Exception as e:
            logger.error(
                "Failed to verify LinkedIn credentials",
                error=str(e),
                error_type=e.__class__.__name__
            )
            return False

    async def refresh_credentials(self) -> LinkedInCredentials:
        """Refresh the LinkedIn access token.

        Returns:
            Updated credentials

        Raises:
            IntegrationError: If refresh fails
        """
        try:
            # This would be a real LinkedIn API call in production
            # to refresh the access token using the refresh token

            # Placeholder implementation
            new_credentials = self.credentials.copy()
            new_credentials.access_token = f"new_token_{int(time.time())}"
            new_credentials.expires_at = datetime.now() + timedelta(days=60)
            new_credentials.updated_at = datetime.now()

            return new_credentials

        except Exception as e:
            logger.error(
                "Failed to refresh LinkedIn credentials",
                error=str(e),
                error_type=e.__class__.__name__
            )
            raise IntegrationError(f"Failed to refresh LinkedIn credentials: {str(e)}")

class PlatformService:
    """Service for cross-platform integration and coordination."""

    def __init__(
        self,
        db: Session,
        metrics_service=None,
        cache_service=None
    ):
        """Initialize the platform service.

        Args:
            db: Database session
            metrics_service: Optional metrics service
            cache_service: Optional cache service
        """
        self.db = db
        self.metrics = metrics_service
        self.cache = cache_service
        self.platform_adapters: Dict[PlatformType, Dict[str, PlatformAdapter]] = {
            PlatformType.EMAIL: {},
            PlatformType.LINKEDIN: {},
            PlatformType.TWITTER: {},
            PlatformType.FACEBOOK: {},
            PlatformType.INSTAGRAM: {}
        }

    def _register_adapter(self, user_id: str, adapter: PlatformAdapter) -> None:
        """Register a platform adapter for a user.

        Args:
            user_id: User ID
            adapter: Platform adapter
        """
        platform_type = adapter.platform_type
        self.platform_adapters[platform_type][user_id] = adapter

    def _get_adapter(self, user_id: str, platform: PlatformType) -> PlatformAdapter:
        """Get a platform adapter for a user.

        Args:
            user_id: User ID
            platform: Platform type

        Returns:
            Platform adapter

        Raises:
            ResourceNotFoundError: If adapter not found
        """
        if user_id not in self.platform_adapters[platform]:
            # Try to load adapter from database
            try:
                # This would load credentials from the database
                # and initialize the appropriate adapter
                if platform == PlatformType.EMAIL:
                    # Placeholder: In production, load from DB
                    credentials = EmailCredentials(
                        user_id=user_id,
                        platform=PlatformType.EMAIL,
                        api_key="api_key_placeholder",
                        platform_name="sendgrid",
                        from_email="user@example.com",
                        from_name="Example User"
                    )
                    adapter = EmailAdapter(credentials)
                    self._register_adapter(user_id, adapter)

                elif platform == PlatformType.LINKEDIN:
                    # Placeholder: In production, load from DB
                    credentials = LinkedInCredentials(
                        user_id=user_id,
                        platform=PlatformType.LINKEDIN,
                        access_token="access_token_placeholder",
                        refresh_token="refresh_token_placeholder",
                        profile_id="profile_id_placeholder",
                        expires_at=datetime.now() + timedelta(days=60)
                    )
                    adapter = LinkedInAdapter(credentials)
                    self._register_adapter(user_id, adapter)

                else:
                    raise ResourceNotFoundError(f"No adapter available for platform: {platform}")

            except Exception as e:
                logger.error(
                    "Failed to load platform adapter",
                    user_id=user_id,
                    platform=platform,
                    error=str(e),
                    error_type=e.__class__.__name__
                )
                raise ResourceNotFoundError(f"No adapter available for platform: {platform}")

        return self.platform_adapters[platform].get(user_id)

    async def execute_platform_action(
        self,
        user_id: str,
        platform: PlatformType,
        action: PlatformAction,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an action on a specific platform.

        Args:
            user_id: User ID
            platform: Platform type
            action: Action to execute
            data: Action data

        Returns:
            Action result

        Raises:
            ValidationError: If action is invalid
            ResourceNotFoundError: If adapter not found
            IntegrationError: If action execution fails
        """
        start_time = time.time()
        adapter = self._get_adapter(user_id, platform)

        if not adapter:
            raise ResourceNotFoundError(f"No adapter found for platform: {platform}")

        try:
            # Record metric
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.INTEGRATION,
                    name=f"platform_action_start_{platform}_{action}",
                    duration_ms=0,
                    metadata={
                        "user_id": user_id,
                        "platform": platform,
                        "action": action
                    }
                )

            result = {}

            if action == PlatformAction.POST:
                # Create platform content
                content = PlatformContent(**data.get("content", {}))

                # Execute post action
                result = await adapter.post(content, **data.get("options", {}))

                # Store in database
                post = PlatformPost(
                    user_id=user_id,
                    platform=platform,
                    platform_id=result.get("post_id"),
                    content=content.dict(),
                    posted_at=datetime.now(),
                    status="PUBLISHED",
                    url=result.get("url"),
                    cross_platform_campaign_id=data.get("cross_platform_campaign_id")
                )

                self.db.add(post)
                self.db.commit()

                result["database_id"] = post.id

            elif action == PlatformAction.SCHEDULE:
                # Create platform content
                content = PlatformContent(**data.get("content", {}))
                schedule_time = datetime.fromisoformat(data.get("schedule_time"))

                # Execute schedule action
                result = await adapter.schedule(content, schedule_time, **data.get("options", {}))

                # Store in database
                post = PlatformPost(
                    user_id=user_id,
                    platform=platform,
                    platform_id=result.get("schedule_id"),
                    content=content.dict(),
                    scheduled_at=datetime.now(),
                    scheduled_for=schedule_time,
                    status="SCHEDULED",
                    cross_platform_campaign_id=data.get("cross_platform_campaign_id")
                )

                self.db.add(post)
                self.db.commit()

                result["database_id"] = post.id

            elif action == PlatformAction.ANALYZE:
                # Get post ID
                post_id = data.get("post_id")

                if not post_id:
                    raise ValidationError("Post ID is required for analysis")

                # Execute analyze action
                analytics = await adapter.analyze(post_id, **data.get("options", {}))

                # Store in database (update the post with analytics)
                post = self.db.query(PlatformPost).filter(
                    PlatformPost.platform_id == post_id,
                    PlatformPost.platform == platform,
                    PlatformPost.user_id == user_id
                ).first()

                if post:
                    post.analytics = analytics.dict()
                    post.analytics_updated_at = datetime.now()
                    self.db.commit()

                result = analytics.dict()
                result["post_id"] = post_id

            else:
                raise ValidationError(f"Unsupported action: {action}")

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record completion metric
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.INTEGRATION,
                    name=f"platform_action_complete_{platform}_{action}",
                    duration_ms=duration_ms,
                    metadata={
                        "user_id": user_id,
                        "platform": platform,
                        "action": action,
                        "success": True
                    }
                )

            # Log action
            logger.info(
                f"Platform action executed: {action}",
                user_id=user_id,
                platform=platform,
                action=action,
                duration_ms=duration_ms
            )

            return {
                "status": "success",
                "platform": platform,
                "action": action,
                "result": result,
                "duration_ms": duration_ms
            }

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record error metric
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.INTEGRATION,
                    name=f"platform_action_error_{platform}_{action}",
                    duration_ms=duration_ms,
                    metadata={
                        "user_id": user_id,
                        "platform": platform,
                        "action": action,
                        "error": str(e),
                        "error_type": e.__class__.__name__
                    },
                    success=False,
                    error=str(e)
                )

            # Log error
            logger.error(
                f"Platform action failed: {action}",
                user_id=user_id,
                platform=platform,
                action=action,
                error=str(e),
                error_type=e.__class__.__name__,
                duration_ms=duration_ms
            )

            # Re-raise the exception
            raise

    async def create_cross_platform_campaign(
        self,
        user_id: str,
        campaign_data: Dict[str, Any],
        platforms: List[PlatformType]
    ) -> Dict[str, Any]:
        """Create a unified campaign across multiple platforms.

        Args:
            user_id: User ID
            campaign_data: Campaign data
            platforms: Platforms to post to

        Returns:
            Campaign result

        Raises:
            ValidationError: If campaign data is invalid
            ResourceNotFoundError: If adapter not found
            IntegrationError: If campaign creation fails
        """
        start_time = time.time()

        try:
            # Validate required fields
            if "name" not in campaign_data:
                raise ValidationError("Campaign name is required")

            if "content" not in campaign_data:
                raise ValidationError("Campaign content is required")

            # Record metric
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.INTEGRATION,
                    name="cross_platform_campaign_start",
                    duration_ms=0,
                    metadata={
                        "user_id": user_id,
                        "platforms": [p.value for p in platforms],
                        "campaign_name": campaign_data["name"]
                    }
                )

            # Create campaign entity
            campaign = CrossPlatformCampaign(
                user_id=user_id,
                name=campaign_data["name"],
                platforms=[p.value for p in platforms],
                status="DRAFT",
                created_at=datetime.now()
            )

            self.db.add(campaign)
            self.db.flush()  # Get ID without committing

            # Generate platform-specific content using AI
            platform_contents = {}

            # In a real implementation, this would use an AI service
            # Here's a placeholder that just uses the same content for all platforms
            base_content = campaign_data["content"]

            for platform in platforms:
                if platform == PlatformType.LINKEDIN:
                    # LinkedIn posts should be more professional
                    platform_contents[platform] = {
                        "text": f"Professional update: {base_content}",
                        "title": campaign_data.get("title", "Professional Update"),
                        "description": campaign_data.get("description", ""),
                        "link_url": campaign_data.get("link_url"),
                        "media_urls": campaign_data.get("media_urls", [])
                    }
                elif platform == PlatformType.TWITTER:
                    # Twitter posts should be shorter
                    twitter_text = base_content
                    if len(twitter_text) > 280:
                        twitter_text = twitter_text[:277] + "..."

                    platform_contents[platform] = {
                        "text": twitter_text,
                        "media_urls": campaign_data.get("media_urls", []),
                        "link_url": campaign_data.get("link_url")
                    }
                elif platform == PlatformType.EMAIL:
                    # Email content should be more detailed
                    platform_contents[platform] = {
                        "text": base_content,
                        "html_content": f"<html><body><h1>{campaign_data.get('title', 'Update')}</h1><p>{base_content}</p></body></html>",
                        "title": campaign_data.get("title"),
                        "description": campaign_data.get("description"),
                        "media_urls": campaign_data.get("media_urls", []),
                        "link_url": campaign_data.get("link_url")
                    }
                else:
                    # Default content
                    platform_contents[platform] = {
                        "text": base_content,
                        "title": campaign_data.get("title"),
                        "description": campaign_data.get("description"),
                        "media_urls": campaign_data.get("media_urls", []),
                        "link_url": campaign_data.get("link_url")
                    }

            # Create platform-specific campaigns
            platform_campaigns = {}
            action = PlatformAction.SCHEDULE if campaign_data.get("schedule_time") else PlatformAction.POST

            for platform in platforms:
                try:
                    # Get platform-specific content
                    content = platform_contents.get(platform, campaign_data["content"])

                    # Create action data
                    action_data = {
                        "content": content,
                        "cross_platform_campaign_id": campaign.id
                    }

                    if campaign_data.get("schedule_time"):
                        action_data["schedule_time"] = campaign_data["schedule_time"]

                    # Add platform-specific options
                    if platform == PlatformType.EMAIL:
                        action_data["options"] = {
                            "recipients": campaign_data.get("recipients", []),
                            "subject": campaign_data.get("title", "Update")
                        }

                    # Execute platform action
                    platform_result = await self.execute_platform_action(
                        user_id=user_id,
                        platform=platform,
                        action=action,
                        data=action_data
                    )

                    platform_campaigns[platform.value] = platform_result

                except Exception as e:
                    logger.error(
                        f"Failed to create campaign for platform: {platform}",
                        user_id=user_id,
                        platform=platform,
                        error=str(e),
                        error_type=e.__class__.__name__
                    )

                    platform_campaigns[platform.value] = {
                        "status": "error",
                        "error": str(e),
                        "error_type": e.__class__.__name__
                    }

            # Update campaign status
            campaign.status = "ACTIVE" if any(pc.get("status") == "success" for pc in platform_campaigns.values()) else "FAILED"
            campaign.platform_data = platform_campaigns
            campaign.content = campaign_data.get("content")
            campaign.platform_contents = platform_contents

            self.db.commit()

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record completion metric
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.INTEGRATION,
                    name="cross_platform_campaign_complete",
                    duration_ms=duration_ms,
                    metadata={
                        "user_id": user_id,
                        "platforms": [p.value for p in platforms],
                        "campaign_name": campaign_data["name"],
                        "campaign_id": campaign.id,
                        "status": campaign.status
                    }
                )

            # Log campaign creation
            logger.info(
                "Cross-platform campaign created",
                user_id=user_id,
                platforms=[p.value for p in platforms],
                campaign_id=campaign.id,
                status=campaign.status,
                duration_ms=duration_ms
            )

            return {
                "status": "success",
                "campaign_id": campaign.id,
                "campaign_status": campaign.status,
                "platform_campaigns": platform_campaigns
            }

        except Exception as e:
            # Rollback transaction
            self.db.rollback()

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record error metric
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.INTEGRATION,
                    name="cross_platform_campaign_error",
                    duration_ms=duration_ms,
                    metadata={
                        "user_id": user_id,
                        "platforms": [p.value for p in platforms],
                        "campaign_name": campaign_data.get("name", "Unknown"),
                        "error": str(e),
                        "error_type": e.__class__.__name__
                    },
                    success=False,
                    error=str(e)
                )

            # Log error
            logger.error(
                "Cross-platform campaign creation failed",
                user_id=user_id,
                platforms=[p.value for p in platforms],
                error=str(e),
                error_type=e.__class__.__name__,
                duration_ms=duration_ms
            )

            # Re-raise the exception
            raise

    async def get_unified_analytics(
        self,
        campaign_id: int,
        refresh: bool = False
    ) -> Dict[str, Any]:
        """Get unified analytics across all platforms for a campaign.

        Args:
            campaign_id: Campaign ID
            refresh: Whether to refresh analytics from platforms

        Returns:
            Unified analytics data

        Raises:
            ResourceNotFoundError: If campaign not found
            IntegrationError: If analytics retrieval fails
        """
        start_time = time.time()

        try:
            # Try cache first if not refreshing
            if not refresh and self.cache:
                cache_key = f"analytics:campaign:{campaign_id}"
                cached = self.cache.get(cache_key)

                if cached:
                    return cached

            # Get campaign
            campaign = self.db.query(CrossPlatformCampaign).filter(
                CrossPlatformCampaign.id == campaign_id
            ).first()

            if not campaign:
                raise ResourceNotFoundError(f"Campaign {campaign_id} not found")

            # Get all posts for this campaign
            posts = self.db.query(PlatformPost).filter(
                PlatformPost.cross_platform_campaign_id == campaign_id
            ).all()

            if not posts:
                return {
                    "campaign_id": campaign_id,
                    "platforms": campaign.platforms,
                    "total_engagements": 0,
                    "total_impressions": 0,
                    "total_clicks": 0,
                    "platform_analytics": {},
                    "refreshed_at": datetime.now().isoformat()
                }

            # Refresh analytics for each post if requested
            if refresh:
                for post in posts:
                    try:
                        # Get platform adapter
                        adapter = self._get_adapter(campaign.user_id, PlatformType(post.platform))

                        if not adapter:
                            continue

                        # Get updated analytics
                        analytics = await adapter.analyze(post.platform_id)

                        # Update post
                        post.analytics = analytics.dict()
                        post.analytics_updated_at = datetime.now()

                    except Exception as e:
                        logger.error(
                            f"Failed to refresh analytics for post",
                            campaign_id=campaign_id,
                            post_id=post.id,
                            platform=post.platform,
                            error=str(e),
                            error_type=e.__class__.__name__
                        )

                # Commit changes
                self.db.commit()

            # Aggregate analytics by platform
            platform_analytics = {}
            total_impressions = 0
            total_engagements = 0
            total_clicks = 0

            for post in posts:
                if not post.analytics:
                    continue

                platform = post.platform

                if platform not in platform_analytics:
                    platform_analytics[platform] = {
                        "impressions": 0,
                        "engagements": 0,
                        "clicks": 0,
                        "likes": 0,
                        "shares": 0,
                        "comments": 0,
                        "conversions": 0,
                        "platform_specific": {}
                    }

                # Add metrics
                platform_analytics[platform]["impressions"] += post.analytics.get("impressions", 0)
                platform_analytics[platform]["engagements"] += post.analytics.get("engagements", 0)
                platform_analytics[platform]["clicks"] += post.analytics.get("clicks", 0)
                platform_analytics[platform]["likes"] += post.analytics.get("likes", 0)
                platform_analytics[platform]["shares"] += post.analytics.get("shares", 0)
                platform_analytics[platform]["comments"] += post.analytics.get("comments", 0)
                platform_analytics[platform]["conversions"] += post.analytics.get("conversions", 0)

                # Merge platform-specific data
                platform_specific = post.analytics.get("platform_specific", {})

                for key, value in platform_specific.items():
                    if key not in platform_analytics[platform]["platform_specific"]:
                        platform_analytics[platform]["platform_specific"][key] = value
                    elif isinstance(value, (int, float)):
                        platform_analytics[platform]["platform_specific"][key] = platform_analytics[platform]["platform_specific"].get(key, 0) + value

                # Add to totals
                total_impressions += post.analytics.get("impressions", 0)
                total_engagements += post.analytics.get("engagements", 0)
                total_clicks += post.analytics.get("clicks", 0)

            # Calculate engagement rate
            engagement_rate = (total_engagements / total_impressions) if total_impressions > 0 else 0

            # Create result
            result = {
                "campaign_id": campaign_id,
                "platforms": campaign.platforms,
                "total_impressions": total_impressions,
                "total_engagements": total_engagements,
                "total_clicks": total_clicks,
                "engagement_rate": engagement_rate,
                "platform_analytics": platform_analytics,
                "refreshed_at": datetime.now().isoformat()
            }

            # Cache result
            if self.cache:
                cache_key = f"analytics:campaign:{campaign_id}"
                self.cache.set(
                    key=cache_key,
                    value=result,
                    data_type="analytics",
                    tier=CacheTier.FREQUENT
                )

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record metric
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.INTEGRATION,
                    name="unified_analytics",
                    duration_ms=duration_ms,
                    metadata={
                        "campaign_id": campaign_id,
                        "platforms": campaign.platforms,
                        "refresh": refresh
                    }
                )

            return result

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record error metric
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.INTEGRATION,
                    name="unified_analytics_error",
                    duration_ms=duration_ms,
                    metadata={
                        "campaign_id": campaign_id,
                        "error": str(e),
                        "error_type": e.__class__.__name__
                    },
                    success=False,
                    error=str(e)
                )

            # Log error
            logger.error(
                "Failed to get unified analytics",
                campaign_id=campaign_id,
                error=str(e),
                error_type=e.__class__.__name__,
                duration_ms=duration_ms
            )

            # Re-raise the exception
            raise
