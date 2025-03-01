"""Database repository for MailyDocs documents."""

import logging
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from db.base import BaseRepository
from core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class DocumentsRepository(BaseRepository):
    """Repository for document storage and management."""

    async def create_document(self, document_data: Dict[str, Any]) -> str:
        """Create a new document record.

        Args:
            document_data: Document data

        Returns:
            Document ID
        """
        required_fields = ["id", "type", "title", "status"]
        for field in required_fields:
            if field not in document_data:
                raise ValueError(f"Missing required field: {field}")

        try:
            # Add timestamps
            document_data["created_at"] = document_data.get("created_at", datetime.utcnow().isoformat() + "Z")
            document_data["updated_at"] = document_data["created_at"]

            # Insert document
            query = """
                INSERT INTO documents (
                    id, type, title, status, file_path, file_url, preview_url,
                    template_id, user_id, campaign_id, tracking_id,
                    personalized, interactive, blockchain_verified,
                    verification_url, verification_info, metadata,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
                )
                RETURNING id
            """

            values = (
                document_data["id"],
                document_data["type"],
                document_data["title"],
                document_data["status"],
                document_data.get("file_path"),
                document_data.get("file_url"),
                document_data.get("preview_url"),
                document_data.get("template_id"),
                document_data.get("user_id"),
                document_data.get("campaign_id"),
                document_data.get("tracking_id"),
                document_data.get("personalized", False),
                document_data.get("interactive", False),
                document_data.get("blockchain_verified", False),
                document_data.get("verification_url"),
                json.dumps(document_data.get("verification_info", {})) if document_data.get("verification_info") else None,
                json.dumps(document_data.get("metadata", {})),
                document_data["created_at"],
                document_data["updated_at"]
            )

            result = await self.db.fetchrow(query, *values)
            return result["id"]

        except Exception as e:
            logger.error(f"Failed to create document: {str(e)}")
            raise DatabaseError(f"Failed to create document: {str(e)}")

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document data or None if not found
        """
        try:
            query = """
                SELECT * FROM documents
                WHERE id = $1
            """

            result = await self.db.fetchrow(query, document_id)

            if not result:
                return None

            # Convert to dict and parse JSON fields
            document = dict(result)
            if document.get("verification_info"):
                document["verification_info"] = json.loads(document["verification_info"])
            if document.get("metadata"):
                document["metadata"] = json.loads(document["metadata"])

            return document

        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to get document: {str(e)}")

    async def update_document(self, document_id: str, update_data: Dict[str, Any]) -> bool:
        """Update document data.

        Args:
            document_id: Document ID
            update_data: Data to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current document to merge data
            current = await self.get_document(document_id)
            if not current:
                return False

            # Build update query dynamically
            fields = []
            values = []
            for i, (key, value) in enumerate(update_data.items(), start=2):  # start=2 because $1 is document_id
                fields.append(f"{key} = ${i}")

                # Handle JSON fields
                if key in ["verification_info", "metadata"] and value is not None:
                    values.append(json.dumps(value))
                else:
                    values.append(value)

            # Add updated_at timestamp
            fields.append(f"updated_at = ${len(fields) + 2}")
            values.append(datetime.utcnow().isoformat() + "Z")

            query = f"""
                UPDATE documents
                SET {", ".join(fields)}
                WHERE id = $1
                RETURNING id
            """

            result = await self.db.fetchrow(query, document_id, *values)
            return result is not None

        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to update document: {str(e)}")

    async def delete_document(self, document_id: str) -> bool:
        """Delete document.

        Args:
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        try:
            query = """
                DELETE FROM documents
                WHERE id = $1
                RETURNING id
            """

            result = await self.db.fetchrow(query, document_id)
            return result is not None

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete document: {str(e)}")

    async def list_documents(
        self,
        user_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List documents with optional filtering.

        Args:
            user_id: Filter by user ID
            campaign_id: Filter by campaign ID
            type: Filter by document type
            status: Filter by status
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of document records
        """
        try:
            conditions = []
            values = []
            value_index = 1

            if user_id:
                conditions.append(f"user_id = ${value_index}")
                values.append(user_id)
                value_index += 1

            if campaign_id:
                conditions.append(f"campaign_id = ${value_index}")
                values.append(campaign_id)
                value_index += 1

            if type:
                conditions.append(f"type = ${value_index}")
                values.append(type)
                value_index += 1

            if status:
                conditions.append(f"status = ${value_index}")
                values.append(status)
                value_index += 1

            where_clause = " AND ".join(conditions)
            if where_clause:
                where_clause = f"WHERE {where_clause}"

            query = f"""
                SELECT * FROM documents
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ${value_index} OFFSET ${value_index + 1}
            """

            values.extend([limit, offset])

            rows = await self.db.fetch(query, *values)

            # Convert rows to dicts and parse JSON fields
            documents = []
            for row in rows:
                document = dict(row)
                if document.get("verification_info"):
                    document["verification_info"] = json.loads(document["verification_info"])
                if document.get("metadata"):
                    document["metadata"] = json.loads(document["metadata"])
                documents.append(document)

            return documents

        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            raise DatabaseError(f"Failed to list documents: {str(e)}")

    async def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create a new document template.

        Args:
            template_data: Template data

        Returns:
            Template ID
        """
        required_fields = ["id", "name", "type"]
        for field in required_fields:
            if field not in template_data:
                raise ValueError(f"Missing required field: {field}")

        try:
            # Add timestamps
            template_data["created_at"] = template_data.get("created_at", datetime.utcnow().isoformat() + "Z")
            template_data["updated_at"] = template_data["created_at"]

            # Insert template
            query = """
                INSERT INTO document_templates (
                    id, name, type, description, content, thumbnail_url,
                    created_by, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9
                )
                RETURNING id
            """

            values = (
                template_data["id"],
                template_data["name"],
                template_data["type"],
                template_data.get("description"),
                json.dumps(template_data.get("content", {})),
                template_data.get("thumbnail_url"),
                template_data.get("created_by"),
                template_data["created_at"],
                template_data["updated_at"]
            )

            result = await self.db.fetchrow(query, *values)
            return result["id"]

        except Exception as e:
            logger.error(f"Failed to create template: {str(e)}")
            raise DatabaseError(f"Failed to create template: {str(e)}")

    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template data or None if not found
        """
        try:
            query = """
                SELECT * FROM document_templates
                WHERE id = $1
            """

            result = await self.db.fetchrow(query, template_id)

            if not result:
                return None

            # Convert to dict and parse JSON fields
            template = dict(result)
            if template.get("content"):
                template["content"] = json.loads(template["content"])

            return template

        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {str(e)}")
            raise DatabaseError(f"Failed to get template: {str(e)}")

    async def list_templates(self, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available templates with optional filtering.

        Args:
            document_type: Filter by document type

        Returns:
            List of template records
        """
        try:
            if document_type:
                query = """
                    SELECT id, name, type, description, thumbnail_url, created_at
                    FROM document_templates
                    WHERE type = $1
                    ORDER BY name
                """
                rows = await self.db.fetch(query, document_type)
            else:
                query = """
                    SELECT id, name, type, description, thumbnail_url, created_at
                    FROM document_templates
                    ORDER BY name
                """
                rows = await self.db.fetch(query)

            # Convert rows to dicts
            templates = [dict(row) for row in rows]
            return templates

        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")
            raise DatabaseError(f"Failed to list templates: {str(e)}")

    async def get_document_analytics(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a document.

        Args:
            document_id: Document ID

        Returns:
            Analytics data or None if not found
        """
        try:
            query = """
                SELECT * FROM document_analytics
                WHERE document_id = $1
            """

            result = await self.db.fetchrow(query, document_id)

            if not result:
                return None

            # Convert to dict and parse JSON fields
            analytics = dict(result)
            if analytics.get("engagement_by_section"):
                analytics["engagement_by_section"] = json.loads(analytics["engagement_by_section"])
            if analytics.get("additional_metrics"):
                analytics["additional_metrics"] = json.loads(analytics["additional_metrics"])

            return analytics

        except Exception as e:
            logger.error(f"Failed to get analytics for document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to get document analytics: {str(e)}")

    async def update_document_analytics(
        self,
        document_id: str,
        view_data: Dict[str, Any]
    ) -> bool:
        """Update document analytics with new view data.

        Args:
            document_id: Document ID
            view_data: View data to incorporate

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if analytics exist
            existing = await self.get_document_analytics(document_id)

            if existing:
                # Update existing analytics
                views = existing["views"] + 1
                unique_views = existing["unique_views"]

                # Check if this is a unique viewer
                viewer_id = view_data.get("viewer_id")
                if viewer_id and viewer_id not in existing.get("additional_metrics", {}).get("unique_viewers", []):
                    unique_views += 1

                # Calculate metrics
                total_time = existing["average_view_time"] * existing["views"]
                new_time = view_data.get("view_time", 0)
                average_view_time = (total_time + new_time) / views

                # Update engagement by section
                engagement_by_section = existing["engagement_by_section"] or {}
                for section_id, time_spent in view_data.get("sections", {}).items():
                    if section_id in engagement_by_section:
                        engagement_by_section[section_id] = (engagement_by_section[section_id] + time_spent) / 2
                    else:
                        engagement_by_section[section_id] = time_spent

                # Additional metrics
                additional_metrics = existing.get("additional_metrics", {})
                if viewer_id and "unique_viewers" in additional_metrics:
                    if viewer_id not in additional_metrics["unique_viewers"]:
                        additional_metrics["unique_viewers"].append(viewer_id)
                else:
                    additional_metrics["unique_viewers"] = [viewer_id] if viewer_id else []

                # Update conversion data if provided
                if "conversion" in view_data:
                    if "conversions" not in additional_metrics:
                        additional_metrics["conversions"] = 0
                    additional_metrics["conversions"] += 1

                # Calculate conversion rate
                conversion_rate = None
                if unique_views > 0 and "conversions" in additional_metrics:
                    conversion_rate = additional_metrics["conversions"] / unique_views

                # Update the analytics record
                query = """
                    UPDATE document_analytics
                    SET
                        views = $2,
                        unique_views = $3,
                        average_view_time = $4,
                        completion_rate = $5,
                        engagement_by_section = $6,
                        conversion_rate = $7,
                        additional_metrics = $8,
                        updated_at = $9
                    WHERE document_id = $1
                    RETURNING document_id
                """

                values = (
                    document_id,
                    views,
                    unique_views,
                    average_view_time,
                    view_data.get("completion_rate", existing["completion_rate"]),
                    json.dumps(engagement_by_section),
                    conversion_rate,
                    json.dumps(additional_metrics),
                    datetime.utcnow().isoformat() + "Z"
                )

                result = await self.db.fetchrow(query, *values)
                return result is not None
            else:
                # Create new analytics record
                return await self._create_document_analytics(document_id, view_data)

        except Exception as e:
            logger.error(f"Failed to update analytics for document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to update document analytics: {str(e)}")

    async def _create_document_analytics(
        self,
        document_id: str,
        view_data: Dict[str, Any]
    ) -> bool:
        """Create initial analytics record for a document.

        Args:
            document_id: Document ID
            view_data: Initial view data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize analytics
            views = 1
            unique_views = 1 if view_data.get("viewer_id") else 0
            average_view_time = view_data.get("view_time", 0)
            completion_rate = view_data.get("completion_rate", 0.0)

            # Engagement by section
            engagement_by_section = {}
            for section_id, time_spent in view_data.get("sections", {}).items():
                engagement_by_section[section_id] = time_spent

            # Additional metrics
            additional_metrics = {
                "unique_viewers": [view_data.get("viewer_id")] if view_data.get("viewer_id") else []
            }

            # Add conversion data if provided
            if "conversion" in view_data:
                additional_metrics["conversions"] = 1
                conversion_rate = 1.0 / unique_views if unique_views > 0 else 0.0
            else:
                conversion_rate = None

            # Create the analytics record
            timestamp = datetime.utcnow().isoformat() + "Z"

            query = """
                INSERT INTO document_analytics (
                    document_id, views, unique_views, average_view_time,
                    completion_rate, engagement_by_section, conversion_rate,
                    additional_metrics, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                )
                RETURNING document_id
            """

            values = (
                document_id,
                views,
                unique_views,
                average_view_time,
                completion_rate,
                json.dumps(engagement_by_section),
                conversion_rate,
                json.dumps(additional_metrics),
                timestamp,
                timestamp
            )

            result = await self.db.fetchrow(query, *values)
            return result is not None

        except Exception as e:
            logger.error(f"Failed to create analytics for document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to create document analytics: {str(e)}")
