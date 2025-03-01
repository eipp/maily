"""Document generator tool for AI tasks."""

import logging
import json
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

from langchain.tools import BaseTool

from services.document_generator import DocumentGenerator

logger = logging.getLogger(__name__)

class DocumentGeneratorTool(BaseTool):
    """Tool for generating documents using AI."""

    name = "document_generator"
    description = """
    Generates various document types based on content and templates.
    This tool can create PDFs, presentations, contracts, reports, newsletters,
    interactive forms, and more. The documents can be personalized, interactive,
    and blockchain-verified.

    Examples of documents that can be generated:
    - Professional PDF reports
    - Marketing presentations
    - Legal contracts
    - Interactive forms
    - Newsletters
    - Invoices and receipts
    - Personalized documents
    """

    def __init__(self):
        """Initialize document generator tool."""
        super().__init__()
        self.generator = DocumentGenerator()

    async def _arun(
        self,
        document_type: str,
        title: str,
        content: Dict[str, Any],
        template_id: Optional[str] = None,
        recipient_data: Optional[Dict[str, Any]] = None,
        blockchain_verify: bool = False,
        interactive_elements: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a document asynchronously.

        Args:
            document_type: Type of document to generate (pdf, presentation, contract, etc.)
            title: Document title
            content: Document content structure
            template_id: Optional template ID to use
            recipient_data: Optional recipient data for personalization
            blockchain_verify: Whether to verify on blockchain
            interactive_elements: Optional interactive elements to include
            metadata: Optional metadata

        Returns:
            Document generation result
        """
        try:
            logger.info(f"Generating {document_type} document: {title}")

            # Process content sections
            sections = []
            for section in content.get("sections", []):
                section_id = section.get("id", f"sect_{uuid.uuid4().hex}")
                sections.append({
                    "id": section_id,
                    "title": section.get("title", ""),
                    "type": section.get("type", "text"),
                    "content": section.get("content"),
                    "content_json": section.get("content_json"),
                    "interactive": section.get("interactive", False),
                    "interaction_data": section.get("interaction_data", {})
                })

            # Prepare document data
            document_data = {
                "id": metadata.get("document_id", f"doc_{uuid.uuid4().hex}"),
                "type": document_type,
                "title": title,
                "template_id": template_id,
                "sections": sections,
                "user_id": metadata.get("user_id"),
                "campaign_id": metadata.get("campaign_id"),
                "tracking_id": metadata.get("tracking_id"),
                "personalized": recipient_data is not None,
                "recipient_data": recipient_data,
                "blockchain_verify": blockchain_verify,
                "interactive": interactive_elements is not None and len(interactive_elements) > 0,
                "interactive_elements": interactive_elements,
                "metadata": metadata or {}
            }

            # Create document
            result = await self.generator.create_document(document_data)

            return {
                "success": True,
                "document_id": result["id"],
                "status": result["status"],
                "created_at": result["created_at"],
                "message": f"Document generation initiated: {document_type} - {title}"
            }

        except Exception as e:
            logger.error(f"Document generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Document generation failed"
            }

    def _run(
        self,
        document_type: str,
        title: str,
        content: Dict[str, Any],
        template_id: Optional[str] = None,
        recipient_data: Optional[Dict[str, Any]] = None,
        blockchain_verify: bool = False,
        interactive_elements: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run document generation synchronously (not implemented).

        Args:
            document_type: Type of document to generate
            title: Document title
            content: Document content structure
            template_id: Optional template ID to use
            recipient_data: Optional recipient data for personalization
            blockchain_verify: Whether to verify on blockchain
            interactive_elements: Optional interactive elements
            metadata: Optional metadata

        Returns:
            Error response
        """
        # Document generation is async-only, this is just a placeholder
        return {
            "success": False,
            "error": "Document generation can only be performed asynchronously",
            "message": "Use the async version of this tool"
        }

    async def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Get the status of a document.

        Args:
            document_id: Document ID

        Returns:
            Document status information
        """
        try:
            document = await self.generator.get_document(document_id)

            return {
                "success": True,
                "document_id": document_id,
                "status": document.get("status"),
                "file_url": document.get("file_url"),
                "preview_url": document.get("preview_url"),
                "created_at": document.get("created_at"),
                "updated_at": document.get("updated_at")
            }

        except Exception as e:
            logger.error(f"Failed to get document status: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get document status"
            }

    async def get_document_analytics(self, document_id: str) -> Dict[str, Any]:
        """Get analytics for a document.

        Args:
            document_id: Document ID

        Returns:
            Document analytics
        """
        try:
            analytics = await self.generator.get_document_analytics(document_id)

            return {
                "success": True,
                "document_id": document_id,
                "analytics": analytics
            }

        except Exception as e:
            logger.error(f"Failed to get document analytics: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get document analytics"
            }

    async def track_document_view(
        self,
        document_id: str,
        viewer_id: Optional[str] = None,
        view_time: Optional[float] = None,
        completion_rate: Optional[float] = None,
        sections: Optional[Dict[str, float]] = None,
        conversion: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Track a document view event.

        Args:
            document_id: Document ID
            viewer_id: Optional viewer ID
            view_time: Optional view time in seconds
            completion_rate: Optional completion rate (0-1)
            sections: Optional dict mapping section IDs to time spent
            conversion: Optional boolean indicating conversion

        Returns:
            Tracking result
        """
        try:
            # Prepare view data
            view_data = {
                "viewer_id": viewer_id,
                "view_time": view_time,
                "completion_rate": completion_rate,
                "sections": sections or {},
                "conversion": conversion
            }

            # Track view
            await self.generator.track_document_view(document_id, view_data)

            return {
                "success": True,
                "document_id": document_id,
                "message": "Document view tracked successfully"
            }

        except Exception as e:
            logger.error(f"Failed to track document view: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to track document view"
            }

    async def list_templates(self, document_type: Optional[str] = None) -> Dict[str, Any]:
        """List available document templates.

        Args:
            document_type: Optional filter by document type

        Returns:
            List of templates
        """
        try:
            templates = await self.generator.list_templates(document_type)

            return {
                "success": True,
                "templates": templates,
                "count": len(templates)
            }

        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list templates"
            }
