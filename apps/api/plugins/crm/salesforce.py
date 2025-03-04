from typing import Any, Dict, List, Optional
from simple_salesforce import Salesforce
from ..base import BasePlugin, PluginMetadata

class SalesforcePlugin(BasePlugin):
    """Salesforce CRM integration plugin."""

    def __init__(self):
        self._client: Optional[Salesforce] = None

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="salesforce",
            version="1.0.0",
            description="Salesforce CRM integration for Maily",
            author="Maily Team",
            website="https://justmaily.com/plugins/salesforce",
            dependencies=["simple-salesforce>=1.12.0"],
            settings_schema={
                "username": {"type": "string", "required": True},
                "password": {"type": "string", "required": True},
                "security_token": {"type": "string", "required": True},
                "domain": {"type": "string", "default": "login"},
            }
        )

    async def initialize(self, settings: Dict[str, Any]) -> None:
        """Initialize Salesforce connection."""
        try:
            self._client = Salesforce(
                username=settings["username"],
                password=settings["password"],
                security_token=settings["security_token"],
                domain=settings.get("domain", "login")
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Salesforce: {str(e)}")

    async def cleanup(self) -> None:
        """Clean up Salesforce connection."""
        if self._client:
            self._client.session.close()
            self._client = None

    async def validate_settings(self, settings: Dict[str, Any]) -> bool:
        """Validate Salesforce connection settings."""
        required_fields = ["username", "password", "security_token"]
        return all(field in settings for field in required_fields)

    async def sync_contacts(self) -> List[Dict[str, Any]]:
        """Sync contacts from Salesforce."""
        if not self._client:
            raise RuntimeError("Salesforce client not initialized")

        try:
            query = """
                SELECT Id, Email, FirstName, LastName, Title,
                       Company, Phone, MailingCity, MailingCountry,
                       HasOptedOutOfEmail, EmailBouncedReason
                FROM Contact
                WHERE Email != null
                AND HasOptedOutOfEmail = false
                AND EmailBouncedReason = null
            """

            result = self._client.query_all(query)
            return [record for record in result["records"]]

        except Exception as e:
            raise RuntimeError(f"Failed to sync contacts: {str(e)}")

    async def update_campaign_stats(
        self,
        campaign_id: str,
        stats: Dict[str, Any]
    ) -> None:
        """Update campaign statistics in Salesforce."""
        if not self._client:
            raise RuntimeError("Salesforce client not initialized")

        try:
            self._client.Campaign.update(campaign_id, {
                "NumberSent__c": stats.get("sent", 0),
                "NumberOpened__c": stats.get("opened", 0),
                "NumberClicked__c": stats.get("clicked", 0),
                "NumberBounced__c": stats.get("bounced", 0),
                "NumberUnsubscribed__c": stats.get("unsubscribed", 0)
            })
        except Exception as e:
            raise RuntimeError(f"Failed to update campaign stats: {str(e)}")

    async def create_campaign(
        self,
        name: str,
        description: str,
        start_date: str,
        end_date: str
    ) -> str:
        """Create a new campaign in Salesforce."""
        if not self._client:
            raise RuntimeError("Salesforce client not initialized")

        try:
            result = self._client.Campaign.create({
                "Name": name,
                "Description": description,
                "StartDate": start_date,
                "EndDate": end_date,
                "Type": "Email",
                "Status": "Planned"
            })

            return result["id"]

        except Exception as e:
            raise RuntimeError(f"Failed to create campaign: {str(e)}")

    async def log_email_event(
        self,
        contact_id: str,
        campaign_id: str,
        event_type: str,
        details: Dict[str, Any]
    ) -> None:
        """Log email interaction events in Salesforce."""
        if not self._client:
            raise RuntimeError("Salesforce client not initialized")

        try:
            self._client.EmailEvent__c.create({
                "Contact__c": contact_id,
                "Campaign__c": campaign_id,
                "EventType__c": event_type,
                "EventDate__c": details.get("timestamp"),
                "Details__c": str(details)
            })
        except Exception as e:
            raise RuntimeError(f"Failed to log email event: {str(e)}")

    async def get_contact_preferences(
        self,
        contact_id: str
    ) -> Dict[str, Any]:
        """Get contact email preferences from Salesforce."""
        if not self._client:
            raise RuntimeError("Salesforce client not initialized")

        try:
            result = self._client.Contact.get(contact_id)
            return {
                "opted_out": result["HasOptedOutOfEmail"],
                "bounce_reason": result["EmailBouncedReason"],
                "last_modified": result["LastModifiedDate"],
                "email_format": result.get("PreferredEmailFormat__c", "html")
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get contact preferences: {str(e)}")
