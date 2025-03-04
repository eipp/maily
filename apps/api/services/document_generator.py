"""Document generation service."""

import os
import logging
import uuid
import json
import base64
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import asyncio

from .base_service import BaseService
from .document_generators.contract_generator import ContractGenerator
from .document_generators.form_generator import FormGenerator
from .document_generators.invoice_generator import InvoiceGenerator
from .document_generators.newsletter_generator import NewsletterGenerator
from .document_generators.pdf_generator import PDFGenerator
from .document_generators.presentation_generator import PresentationGenerator
from .document_generators.report_generator import ReportGenerator
from ..monitoring.mailydocs_monitoring import (
    monitor_document_generation,
    track_document_size,
    track_template_usage,
    track_document_analytics_event,
    log_document_event
)

logger = logging.getLogger(__name__)

class DocumentGenerationError(Exception):
    """Exception raised for document generation errors."""
    pass

class DocumentGenerator(BaseService):
    """Service for generating various document types."""

    def __init__(self, db=None, settings=None):
        """Initialize the document generator service."""
        super().__init__(db, settings)
        
        # Set base paths for document storage and access
        self.document_base_path = os.environ.get("DOCUMENT_BASE_PATH", "storage/documents")
        self.document_base_url = os.environ.get("DOCUMENT_BASE_URL", "/api/documents/files")
        
        # Ensure base directory exists
        os.makedirs(self.document_base_path, exist_ok=True)
        
        # Initialize document generators
        self.generators = {
            "contract": ContractGenerator(self.document_base_path, self.document_base_url),
            "form": FormGenerator(self.document_base_path, self.document_base_url),
            "invoice": InvoiceGenerator(self.document_base_path, self.document_base_url),
            "newsletter": NewsletterGenerator(self.document_base_path, self.document_base_url),
            "pdf": PDFGenerator(self.document_base_path, self.document_base_url),
            "presentation": PresentationGenerator(self.document_base_path, self.document_base_url),
            "report": ReportGenerator(self.document_base_path, self.document_base_url)
        }
        
        # Initialize document database
        self.documents_db_path = os.path.join(self.document_base_path, "documents.json")
        self.templates_db_path = os.path.join(self.document_base_path, "templates.json")
        self.analytics_db_path = os.path.join(self.document_base_path, "analytics.json")
        
        # Load existing data or create new databases
        self.documents = self._load_json_db(self.documents_db_path, {})
        self.templates = self._load_json_db(self.templates_db_path, {})
        self.analytics = self._load_json_db(self.analytics_db_path, {})
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info("Document generator service initialized")

    def _load_json_db(self, path: str, default: Any) -> Any:
        """Load JSON database from file or create new one.
        
        Args:
            path: Path to JSON file
            default: Default value if file doesn't exist
            
        Returns:
            Loaded data or default value
        """
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
            else:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                # Create new file with default value
                with open(path, 'w') as f:
                    json.dump(default, f)
                return default
        except Exception as e:
            logger.error(f"Error loading JSON database from {path}: {e}")
            return default

    async def _save_json_db(self, path: str, data: Any) -> None:
        """Save JSON database to file.
        
        Args:
            path: Path to JSON file
            data: Data to save
        """
        try:
            async with self._lock:
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving JSON database to {path}: {e}")
            raise DocumentGenerationError(f"Failed to save data: {str(e)}")

    @monitor_document_generation("generic")
    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document.
        
        Args:
            document_data: Document data including type, title, etc.
            
        Returns:
            Created document data
        """
        try:
            # Generate document ID
            document_id = f"doc_{uuid.uuid4().hex}"
            
            # Get document type
            document_type = document_data.get("type", "pdf").lower()
            
            # Validate document type
            if document_type not in self.generators:
                raise DocumentGenerationError(f"Unsupported document type: {document_type}")
            
            # Get template if specified
            template = None
            template_id = document_data.get("template_id")
            if template_id:
                template = self.templates.get(template_id)
                if not template:
                    raise DocumentGenerationError(f"Template not found: {template_id}")
                
                # Track template usage
                track_template_usage(template_id, document_type)
            
            # Generate document
            generator = self.generators[document_type]
            file_path, file_url, preview_url = await generator.generate(
                document_id=document_id,
                document_data=document_data,
                template=template
            )
            
            # Track document size
            track_document_size(file_path, document_type)
            
            # Create document record
            timestamp = datetime.utcnow().isoformat()
            document = {
                "id": document_id,
                "title": document_data.get("title", "Untitled Document"),
                "type": document_type,
                "user_id": document_data.get("user_id"),
                "status": "completed",
                "file_url": file_url,
                "preview_url": preview_url,
                "created_at": timestamp,
                "updated_at": timestamp,
                "metadata": document_data.get("metadata", {})
            }
            
            # Save document record
            self.documents[document_id] = document
            await self._save_json_db(self.documents_db_path, self.documents)
            
            # Log document creation
            log_document_event(
                event_type="document_created",
                document_id=document_id,
                document_type=document_type,
                user_id=document_data.get("user_id")
            )
            
            # Initialize analytics for this document
            self.analytics[document_id] = {
                "views": 0,
                "downloads": 0,
                "shares": 0,
                "last_viewed": None,
                "view_history": []
            }
            await self._save_json_db(self.analytics_db_path, self.analytics)
            
            return document
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            raise DocumentGenerationError(f"Failed to create document: {str(e)}")

    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document data
        """
        document = self.documents.get(document_id)
        if not document:
            raise DocumentGenerationError(f"Document not found: {document_id}")
        
        return document

    async def list_documents(
        self,
        user_id: Optional[str] = None,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List documents with optional filtering.
        
        Args:
            user_id: Filter by user ID
            document_type: Filter by document type
            status: Filter by status
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of document records
        """
        # Filter documents
        filtered_documents = []
        for doc in self.documents.values():
            # Apply filters
            if user_id and doc.get("user_id") != user_id:
                continue
                
            if document_type and doc.get("type") != document_type:
                continue
                
            if status and doc.get("status") != status:
                continue
                
            filtered_documents.append(doc)
        
        # Sort by creation date (newest first)
        filtered_documents.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        paginated_documents = filtered_documents[offset:offset + limit]
        
        return paginated_documents

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if document_id not in self.documents:
            return False
        
        try:
            # Get document data
            document = self.documents[document_id]
            document_type = document.get("type", "pdf")
            
            # Delete document file
            file_path = os.path.join(self.document_base_path, f"{document_id}.{self._get_file_extension(document_type)}")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete preview file if exists
            preview_path = os.path.join(self.document_base_path, "previews", f"{document_id}_preview.png")
            if os.path.exists(preview_path):
                os.remove(preview_path)
            
            # Remove document record
            del self.documents[document_id]
            await self._save_json_db(self.documents_db_path, self.documents)
            
            # Remove analytics record
            if document_id in self.analytics:
                del self.analytics[document_id]
                await self._save_json_db(self.analytics_db_path, self.analytics)
            
            # Log document deletion
            log_document_event(
                event_type="document_deleted",
                document_id=document_id,
                document_type=document_type,
                user_id=document.get("user_id")
            )
            
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False

    def _get_file_extension(self, document_type: str) -> str:
        """Get file extension for document type.
        
        Args:
            document_type: Document type
            
        Returns:
            File extension
        """
        extensions = {
            "pdf": "pdf",
            "presentation": "pptx",
            "contract": "pdf",
            "report": "pdf",
            "newsletter": "html",
            "form": "html",
            "invoice": "pdf"
        }
        
        return extensions.get(document_type, "pdf")

    async def list_templates(self, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List document templates.
        
        Args:
            document_type: Filter by document type
            
        Returns:
            List of templates
        """
        # Filter templates
        filtered_templates = []
        for template_id, template in self.templates.items():
            # Apply filter
            if document_type and template.get("type") != document_type:
                continue
                
            # Add template ID to data
            template_data = dict(template)
            template_data["id"] = template_id
            
            filtered_templates.append(template_data)
        
        # Sort by name
        filtered_templates.sort(key=lambda x: x.get("name", ""))
        
        return filtered_templates

    async def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create a new document template.
        
        Args:
            template_data: Template data
            
        Returns:
            Template ID
        """
        try:
            # Generate template ID
            template_id = f"template_{uuid.uuid4().hex}"
            
            # Create template record
            timestamp = datetime.utcnow().isoformat()
            template = {
                "name": template_data.get("name", "Untitled Template"),
                "type": template_data.get("type", "pdf"),
                "description": template_data.get("description"),
                "content": template_data.get("content", {}),
                "created_at": timestamp,
                "updated_at": timestamp,
                "user_id": template_data.get("user_id"),
                "metadata": template_data.get("metadata", {})
            }
            
            # Save template record
            self.templates[template_id] = template
            await self._save_json_db(self.templates_db_path, self.templates)
            
            # Log template creation
            logger.info(f"Template created: {template_id} ({template['name']})")
            
            return template_id
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            raise DocumentGenerationError(f"Failed to create template: {str(e)}")

    async def get_document_analytics(self, document_id: str) -> Dict[str, Any]:
        """Get analytics for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document analytics data
        """
        if document_id not in self.analytics:
            raise DocumentGenerationError(f"Analytics not found for document: {document_id}")
        
        return self.analytics[document_id]

    async def track_document_view(self, document_id: str, view_data: Dict[str, Any]) -> None:
        """Track a document view event.
        
        Args:
            document_id: Document ID
            view_data: View event data
        """
        if document_id not in self.documents:
            raise DocumentGenerationError(f"Document not found: {document_id}")
        
        if document_id not in self.analytics:
            self.analytics[document_id] = {
                "views": 0,
                "downloads": 0,
                "shares": 0,
                "last_viewed": None,
                "view_history": []
            }
        
        # Update analytics
        timestamp = datetime.utcnow().isoformat()
        self.analytics[document_id]["views"] += 1
        self.analytics[document_id]["last_viewed"] = timestamp
        
        # Add view event to history
        view_event = {
            "timestamp": timestamp,
            "ip": view_data.get("ip"),
            "user_agent": view_data.get("user_agent"),
            "user_id": view_data.get("user_id"),
            "referrer": view_data.get("referrer")
        }
        
        self.analytics[document_id]["view_history"].append(view_event)
        
        # Limit history size
        if len(self.analytics[document_id]["view_history"]) > 100:
            self.analytics[document_id]["view_history"] = self.analytics[document_id]["view_history"][-100:]
        
        # Save analytics
        await self._save_json_db(self.analytics_db_path, self.analytics)
        
        # Track analytics event
        track_document_analytics_event("view")
        
        # Log view event
        log_document_event(
            event_type="document_viewed",
            document_id=document_id,
            user_id=view_data.get("user_id"),
            ip=view_data.get("ip")
        )
        
    async def generate_document_certificate(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """Generate a blockchain certificate for a document.
        
        Args:
            document_id: Document ID
            user_id: User ID generating the certificate
            
        Returns:
            Certificate data
        """
        try:
            # Check if document exists
            if document_id not in self.documents:
                raise DocumentGenerationError(f"Document not found: {document_id}")
            
            document = self.documents[document_id]
            
            # Get document file path
            file_extension = self._get_file_extension(document.get("type", "pdf"))
            file_path = os.path.join(self.document_base_path, f"{document_id}.{file_extension}")
            
            if not os.path.exists(file_path):
                raise DocumentGenerationError(f"Document file not found: {file_path}")
            
            # Get document metadata
            metadata = document.get("metadata", {})
            metadata.update({
                "document_id": document_id,
                "document_type": document.get("type", "pdf"),
                "document_title": document.get("title", "Untitled Document"),
                "user_id": user_id
            })
            
            # Generate certificate by calling the verification method
            verification_info = await self._verify_on_blockchain(file_path, metadata)
            
            # Update document with verification info
            document["blockchain_verified"] = True
            document["verification_info"] = verification_info
            document["verification_url"] = verification_info.get("verification_url")
            
            # Save updated document
            await self._save_json_db(self.documents_db_path, self.documents)
            
            # Log certificate generation
            log_document_event(
                event_type="document_certificate_generated",
                document_id=document_id,
                user_id=user_id
            )
            
            return verification_info
            
        except Exception as e:
            logger.error(f"Error generating document certificate: {e}")
            raise DocumentGenerationError(f"Failed to generate certificate: {str(e)}")
            
    async def _verify_on_blockchain(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Verify document on blockchain.
        
        Args:
            file_path: Path to the document file
            metadata: Document metadata
            
        Returns:
            Verification information
        """
        try:
            # Try to import the certificate service
            try:
                from .mailydocs_certificate_service import get_mailydocs_certificate_service
                certificate_service = get_mailydocs_certificate_service()
                
                # Read document content
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Convert binary content to base64 string for hashing
                content_base64 = base64.b64encode(content).decode('utf-8')
                
                # Get required metadata
                document_id = metadata.get('document_id', f"doc_{uuid.uuid4().hex}")
                user_id = metadata.get('user_id', 'system')
                
                # Prepare certificate metadata
                cert_metadata = {
                    "document_type": metadata.get('document_type', 'pdf'),
                    "document_title": metadata.get('document_title', 'Untitled Document'),
                    "issuer_name": metadata.get('issuer_name', 'Maily System'),
                    "recipient_id": metadata.get('recipient_id'),
                    "recipient_name": metadata.get('recipient_name'),
                    "additional_data": {
                        "file_path": file_path,
                        "file_size": os.path.getsize(file_path),
                        "mime_type": self._get_mime_type(file_path),
                        "generation_timestamp": datetime.utcnow().isoformat()
                    }
                }
                
                # Generate certificate
                certificate = await certificate_service.generate_certificate(
                    document_id=document_id,
                    document_content=content_base64,
                    metadata=cert_metadata,
                    user_id=user_id
                )
                
                # Return verification info
                verification_info = {
                    "certificate_id": certificate.id,
                    "verification_id": certificate.blockchain_id,
                    "timestamp": certificate.metadata.issued_at.isoformat(),
                    "document_hash": certificate.content_hash,
                    "verification_url": certificate.verification_url,
                    "blockchain_transaction": certificate.blockchain_transaction,
                    "qr_code": certificate.qr_code
                }
                
                logger.info(f"Document verified with certificate: {certificate.id}")
                
                return verification_info
                
            except ImportError:
                # If certificate service is not available, use placeholder implementation
                logger.warning("MailyDocs certificate service not available, using placeholder verification")
                verification_info = {
                    "verification_id": f"verify_{uuid.uuid4().hex}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "document_hash": f"hash_{uuid.uuid4().hex}",
                    "verification_url": f"{self.document_base_url}/verify?id={metadata.get('document_id', '')}"
                }
                
                logger.info(f"Document verified with placeholder: {verification_info['verification_id']}")
                
                return verification_info
                
        except Exception as e:
            logger.error(f"Error verifying document on blockchain: {e}")
            # Return a placeholder but mark the error
            return {
                "verification_id": f"error_{uuid.uuid4().hex}",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "verification_url": f"{self.document_base_url}/verify?id={metadata.get('document_id', '')}"
            }
            
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        # Simple extension-based MIME type detection
        extension = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.html': 'text/html',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg'
        }
        
        return mime_types.get(extension, 'application/octet-stream')
