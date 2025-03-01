"""MailyDocs API endpoints for document generation and management."""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field

from core.auth import get_current_user
from core.utils import generate_id
from services.document_generator import DocumentGenerator, DocumentGenerationError
from db.documents import DocumentsRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mailydocs", tags=["mailydocs"])

# Models
class DocumentSection(BaseModel):
    """Model for document sections."""
    id: str
    type: str
    title: str
    content: Any

class DocumentTemplate(BaseModel):
    """Model for document templates."""
    id: str
    name: str
    type: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None

class DocumentRequest(BaseModel):
    """Model for document generation requests."""
    type: str = Field(..., description="Document type (pdf, pptx, xlsx, docx, smart_pdf, etc.)")
    title: str = Field(..., description="Document title")
    template_id: Optional[str] = Field(None, description="Template ID to use")
    campaign_id: Optional[str] = Field(None, description="Associated campaign ID")
    recipient_id: Optional[str] = Field(None, description="Recipient ID for personalization")
    recipient_data: Optional[Dict[str, Any]] = Field(None, description="Custom recipient data")
    sections: List[DocumentSection] = Field([], description="Document sections")
    model_preference: Optional[str] = Field(None, description="AI model preference")
    blockchain_verify: bool = Field(False, description="Enable blockchain verification")
    interactive_elements: Optional[List[Dict[str, Any]]] = Field(None, description="Interactive elements")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Custom metadata")

class DocumentResponse(BaseModel):
    """Model for document generation response."""
    id: str
    status: str
    type: str
    title: str
    file_url: Optional[str] = None
    preview_url: Optional[str] = None
    tracking_id: Optional[str] = None
    personalized: bool
    interactive: bool
    blockchain_verified: bool
    verification_url: Optional[str] = None
    created_at: str
    metadata: Dict[str, Any] = {}

class DocumentAnalytics(BaseModel):
    """Model for document analytics."""
    document_id: str
    views: int
    unique_views: int
    average_view_time: float
    completion_rate: float
    engagement_by_section: Dict[str, float]
    conversion_rate: Optional[float] = None
    created_at: str
    updated_at: str

# Endpoints
@router.post("/documents", response_model=DocumentResponse)
async def create_document(
    request: DocumentRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    documents_repo: DocumentsRepository = Depends()
):
    """Create a new document."""
    logger.info(f"Document generation request received: {request.type} - {request.title}")

    try:
        document_id = generate_id("doc")

        # Prepare document sections
        sections = []
        for section in request.sections:
            sections.append({
                "id": section.id,
                "title": section.title,
                "type": section.type,
                "content": section.content
            })

        # Add metadata
        metadata = request.metadata or {}
        metadata.update({
            "document_id": document_id,
            "user_id": current_user.id,
            "campaign_id": request.campaign_id
        })

        # Prepare document data
        document_data = {
            "id": document_id,
            "type": request.type,
            "title": request.title,
            "template_id": request.template_id,
            "sections": sections,
            "user_id": current_user.id,
            "campaign_id": request.campaign_id,
            "recipient_data": request.recipient_data,
            "blockchain_verify": request.blockchain_verify,
            "interactive_elements": request.interactive_elements,
            "metadata": metadata
        }

        # Create document generator
        document_generator = DocumentGenerator(documents_repo)

        # Execute document generation in background
        background_tasks.add_task(
            _generate_document_async,
            document_generator,
            document_data
        )

        # Return immediate response
        return DocumentResponse(
            id=document_id,
            status="pending",
            type=request.type,
            title=request.title,
            personalized=request.recipient_data is not None,
            interactive=request.interactive_elements is not None and len(request.interactive_elements) > 0,
            blockchain_verified=False,  # Will be updated during generation
            created_at=datetime.utcnow().isoformat() + "Z",
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"Document generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user = Depends(get_current_user),
    documents_repo: DocumentsRepository = Depends()
):
    """Get document status and details."""
    document = await documents_repo.get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check document ownership or permissions
    if document.get("user_id") != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")

    return document

@router.get("/documents/{document_id}/analytics", response_model=DocumentAnalytics)
async def get_document_analytics(
    document_id: str,
    current_user = Depends(get_current_user),
    documents_repo: DocumentsRepository = Depends()
):
    """Get document analytics."""
    document = await documents_repo.get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check document ownership or permissions
    if document.get("user_id") != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")

    # Get document analytics
    analytics = await documents_repo.get_document_analytics(document_id)

    if not analytics:
        raise HTTPException(status_code=404, detail="Analytics not found for this document")

    return analytics

@router.get("/templates", response_model=List[DocumentTemplate])
async def list_templates(
    document_type: Optional[str] = None,
    current_user = Depends(get_current_user),
    documents_repo: DocumentsRepository = Depends()
):
    """List available document templates."""
    templates = await documents_repo.list_templates(document_type)
    return templates

@router.post("/templates", response_model=DocumentTemplate)
async def create_template(
    template: DocumentTemplate,
    current_user = Depends(get_current_user),
    documents_repo: DocumentsRepository = Depends()
):
    """Create a new document template."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can create templates")

    template_id = await documents_repo.create_template(template.dict())
    created_template = await documents_repo.get_template(template_id)

    return created_template

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user = Depends(get_current_user),
    documents_repo: DocumentsRepository = Depends()
):
    """Delete a document."""
    document = await documents_repo.get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check document ownership or permissions
    if document.get("user_id") != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")

    # Delete document
    success = await documents_repo.delete_document(document_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")

    return {"status": "success", "message": "Document deleted successfully"}

@router.post("/documents/{document_id}/verify", response_model=Dict[str, Any])
async def verify_document(
    document_id: str,
    current_user = Depends(get_current_user),
    documents_repo: DocumentsRepository = Depends()
):
    """Verify document authenticity using blockchain."""
    document = await documents_repo.get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # If already verified, return verification info
    if document.get("blockchain_verified"):
        return {
            "verified": True,
            "verification_info": document.get("verification_info", {}),
            "verification_url": document.get("verification_url")
        }

    # Otherwise, verify the document
    document_generator = DocumentGenerator(documents_repo)

    try:
        # Get document file path
        file_path = document.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document file not found")

        # Verify on blockchain
        verification_info = await document_generator._verify_on_blockchain(file_path, document.get("metadata", {}))

        # Update document with verification info
        updated = await documents_repo.update_document(
            document_id,
            {
                "blockchain_verified": True,
                "verification_info": verification_info,
                "verification_url": verification_info.get("verification_url")
            }
        )

        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update document verification")

        return {
            "verified": True,
            "verification_info": verification_info,
            "verification_url": verification_info.get("verification_url")
        }

    except Exception as e:
        logger.error(f"Document verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def _generate_document_async(
    document_generator: DocumentGenerator,
    document_data: Dict[str, Any]
):
    """Generate document asynchronously.

    Args:
        document_generator: Document generator service
        document_data: Document data for generation
    """
    try:
        logger.info(f"Starting async document generation for {document_data['id']}")

        # Create document - this will start the generation process internally
        await document_generator.create_document(document_data)

    except Exception as e:
        logger.error(f"Async document generation failed: {str(e)}")
        # Update document with error status if needed
        try:
            await document_generator.docs_repo.update_document(
                document_data["id"],
                {
                    "status": "failed",
                    "metadata": {
                        "error": str(e)
                    }
                }
            )
        except Exception as update_error:
            logger.error(f"Failed to update document status: {str(update_error)}")

def get_current_timestamp():
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"
