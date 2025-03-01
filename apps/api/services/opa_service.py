do i have any inconcistencies?
"""Open Policy Agent (OPA) service for authorization."""
import json
import logging
from typing import Any, Dict, List, Optional, Union

import requests
from fastapi import HTTPException, status

from config.opa import opa_settings

logger = logging.getLogger(__name__)


class OPAService:
    """Service for interacting with Open Policy Agent."""

    def __init__(self):
        """Initialize the OPA service."""
        self.url = opa_settings.URL
        self.policy_path = opa_settings.POLICY_PATH
        self.timeout = opa_settings.TIMEOUT

    async def check_permission(
        self,
        user: Dict[str, Any],
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check if a user has permission to perform an action on a resource.

        Args:
            user: The user information.
            action: The action to perform.
            resource: The resource type.
            resource_id: The resource ID.
            context: Additional context for the authorization decision.

        Returns:
            True if the user has permission, False otherwise.

        Raises:
            HTTPException: If the OPA service cannot be reached.
        """
        input_data = {
            "input": {
                "user": user,
                "action": action,
                "resource": resource,
                "resource_id": resource_id,
                "context": context or {},
            }
        }

        try:
            response = requests.post(
                f"{self.url}/{self.policy_path}",
                json=input_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            # OPA returns a result with a "result" field that contains the policy decision
            return result.get("result", {}).get("allow", False)
        except requests.RequestException as e:
            logger.error(f"Failed to check permission with OPA: {str(e)}")
            # In case of OPA service failure, deny access by default
            return False

    async def get_allowed_resources(
        self,
        user: Dict[str, Any],
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Get the resources that a user has permission to perform an action on.

        Args:
            user: The user information.
            action: The action to perform.
            resource: The resource type.
            context: Additional context for the authorization decision.

        Returns:
            A list of resource IDs that the user has permission to access.

        Raises:
            HTTPException: If the OPA service cannot be reached.
        """
        input_data = {
            "input": {
                "user": user,
                "action": action,
                "resource": resource,
                "context": context or {},
            }
        }

        try:
            response = requests.post(
                f"{self.url}/{self.policy_path}/allowed_resources",
                json=input_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            # OPA returns a result with a "result" field that contains the allowed resources
            return result.get("result", {}).get("allowed_resources", [])
        except requests.RequestException as e:
            logger.error(f"Failed to get allowed resources from OPA: {str(e)}")
            # In case of OPA service failure, return an empty list
            return []

    async def check_bulk_permissions(
        self,
        user: Dict[str, Any],
        permissions: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """Check multiple permissions at once.

        Args:
            user: The user information.
            permissions: A list of permission requests, each with action, resource, and resource_id.
            context: Additional context for the authorization decision.

        Returns:
            A dictionary mapping permission keys to boolean results.

        Raises:
            HTTPException: If the OPA service cannot be reached.
        """
        input_data = {
            "input": {
                "user": user,
                "permissions": permissions,
                "context": context or {},
            }
        }

        try:
            response = requests.post(
                f"{self.url}/{self.policy_path}/bulk",
                json=input_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            # OPA returns a result with a "result" field that contains the permission decisions
            return result.get("result", {}).get("decisions", {})
        except requests.RequestException as e:
            logger.error(f"Failed to check bulk permissions with OPA: {str(e)}")
            # In case of OPA service failure, deny all permissions by default
            return {f"{p['action']}:{p['resource']}:{p.get('resource_id', '')}" : False for p in permissions}

    async def upload_policy(self, policy_name: str, policy_content: str) -> bool:
        """Upload a policy to OPA.

        Args:
            policy_name: The name of the policy.
            policy_content: The Rego policy content.

        Returns:
            True if the policy was uploaded successfully.

        Raises:
            HTTPException: If the policy cannot be uploaded.
        """
        try:
            response = requests.put(
                f"{self.url}/v1/policies/{policy_name}",
                data=policy_content,
                headers={"Content-Type": "text/plain"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to upload policy to OPA: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to upload policy to OPA: {str(e)}",
            )

    async def get_policy(self, policy_name: str) -> str:
        """Get a policy from OPA.

        Args:
            policy_name: The name of the policy.

        Returns:
            The policy content.

        Raises:
            HTTPException: If the policy cannot be retrieved.
        """
        try:
            response = requests.get(
                f"{self.url}/v1/policies/{policy_name}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to get policy from OPA: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy not found: {policy_name}",
            )

    async def delete_policy(self, policy_name: str) -> bool:
        """Delete a policy from OPA.

        Args:
            policy_name: The name of the policy.

        Returns:
            True if the policy was deleted successfully.

        Raises:
            HTTPException: If the policy cannot be deleted.
        """
        try:
            response = requests.delete(
                f"{self.url}/v1/policies/{policy_name}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to delete policy from OPA: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy not found: {policy_name}",
            )


# Create a singleton instance
opa_service = OPAService()
