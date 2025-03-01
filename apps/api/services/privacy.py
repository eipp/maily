import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..config import Settings
from ..database import Database
from ..models.privacy import (
    ConsentLog,
    ConsentPreferences,
    DataDeletionRequest,
    DataExportRequest,
    RequestStatus,
)
from ..utils.encryption import EncryptionManager
from ..utils.storage import StorageManager

logger = logging.getLogger(__name__)


class PrivacyService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db = Database(settings)
        self.storage = StorageManager(settings)
        self.encryption = EncryptionManager(settings)

    async def get_consent_preferences(self, user_id: str) -> ConsentPreferences:
        """
        Retrieve the current consent preferences for a user.

        Args:
            user_id: The ID of the user

        Returns:
            ConsentPreferences: The user's current privacy preferences
        """
        try:
            preferences = await self.db.find_one(
                "consent_preferences", {"user_id": user_id}
            )
            if not preferences:
                # Return default preferences if none exist
                return ConsentPreferences(user_id=user_id)
            return ConsentPreferences(**preferences)
        except Exception as e:
            logger.error(f"Error getting consent preferences: {str(e)}")
            raise

    async def update_consent_preferences(
        self,
        user_id: str,
        preferences: Dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ConsentPreferences:
        """
        Update a user's consent preferences and log the change.

        Args:
            user_id: The ID of the user
            preferences: New consent preferences
            ip_address: Optional IP address of the request
            user_agent: Optional user agent string

        Returns:
            ConsentPreferences: Updated preferences
        """
        try:
            # Get current preferences for logging
            current_prefs = await self.get_consent_preferences(user_id)

            # Create new preferences object
            new_prefs = ConsentPreferences(
                user_id=user_id,
                **preferences,
                ip_address=ip_address,
                user_agent=user_agent,
                last_updated=datetime.utcnow(),
            )

            # Save to database
            await self.db.update_one(
                "consent_preferences",
                {"user_id": user_id},
                new_prefs.dict(),
                upsert=True,
            )

            # Log the change
            log = ConsentLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action="update",
                preferences_before=current_prefs.dict(),
                preferences_after=new_prefs.dict(),
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self.db.insert_one("consent_logs", log.dict())

            return new_prefs
        except Exception as e:
            logger.error(f"Error updating consent preferences: {str(e)}")
            raise

    async def create_deletion_request(
        self, user_id: str, execution_date: datetime, reason: Optional[str] = None
    ) -> DataDeletionRequest:
        """
        Create a new data deletion request.

        Args:
            user_id: The ID of the user
            execution_date: When to execute the deletion
            reason: Optional reason for deletion

        Returns:
            DataDeletionRequest: The created request
        """
        try:
            request = DataDeletionRequest(
                id=str(uuid.uuid4()),
                user_id=user_id,
                execution_date=execution_date,
                reason=reason,
                data_categories=["personal_info", "analytics", "campaigns"],
            )

            await self.db.insert_one("deletion_requests", request.dict())
            return request
        except Exception as e:
            logger.error(f"Error creating deletion request: {str(e)}")
            raise

    async def execute_deletion_request(self, request_id: str):
        """
        Execute a pending data deletion request.

        Args:
            request_id: The ID of the deletion request
        """
        try:
            request = await self.get_deletion_request(request_id)

            # Update status to processing
            await self.db.update_one(
                "deletion_requests",
                {"id": request_id},
                {"$set": {"status": RequestStatus.PROCESSING}},
            )

            # Delete user data from various collections
            await self._delete_user_data(request.user_id)

            # Update request status
            await self.db.update_one(
                "deletion_requests",
                {"id": request_id},
                {
                    "$set": {
                        "status": RequestStatus.COMPLETED,
                        "completed_date": datetime.utcnow(),
                    }
                },
            )
        except Exception as e:
            logger.error(f"Error executing deletion request: {str(e)}")
            await self.db.update_one(
                "deletion_requests",
                {"id": request_id},
                {"$set": {"status": RequestStatus.FAILED}},
            )
            raise

    async def _delete_user_data(self, user_id: str):
        """
        Delete all data associated with a user.

        Args:
            user_id: The ID of the user
        """
        collections = [
            "users",
            "campaigns",
            "analytics",
            "consent_preferences",
            "consent_logs",
        ]

        for collection in collections:
            await self.db.delete_many(collection, {"user_id": user_id})

        # Delete files from storage
        await self.storage.delete_user_files(user_id)

    async def get_deletion_request(self, request_id: str) -> DataDeletionRequest:
        """
        Get the status of a deletion request.

        Args:
            request_id: The ID of the deletion request

        Returns:
            DataDeletionRequest: The deletion request details
        """
        try:
            request = await self.db.find_one("deletion_requests", {"id": request_id})
            if not request:
                raise ValueError(f"Deletion request {request_id} not found")
            return DataDeletionRequest(**request)
        except Exception as e:
            logger.error(f"Error getting deletion request: {str(e)}")
            raise

    async def create_export_request(self, user_id: str) -> DataExportRequest:
        """
        Create a new data export request.

        Args:
            user_id: The ID of the user

        Returns:
            DataExportRequest: The created export request
        """
        try:
            request = DataExportRequest(
                id=str(uuid.uuid4()),
                user_id=user_id,
                data_categories=["personal_info", "campaigns", "analytics"],
            )

            await self.db.insert_one("export_requests", request.dict())
            return request
        except Exception as e:
            logger.error(f"Error creating export request: {str(e)}")
            raise

    async def generate_data_export(self, request_id: str):
        """
        Generate a data export for a user.

        Args:
            request_id: The ID of the export request
        """
        try:
            request = await self.get_export_request(request_id)

            # Update status to processing
            await self.db.update_one(
                "export_requests",
                {"id": request_id},
                {"$set": {"status": RequestStatus.PROCESSING}},
            )

            # Collect user data
            data = await self._collect_user_data(request.user_id)

            # Generate export file
            file_name = f"export_{request_id}.json"
            encrypted_data = self.encryption.encrypt(json.dumps(data))

            # Upload to storage
            download_url = await self.storage.upload_export(file_name, encrypted_data)

            # Set expiry date (7 days from now)
            expiry_date = datetime.utcnow() + timedelta(days=7)

            # Update request
            await self.db.update_one(
                "export_requests",
                {"id": request_id},
                {
                    "$set": {
                        "status": RequestStatus.COMPLETED,
                        "completed_date": datetime.utcnow(),
                        "download_url": download_url,
                        "expiry_date": expiry_date,
                    }
                },
            )
        except Exception as e:
            logger.error(f"Error generating data export: {str(e)}")
            await self.db.update_one(
                "export_requests",
                {"id": request_id},
                {"$set": {"status": RequestStatus.FAILED}},
            )
            raise

    async def _collect_user_data(self, user_id: str) -> Dict:
        """
        Collect all data associated with a user.

        Args:
            user_id: The ID of the user

        Returns:
            Dict: Collected user data
        """
        data = {
            "personal_info": await self.db.find_one("users", {"id": user_id}),
            "campaigns": await self.db.find("campaigns", {"user_id": user_id}),
            "analytics": await self.db.find("analytics", {"user_id": user_id}),
            "consent_preferences": await self.get_consent_preferences(user_id),
            "consent_logs": await self.get_consent_logs(user_id),
        }
        return data

    async def get_export_request(self, request_id: str) -> DataExportRequest:
        """
        Get the status of an export request.

        Args:
            request_id: The ID of the export request

        Returns:
            DataExportRequest: The export request details
        """
        try:
            request = await self.db.find_one("export_requests", {"id": request_id})
            if not request:
                raise ValueError(f"Export request {request_id} not found")
            return DataExportRequest(**request)
        except Exception as e:
            logger.error(f"Error getting export request: {str(e)}")
            raise

    async def get_consent_logs(self, user_id: str) -> List[ConsentLog]:
        """
        Get the consent change history for a user.

        Args:
            user_id: The ID of the user

        Returns:
            List[ConsentLog]: History of consent changes
        """
        try:
            logs = await self.db.find(
                "consent_logs", {"user_id": user_id}, sort=[("timestamp", -1)]
            )
            return [ConsentLog(**log) for log in logs]
        except Exception as e:
            logger.error(f"Error getting consent logs: {str(e)}")
            raise

    async def anonymize_user_data(self, user_id: str):
        """
        Anonymize a user's personal data while preserving analytics data.

        Args:
            user_id: The ID of the user
        """
        try:
            # Generate anonymous identifier
            anon_id = f"anon_{str(uuid.uuid4())}"

            # Update user document
            await self.db.update_one(
                "users",
                {"id": user_id},
                {
                    "$set": {
                        "email": f"{anon_id}@anonymous.com",
                        "name": "Anonymous User",
                        "is_anonymized": True,
                        "anonymized_date": datetime.utcnow(),
                    },
                    "$unset": {
                        "phone": "",
                        "address": "",
                        "company": "",
                        "social_profiles": "",
                    },
                },
            )

            # Anonymize campaign data
            await self.db.update_many(
                "campaigns",
                {"user_id": user_id},
                {"$set": {"creator_name": "Anonymous User", "is_anonymized": True}},
            )

            # Keep analytics data but remove personal identifiers
            await self.db.update_many(
                "analytics",
                {"user_id": user_id},
                {
                    "$set": {"user_identifier": anon_id, "is_anonymized": True},
                    "$unset": {"email": "", "name": "", "device_id": ""},
                },
            )

            logger.info(f"Successfully anonymized data for user {user_id}")
        except Exception as e:
            logger.error(f"Error anonymizing user data: {str(e)}")
            raise

    async def delete_user_cookies(self, user_id: str):
        """
        Delete all non-essential cookies for a user.

        Args:
            user_id: The ID of the user
        """
        try:
            # Update consent preferences to disable all non-essential cookies
            await self.update_consent_preferences(
                user_id=user_id,
                preferences={
                    "essential": True,  # Keep essential cookies
                    "functional": False,
                    "analytics": False,
                    "marketing": False,
                    "notification_preferences": {},
                },
            )

            # Additional cleanup if needed
            # This would depend on how cookies are actually stored/managed

            logger.info(
                f"Successfully deleted non-essential cookies for user {user_id}"
            )
        except Exception as e:
            logger.error(f"Error deleting user cookies: {str(e)}")
            raise
