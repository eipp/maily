from typing import Dict, Any, List, Optional
import logging
import json
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class IdentityResolutionService:
    """
    Service for resolving identities across different platforms.

    This service provides methods for matching contacts across different platforms,
    creating a unified view of contacts, and assigning confidence scores to matches.

    Even with Nango handling the platform integrations, identity resolution remains
    a critical component unique to Maily that adds significant value.
    """

    def __init__(self):
        # Initialize with default confidence thresholds
        self.exact_match_threshold = 0.9
        self.high_confidence_threshold = 0.7
        self.medium_confidence_threshold = 0.5

        # Map of normalization rules for different platforms
        self.normalization_rules = {
            "linkedin": {
                "name_fields": ["first_name", "last_name"],
                "email_fields": ["email"],
                "phone_fields": ["phone"],
                "company_fields": ["company"],
                "title_fields": ["title"]
            },
            "twitter": {
                "name_fields": ["name"],
                "username_fields": ["username"],
                "bio_fields": ["description"]
            },
            "gmail": {
                "name_fields": ["name"],
                "email_fields": ["email"],
                "phone_fields": ["phone"]
            },
            "outlook": {
                "name_fields": ["name"],
                "email_fields": ["email"],
                "phone_fields": ["phone"],
                "company_fields": ["company"],
                "title_fields": ["title"]
            }
        }

    async def resolve_identities(
        self,
        user_id: str,
        platform: str,
        contacts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Resolve identities across different platforms.

        Args:
            user_id: User ID to resolve identities for
            platform: Platform the contacts are from
            contacts: List of contacts to resolve

        Returns:
            List of contacts with resolved identities
        """
        try:
            # Get existing global identities for the user
            global_identities = await self._get_global_identities(user_id)

            # Normalize contacts based on platform
            normalized_contacts = self._normalize_contacts(platform, contacts)

            # Match contacts with global identities
            resolved_contacts = []
            for contact in normalized_contacts:
                # Try to find a match in global identities
                match_result = self._find_best_match(contact, global_identities)

                if match_result["match_found"]:
                    # Add global identity information to contact
                    contact["global_identity"] = {
                        "id": match_result["global_id"],
                        "confidence": match_result["confidence"],
                        "match_type": match_result["match_type"]
                    }
                else:
                    # Create a new global identity
                    global_id = self._generate_global_id(contact)
                    contact["global_identity"] = {
                        "id": global_id,
                        "confidence": 1.0,
                        "match_type": "new"
                    }

                    # Add to global identities
                    global_identities.append({
                        "id": global_id,
                        "platforms": {
                            platform: {
                                "id": contact.get("id", ""),
                                "name": self._get_full_name(contact, platform),
                                "email": self._get_primary_email(contact, platform),
                                "phone": self._get_primary_phone(contact, platform)
                            }
                        },
                        "primary_name": self._get_full_name(contact, platform),
                        "primary_email": self._get_primary_email(contact, platform),
                        "primary_phone": self._get_primary_phone(contact, platform)
                    })

                resolved_contacts.append(contact)

            # Update global identities
            await self._update_global_identities(user_id, global_identities)

            return resolved_contacts
        except Exception as e:
            logger.error(f"Error resolving identities: {str(e)}")
            # Don't raise an exception, just return the original contacts
            # This ensures the application continues to function even if identity resolution fails
            return contacts

    async def _get_global_identities(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get global identities for a user.

        In a real implementation, this would fetch from a database.
        For this example, we'll return an empty list.

        Args:
            user_id: User ID to get global identities for

        Returns:
            List of global identities
        """
        # In a real implementation, this would fetch from a database
        # For this example, we'll return an empty list
        return []

    async def _update_global_identities(self, user_id: str, global_identities: List[Dict[str, Any]]) -> None:
        """
        Update global identities for a user.

        In a real implementation, this would update a database.
        For this example, we'll just log the update.

        Args:
            user_id: User ID to update global identities for
            global_identities: List of global identities to update
        """
        # In a real implementation, this would update a database
        # For this example, we'll just log the update
        logger.info(f"Updated {len(global_identities)} global identities for user {user_id}")

    def _normalize_contacts(self, platform: str, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize contacts based on platform.

        Args:
            platform: Platform the contacts are from
            contacts: List of contacts to normalize

        Returns:
            List of normalized contacts
        """
        normalized_contacts = []

        for contact in contacts:
            # Create a copy of the contact to avoid modifying the original
            normalized_contact = contact.copy()

            # Add platform information
            normalized_contact["_platform"] = platform

            # Normalize name fields
            normalized_contact["_normalized_name"] = self._normalize_name(contact, platform)

            # Normalize email fields
            normalized_contact["_normalized_email"] = self._normalize_email(contact, platform)

            # Normalize phone fields
            normalized_contact["_normalized_phone"] = self._normalize_phone(contact, platform)

            normalized_contacts.append(normalized_contact)

        return normalized_contacts

    def _normalize_name(self, contact: Dict[str, Any], platform: str) -> str:
        """
        Normalize name fields for a contact.

        Args:
            contact: Contact to normalize name for
            platform: Platform the contact is from

        Returns:
            Normalized name
        """
        name_fields = self.normalization_rules.get(platform, {}).get("name_fields", [])

        # Special case for platforms with first_name and last_name
        if "first_name" in name_fields and "last_name" in name_fields:
            first_name = contact.get("first_name", "").strip().lower()
            last_name = contact.get("last_name", "").strip().lower()
            return f"{first_name} {last_name}".strip()

        # For platforms with a single name field
        for field in name_fields:
            if field in contact and contact[field]:
                return contact[field].strip().lower()

        return ""

    def _normalize_email(self, contact: Dict[str, Any], platform: str) -> str:
        """
        Normalize email fields for a contact.

        Args:
            contact: Contact to normalize email for
            platform: Platform the contact is from

        Returns:
            Normalized email
        """
        email_fields = self.normalization_rules.get(platform, {}).get("email_fields", [])

        for field in email_fields:
            if field in contact and contact[field]:
                return contact[field].strip().lower()

        return ""

    def _normalize_phone(self, contact: Dict[str, Any], platform: str) -> str:
        """
        Normalize phone fields for a contact.

        Args:
            contact: Contact to normalize phone for
            platform: Platform the contact is from

        Returns:
            Normalized phone
        """
        phone_fields = self.normalization_rules.get(platform, {}).get("phone_fields", [])

        for field in phone_fields:
            if field in contact and contact[field]:
                # Remove all non-numeric characters
                return ''.join(filter(str.isdigit, contact[field]))

        return ""

    def _find_best_match(
        self,
        contact: Dict[str, Any],
        global_identities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Find the best match for a contact in global identities.

        Args:
            contact: Contact to find a match for
            global_identities: List of global identities to search

        Returns:
            Match result
        """
        best_match = {
            "match_found": False,
            "global_id": None,
            "confidence": 0.0,
            "match_type": None
        }

        # Get normalized fields
        normalized_name = contact.get("_normalized_name", "")
        normalized_email = contact.get("_normalized_email", "")
        normalized_phone = contact.get("_normalized_phone", "")

        # Skip if no identifying information
        if not normalized_name and not normalized_email and not normalized_phone:
            return best_match

        for identity in global_identities:
            # Check for exact email match (highest confidence)
            if normalized_email and normalized_email == identity.get("primary_email", "").lower():
                best_match["match_found"] = True
                best_match["global_id"] = identity["id"]
                best_match["confidence"] = 0.95
                best_match["match_type"] = "email_exact"
                return best_match

            # Check for exact phone match (high confidence)
            if normalized_phone and normalized_phone == ''.join(filter(str.isdigit, identity.get("primary_phone", ""))):
                best_match["match_found"] = True
                best_match["global_id"] = identity["id"]
                best_match["confidence"] = 0.9
                best_match["match_type"] = "phone_exact"
                return best_match

            # Check for exact name match (medium confidence)
            if normalized_name and normalized_name == identity.get("primary_name", "").lower():
                best_match["match_found"] = True
                best_match["global_id"] = identity["id"]
                best_match["confidence"] = 0.7
                best_match["match_type"] = "name_exact"
                return best_match

        return best_match

    def _generate_global_id(self, contact: Dict[str, Any]) -> str:
        """
        Generate a global ID for a contact.

        In a real implementation, this would generate a unique ID.
        For this example, we'll use a simple hash of the contact.

        Args:
            contact: Contact to generate a global ID for

        Returns:
            Global ID
        """
        # In a real implementation, this would generate a unique ID
        # For this example, we'll use a simple hash of the contact
        platform = contact.get("_platform", "unknown")
        contact_id = contact.get("id", "")
        name = contact.get("_normalized_name", "")
        email = contact.get("_normalized_email", "")

        return f"global_{platform}_{contact_id}_{hash(name + email) % 10000:04d}"

    def _get_full_name(self, contact: Dict[str, Any], platform: str) -> str:
        """
        Get the full name for a contact.

        Args:
            contact: Contact to get full name for
            platform: Platform the contact is from

        Returns:
            Full name
        """
        # Special case for platforms with first_name and last_name
        if platform == "linkedin":
            first_name = contact.get("first_name", "")
            last_name = contact.get("last_name", "")
            return f"{first_name} {last_name}".strip()

        # For platforms with a single name field
        name_fields = self.normalization_rules.get(platform, {}).get("name_fields", [])
        for field in name_fields:
            if field in contact and contact[field]:
                return contact[field]

        return ""

    def _get_primary_email(self, contact: Dict[str, Any], platform: str) -> str:
        """
        Get the primary email for a contact.

        Args:
            contact: Contact to get primary email for
            platform: Platform the contact is from

        Returns:
            Primary email
        """
        email_fields = self.normalization_rules.get(platform, {}).get("email_fields", [])

        for field in email_fields:
            if field in contact and contact[field]:
                return contact[field]

        return ""

    def _get_primary_phone(self, contact: Dict[str, Any], platform: str) -> str:
        """
        Get the primary phone for a contact.

        Args:
            contact: Contact to get primary phone for
            platform: Platform the contact is from

        Returns:
            Primary phone
        """
        phone_fields = self.normalization_rules.get(platform, {}).get("phone_fields", [])

        for field in phone_fields:
            if field in contact and contact[field]:
                return contact[field]

        return ""
