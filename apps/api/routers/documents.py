"""Document generation router."""

import logging
import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, UploadFile, File, Form
from pydantic import BaseModel, Field

from middleware.standardized_auth import require_auth
from services.document_generator import DocumentGenerator, DocumentGenerationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Document generator service
document_generator = DocumentGenerator()


class DocumentCreateRequest(BaseModel):
    """Document creation request model."""
    title: str = Field(..., description="Document title")
    type: str = Field(..., description="Document type (pdf, presentation, contract, report, newsletter, form, invoice)")
    template_id: Optional[str] = Field(None, description="Template ID to use")
    sections: Optional[List[Dict[str, Any]]] = Field(None, description="Document sections")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    blockchain_verify: Optional[bool] = Field(False, description="Whether to verify the document on blockchain")


class DocumentResponse(BaseModel):
    """Document response model."""
    id: str
    title: str
    type: str
    status: str
    file_url: Optional[str] = None
    preview_url: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TemplateResponse(BaseModel):
    """Template response model."""
    id: str
    name: str
    type: str
    description: Optional[str] = None
    preview_url: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TemplateCreateRequest(BaseModel):
    """Template creation request model."""
    name: str = Field(..., description="Template name")
    type: str = Field(..., description="Template type (pdf, presentation, contract, report, newsletter, form, invoice)")
    description: Optional[str] = Field(None, description="Template description")
    content: Dict[str, Any] = Field(..., description="Template content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreateRequest,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Create a new document.

    Args:
        document_data: Document creation data
        user: Authenticated user

    Returns:
        Created document data
    """
    try:
        # Add user ID to document data
        document_data_dict = document_data.dict()
        document_data_dict["user_id"] = user["id"]

        # Create document
        document = await document_generator.create_document(document_data_dict)
        return document
    except DocumentGenerationError as e:
        logger.error(f"Document generation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating document")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str = Path(..., description="Document ID"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get a document by ID.

    Args:
        document_id: Document ID
        user: Authenticated user

    Returns:
        Document data
    """
    try:
        document = await document_generator.get_document(document_id)
        
        # Check if user has access to the document
        if document.get("user_id") != user["id"] and not user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Access denied")
            
        return document
    except DocumentGenerationError as e:
        logger.error(f"Document retrieval error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving document")


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Pagination offset"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """List documents with optional filtering.

    Args:
        user_id: Filter by user ID
        document_type: Filter by document type
        status: Filter by status
        limit: Maximum number of results
        offset: Pagination offset
        user: Authenticated user

    Returns:
        List of document records
    """
    try:
        # If not admin, force filter by current user ID
        if not user.get("is_admin", False):
            user_id = user["id"]
            
        documents = await document_generator.list_documents(
            user_id=user_id,
            document_type=document_type,
            status=status,
            limit=limit,
            offset=offset
        )
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing documents")


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str = Path(..., description="Document ID"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Delete a document.

    Args:
        document_id: Document ID
        user: Authenticated user
    """
    try:
        # Get document to check ownership
        document = await document_generator.get_document(document_id)
        
        # Check if user has access to delete the document
        if document.get("user_id") != user["id"] and not user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Delete document
        success = await document_generator.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
    except DocumentGenerationError as e:
        logger.error(f"Document deletion error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting document")


@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """List document templates.

    Args:
        document_type: Filter by document type
        user: Authenticated user

    Returns:
        List of templates
    """
    try:
        templates = await document_generator.list_templates(document_type)
        return templates
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing templates")


@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreateRequest,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Create a new document template.

    Args:
        template_data: Template creation data
        user: Authenticated user

    Returns:
        Created template data
    """
    try:
        # Check if user has permission to create templates
        if not user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Only admins can create templates")
            
        # Add user ID to template data
        template_data_dict = template_data.dict()
        template_data_dict["user_id"] = user["id"]
        
        # Create template
        template_id = await document_generator.create_template(template_data_dict)
        
        # Return template data
        return {
            "id": template_id,
            "name": template_data.name,
            "type": template_data.type,
            "description": template_data.description,
            "created_at": template_data_dict.get("created_at", ""),
            "metadata": template_data.metadata
        }
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating template")


@router.post("/upload", response_model=Dict[str, Any])
async def upload_document_file(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Upload a document file.

    Args:
        file: Document file
        document_type: Document type
        title: Document title
        description: Optional document description
        metadata: Optional JSON string containing metadata
        user: Authenticated user

    Returns:
        Upload result with document details
    """
    try:
        # Validate document type
        valid_types = ["pdf", "presentation", "contract", "report", "newsletter", "form", "invoice"]
        if document_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid document type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Validate file content
        content_type = file.content_type
        file_extension = get_file_extension(file.filename)
        
        # Check file size (limit to 10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
        file_size = 0
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        # Seek back to beginning of file
        await file.seek(0)
        
        # Prepare metadata if provided
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON format")
        
        # Add file information to metadata
        metadata_dict.update({
            "original_filename": file.filename,
            "content_type": content_type,
            "file_size": file_size,
            "upload_date": datetime.now().isoformat()
        })
        
        # Generate a unique document ID
        document_id = f"doc_{uuid.uuid4().hex}"
        
        # Determine file extension based on document type
        target_extension = document_generator._get_file_extension(document_type)
        
        # Create directory if it doesn't exist
        document_dir = os.path.join(document_generator.document_base_path)
        os.makedirs(document_dir, exist_ok=True)
        
        # Create subdirectory for previews
        preview_dir = os.path.join(document_generator.document_base_path, "previews")
        os.makedirs(preview_dir, exist_ok=True)
        
        # Save the uploaded file
        file_path = os.path.join(document_dir, f"{document_id}.{target_extension}")
        with open(file_path, "wb") as f:
            # Write the file content we've already read
            f.write(file_content)
        
        # Generate file URL
        file_url = f"{document_generator.document_base_url}/{document_id}.{target_extension}"
        
        # Generate a preview (for demonstration, just adding a placeholder preview URL)
        preview_url = f"{document_generator.document_base_url}/previews/{document_id}_preview.png"
        
        # Create document record
        timestamp = datetime.utcnow().isoformat()
        document = {
            "id": document_id,
            "title": title,
            "description": description,
            "type": document_type,
            "user_id": user["id"],
            "status": "uploaded",
            "file_url": file_url,
            "preview_url": preview_url,
            "created_at": timestamp,
            "updated_at": timestamp,
            "metadata": metadata_dict
        }
        
        # Save document record
        document_generator.documents[document_id] = document
        await document_generator._save_json_db(document_generator.documents_db_path, document_generator.documents)
        
        # Initialize analytics for this document
        document_generator.analytics[document_id] = {
            "views": 0,
            "downloads": 0,
            "shares": 0,
            "last_viewed": None,
            "view_history": []
        }
        await document_generator._save_json_db(document_generator.analytics_db_path, document_generator.analytics)
        
        # Log document upload
        logger.info(f"Document uploaded: {document_id} ({title}) by user {user['id']}")
        
        return document
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename.
    
    Args:
        filename: Filename including extension
        
    Returns:
        File extension without the dot
    """
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


@router.get("/{document_id}/analytics", response_model=Dict[str, Any])
async def get_document_analytics(
    document_id: str = Path(..., description="Document ID"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get analytics for a document.

    Args:
        document_id: Document ID
        user: Authenticated user

    Returns:
        Document analytics data
    """
    try:
        # Get document to check ownership
        document = await document_generator.get_document(document_id)
        
        # Check if user has access to the document
        if document.get("user_id") != user["id"] and not user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Get analytics
        analytics = await document_generator.get_document_analytics(document_id)
        return analytics
    except DocumentGenerationError as e:
        logger.error(f"Document analytics error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving document analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving document analytics")


@router.post("/{document_id}/track-view", status_code=status.HTTP_204_NO_CONTENT)
async def track_document_view(
    view_data: Dict[str, Any],
    document_id: str = Path(..., description="Document ID")
):
    """Track a document view event.

    Args:
        view_data: View event data
        document_id: Document ID
    """
    try:
        await document_generator.track_document_view(document_id, view_data)
    except DocumentGenerationError as e:
        logger.error(f"Document view tracking error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error tracking document view: {str(e)}")
        raise HTTPException(status_code=500, detail="Error tracking document view")
