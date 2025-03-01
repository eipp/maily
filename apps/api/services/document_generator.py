"""Document generation service for MailyDocs."""

import os
import uuid
import logging
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import asyncio
import tempfile

from core.config import settings
from core.storage import get_storage
from db.documents import DocumentsRepository
from services.ai import get_ai_service
from services.blockchain import BlockchainService
from metrics.prometheus import (
    monitor_document_generation,
    track_document_size,
    track_template_usage
)

logger = logging.getLogger(__name__)

class DocumentGenerationError(Exception):
    """Exception raised for errors during document generation."""
    pass

class DocumentGenerator:
    """Service for generating and managing documents."""

    def __init__(self, docs_repo: DocumentsRepository = None):
        """Initialize the document generator.

        Args:
            docs_repo: Repository for document storage
        """
        self.docs_repo = docs_repo or DocumentsRepository()
        self.storage = get_storage()
        self.ai_service = get_ai_service()
        self.blockchain_service = BlockchainService() if settings.BLOCKCHAIN_ENABLED else None

        # File paths configuration
        self.document_base_path = settings.DOCUMENT_STORAGE_PATH
        self.document_base_url = settings.DOCUMENT_BASE_URL
        self.temp_dir = settings.TEMP_DIRECTORY

        # Ensure directories exist
        os.makedirs(self.document_base_path, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document based on provided data.

        Args:
            document_data: Document creation parameters

        Returns:
            Created document data
        """
        # Generate ID if not provided
        document_id = document_data.get("id", f"doc_{uuid.uuid4().hex}")
        document_data["id"] = document_id

        # Set initial status
        document_data["status"] = "pending"

        # Create document record
        await self.docs_repo.create_document(document_data)

        # Start generation process in background
        asyncio.create_task(self._generate_document(document_id, document_data))

        # Return initial data
        return {
            "id": document_id,
            "status": "pending",
            "created_at": document_data.get("created_at", datetime.utcnow().isoformat() + "Z")
        }

    async def _generate_document(self, document_id: str, document_data: Dict[str, Any]) -> None:
        """Generate document content based on document type and template.

        Args:
            document_id: Document ID
            document_data: Document data including template and content parameters
        """
        try:
            # Update status to processing
            await self.docs_repo.update_document(document_id, {"status": "processing"})

            # Get template if specified
            template = None
            if template_id := document_data.get("template_id"):
                template = await self.docs_repo.get_template(template_id)
                if not template:
                    raise DocumentGenerationError(f"Template not found: {template_id}")

            # Choose generator based on document type
            document_type = document_data.get("type", "standard")

            # Generate content based on document type
            file_path, file_url, preview_url = await self._generate_by_type(
                document_id,
                document_type,
                document_data,
                template
            )

            # Update document with file info
            update_data = {
                "status": "completed",
                "file_path": file_path,
                "file_url": file_url,
                "preview_url": preview_url
            }

            # Verify document if blockchain verification is enabled
            if document_data.get("blockchain_verify", False) and self.blockchain_service:
                verification_info = await self._verify_document(document_id, file_path)
                if verification_info:
                    update_data["blockchain_verified"] = True
                    update_data["verification_url"] = verification_info.get("verification_url")
                    update_data["verification_info"] = verification_info

            # Update document record
            await self.docs_repo.update_document(document_id, update_data)

            # Process document sections if provided
            if sections := document_data.get("sections"):
                await self._process_sections(document_id, sections)

            logger.info(f"Document {document_id} generated successfully")

        except Exception as e:
            logger.error(f"Document generation failed for {document_id}: {str(e)}")
            # Update document with error status
            await self.docs_repo.update_document(document_id, {
                "status": "failed",
                "metadata": {
                    "error": str(e)
                }
            })

    async def _generate_by_type(
        self,
        document_id: str,
        document_type: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate document based on its type.

        Args:
            document_id: Document ID
            document_type: Type of document to generate
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        if document_type == "pdf":
            return await self._generate_pdf_document(document_id, document_data, template)
        elif document_type == "presentation":
            return await self._generate_presentation(document_id, document_data, template)
        elif document_type == "contract":
            return await self._generate_contract(document_id, document_data, template)
        elif document_type == "report":
            return await self._generate_report(document_id, document_data, template)
        elif document_type == "newsletter":
            return await self._generate_newsletter(document_id, document_data, template)
        elif document_type == "form":
            return await self._generate_interactive_form(document_id, document_data, template)
        elif document_type == "invoice":
            return await self._generate_invoice(document_id, document_data, template)
        else:
            # Default to standard document
            return await self._generate_standard_document(document_id, document_data, template)

    @monitor_document_generation(document_type="pdf")
    async def _generate_pdf_document(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate a PDF document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        # Implement PDF generation logic
        # For now, we'll create a placeholder
        title = document_data.get("title", "Untitled Document")

        # Define file paths
        file_name = f"{document_id}.pdf"
        file_path = os.path.join(self.document_base_path, file_name)
        file_url = f"{self.document_base_url}/{file_name}"
        preview_url = f"{self.document_base_url}/previews/{document_id}_preview.png"

        # TODO: Implement actual PDF generation with a PDF library
        # For now, just create a dummy file
        with open(file_path, "w") as f:
            f.write(f"PDF Document: {title}")

        # Track document size
        track_document_size(file_path, "pdf")

        # Track template usage
        if template:
            track_template_usage(template["id"], "pdf")

        return file_path, file_url, preview_url

    async def _generate_presentation(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate a presentation document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        # Placeholder for presentation generation logic
        title = document_data.get("title", "Untitled Presentation")

        # Define file paths
        file_name = f"{document_id}.pptx"
        file_path = os.path.join(self.document_base_path, file_name)
        file_url = f"{self.document_base_url}/{file_name}"
        preview_url = f"{self.document_base_url}/previews/{document_id}_preview.png"

        # TODO: Implement actual presentation generation
        # For now, just create a dummy file
        with open(file_path, "w") as f:
            f.write(f"Presentation: {title}")

        return file_path, file_url, preview_url

    async def _generate_contract(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate a contract document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        # Placeholder for contract generation logic
        title = document_data.get("title", "Untitled Contract")

        # Define file paths
        file_name = f"{document_id}.pdf"
        file_path = os.path.join(self.document_base_path, file_name)
        file_url = f"{self.document_base_url}/{file_name}"
        preview_url = f"{self.document_base_url}/previews/{document_id}_preview.png"

        # TODO: Implement actual contract generation
        # For now, just create a dummy file
        with open(file_path, "w") as f:
            f.write(f"Contract: {title}")

        return file_path, file_url, preview_url

    async def _generate_report(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate a report document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        # Placeholder for report generation logic
        title = document_data.get("title", "Untitled Report")

        # Define file paths
        file_name = f"{document_id}.pdf"
        file_path = os.path.join(self.document_base_path, file_name)
        file_url = f"{self.document_base_url}/{file_name}"
        preview_url = f"{self.document_base_url}/previews/{document_id}_preview.png"

        # TODO: Implement actual report generation
        # For now, just create a dummy file
        with open(file_path, "w") as f:
            f.write(f"Report: {title}")

        return file_path, file_url, preview_url

    async def _generate_newsletter(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate a newsletter document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        # Placeholder for newsletter generation logic
        title = document_data.get("title", "Untitled Newsletter")

        # Define file paths
        file_name = f"{document_id}.html"
        file_path = os.path.join(self.document_base_path, file_name)
        file_url = f"{self.document_base_url}/{file_name}"
        preview_url = f"{self.document_base_url}/previews/{document_id}_preview.png"

        # TODO: Implement actual newsletter generation
        # For now, just create a dummy file
        with open(file_path, "w") as f:
            f.write(f"<html><body><h1>Newsletter: {title}</h1></body></html>")

        return file_path, file_url, preview_url

    async def _generate_interactive_form(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate an interactive form document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        # Placeholder for interactive form generation logic
        title = document_data.get("title", "Untitled Form")

        # Define file paths
        file_name = f"{document_id}.html"
        file_path = os.path.join(self.document_base_path, file_name)
        file_url = f"{self.document_base_url}/{file_name}"
        preview_url = f"{self.document_base_url}/previews/{document_id}_preview.png"

        # TODO: Implement actual form generation
        # For now, just create a dummy file
        with open(file_path, "w") as f:
            f.write(f"<html><body><h1>Interactive Form: {title}</h1></body></html>")

        return file_path, file_url, preview_url

    async def _generate_invoice(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate an invoice document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        # Placeholder for invoice generation logic
        title = document_data.get("title", "Untitled Invoice")

        # Define file paths
        file_name = f"{document_id}.pdf"
        file_path = os.path.join(self.document_base_path, file_name)
        file_url = f"{self.document_base_url}/{file_name}"
        preview_url = f"{self.document_base_url}/previews/{document_id}_preview.png"

        # TODO: Implement actual invoice generation
        # For now, just create a dummy file
        with open(file_path, "w") as f:
            f.write(f"Invoice: {title}")

        return file_path, file_url, preview_url

    async def _generate_standard_document(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate a standard document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        # Placeholder for standard document generation logic
        title = document_data.get("title", "Untitled Document")

        # Define file paths
        file_name = f"{document_id}.pdf"
        file_path = os.path.join(self.document_base_path, file_name)
        file_url = f"{self.document_base_url}/{file_name}"
        preview_url = f"{self.document_base_url}/previews/{document_id}_preview.png"

        # TODO: Implement actual document generation
        # For now, just create a dummy file
        with open(file_path, "w") as f:
            f.write(f"Standard Document: {title}")

        return file_path, file_url, preview_url

    async def _process_sections(
        self,
        document_id: str,
        sections: List[Dict[str, Any]]
    ) -> None:
        """Process and store document sections.

        Args:
            document_id: Document ID
            sections: List of section data
        """
        for idx, section in enumerate(sections):
            # Generate ID if not provided
            section_id = section.get("id", f"sect_{uuid.uuid4().hex}")

            # Prepare section data
            section_data = {
                "id": section_id,
                "document_id": document_id,
                "title": section.get("title"),
                "type": section.get("type", "text"),
                "content": section.get("content"),
                "content_json": section.get("content_json"),
                "order_index": section.get("order_index", idx),
                "interactive": section.get("interactive", False),
                "interaction_data": section.get("interaction_data"),
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }

            # Insert section record
            # TODO: Implement section repository
            # For now, we'll just log
            logger.info(f"Processing section {section_id} for document {document_id}")

    async def _verify_document(
        self,
        document_id: str,
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Verify document on blockchain.

        Args:
            document_id: Document ID
            file_path: Path to the document file

        Returns:
            Verification info or None if verification failed
        """
        if not self.blockchain_service:
            logger.warning("Blockchain service not available for verification")
            return None

        try:
            # Generate document hash
            with open(file_path, "rb") as f:
                document_content = f.read()

            # Submit to blockchain
            tx_hash, verification_url = await self.blockchain_service.register_document(
                document_id, document_content
            )

            if not tx_hash:
                logger.error(f"Failed to verify document {document_id} on blockchain")
                return None

            # Create verification record
            verification_id = f"ver_{uuid.uuid4().hex}"
            verification_data = {
                "id": verification_id,
                "document_id": document_id,
                "hash": self.blockchain_service.calculate_hash(document_content),
                "blockchain_tx": tx_hash,
                "verification_method": "blockchain",
                "verified_at": datetime.utcnow().isoformat() + "Z",
                "verification_data": {
                    "blockchain": "ethereum",  # or whatever blockchain is used
                    "network": self.blockchain_service.network
                },
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }

            # TODO: Store verification record
            # For now, just return the data
            return {
                "verification_id": verification_id,
                "tx_hash": tx_hash,
                "verification_url": verification_url,
                "verified_at": verification_data["verified_at"]
            }

        except Exception as e:
            logger.error(f"Document verification failed: {str(e)}")
            return None

    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document data by ID.

        Args:
            document_id: Document ID

        Returns:
            Document data
        """
        document = await self.docs_repo.get_document(document_id)
        if not document:
            raise DocumentGenerationError(f"Document not found: {document_id}")
        return document

    async def get_document_analytics(self, document_id: str) -> Dict[str, Any]:
        """Get analytics data for a document.

        Args:
            document_id: Document ID

        Returns:
            Analytics data
        """
        # Ensure document exists
        document = await self.docs_repo.get_document(document_id)
        if not document:
            raise DocumentGenerationError(f"Document not found: {document_id}")

        # Get analytics
        analytics = await self.docs_repo.get_document_analytics(document_id)
        if not analytics:
            # Return empty analytics if none exist
            return {
                "document_id": document_id,
                "views": 0,
                "unique_views": 0,
                "average_view_time": 0,
                "completion_rate": 0,
                "engagement_by_section": {},
                "conversion_rate": None,
                "additional_metrics": {}
            }

        return analytics

    async def track_document_view(
        self,
        document_id: str,
        view_data: Dict[str, Any]
    ) -> None:
        """Track a document view event.

        Args:
            document_id: Document ID
            view_data: View event data
        """
        # Ensure document exists
        document = await self.docs_repo.get_document(document_id)
        if not document:
            raise DocumentGenerationError(f"Document not found: {document_id}")

        # Update analytics
        await self.docs_repo.update_document_analytics(document_id, view_data)

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and its associated files.

        Args:
            document_id: Document ID

        Returns:
            True if deleted, False otherwise
        """
        # Get document details
        document = await self.docs_repo.get_document(document_id)
        if not document:
            return False

        # Delete associated files
        if file_path := document.get("file_path"):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Failed to delete document file {file_path}: {str(e)}")

        # Delete from database
        return await self.docs_repo.delete_document(document_id)

    async def list_templates(
        self,
        document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List available document templates.

        Args:
            document_type: Optional filter by document type

        Returns:
            List of templates
        """
        return await self.docs_repo.list_templates(document_type)

    async def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create a new document template.

        Args:
            template_data: Template data

        Returns:
            Template ID
        """
        # Generate ID if not provided
        template_id = template_data.get("id", f"tmpl_{uuid.uuid4().hex}")
        template_data["id"] = template_id

        # Create template record
        await self.docs_repo.create_template(template_data)

        return template_id

    async def list_documents(
        self,
        user_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List documents with optional filtering.

        Args:
            user_id: Filter by user ID
            campaign_id: Filter by campaign ID
            document_type: Filter by document type
            status: Filter by status
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of document records
        """
        return await self.docs_repo.list_documents(
            user_id=user_id,
            campaign_id=campaign_id,
            type=document_type,
            status=status,
            limit=limit,
            offset=offset
        )
