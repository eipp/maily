"""
MailyDocs Certificates Router

This router provides API endpoints for managing MailyDocs certificates.
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field

from ..services.auth_service import get_current_user
from ..models.user import User
from ..services.mailydocs_certificate_service import get_mailydocs_certificate_service, MailyDocsCertificate
from ..services.blockchain_service import get_blockchain_service

logger = logging.getLogger("api.routers.mailydocs_certificates")

router = APIRouter(prefix="/v1/mailydocs/certificates")

# Models
class CertificateRequest(BaseModel):
    """Request model for certificate generation"""
    document_id: str = Field(..., description="Document ID to certify")
    document_content: str = Field(..., description="Document content to hash and verify")
    document_type: str = Field("pdf", description="Document type (pdf, pptx, docx, etc.)")
    document_title: str = Field(..., description="Document title")
    issuer_name: Optional[str] = Field(None, description="Certificate issuer name")
    recipient_id: Optional[str] = Field(None, description="Recipient ID")
    recipient_name: Optional[str] = Field(None, description="Recipient name")
    expires_at: Optional[datetime] = Field(None, description="Certificate expiration date")
    additional_data: Optional[Dict[str, Any]] = Field({}, description="Additional certificate metadata")

class VerificationRequest(BaseModel):
    """Request model for certificate verification"""
    certificate_id: str = Field(..., description="Certificate ID")
    content_hash: Optional[str] = Field(None, description="Document content hash")
    document_content: Optional[str] = Field(None, description="Raw document content to verify")

class CertificateResponse(BaseModel):
    """Response model for certificate operations"""
    success: bool
    message: str
    certificate: Optional[Dict[str, Any]] = None

class VerificationResponse(BaseModel):
    """Response model for verification operations"""
    verified: bool
    message: str
    certificate: Optional[Dict[str, Any]] = None
    blockchain_verification: Optional[Dict[str, Any]] = None
    timestamp: str

class RevocationRequest(BaseModel):
    """Request model for certificate revocation"""
    reason: str = Field(..., description="Reason for revocation")

# Endpoints
@router.post("/generate", response_model=CertificateResponse)
async def generate_certificate(
    request: CertificateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Generate a certificate for a MailyDocs document"""
    try:
        certificate_service = get_mailydocs_certificate_service()
        
        # Build certificate metadata
        metadata = {
            "document_type": request.document_type,
            "document_title": request.document_title,
            "issuer_name": request.issuer_name,
            "recipient_id": request.recipient_id,
            "recipient_name": request.recipient_name,
            "expires_at": request.expires_at,
            "additional_data": request.additional_data
        }
        
        # Generate certificate
        certificate = await certificate_service.generate_certificate(
            document_id=request.document_id,
            document_content=request.document_content,
            metadata=metadata,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Certificate generated successfully",
            "certificate": certificate.dict()
        }
    
    except Exception as e:
        logger.error(f"Certificate generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate certificate: {str(e)}"
        )

@router.post("/verify", response_model=VerificationResponse)
async def verify_certificate(
    request: VerificationRequest,
    current_user: User = Depends(get_current_user)
):
    """Verify a MailyDocs certificate"""
    try:
        certificate_service = get_mailydocs_certificate_service()
        blockchain_service = get_blockchain_service()
        
        # Ensure we have either a content hash or document content
        content_hash = request.content_hash
        if not content_hash and request.document_content:
            content_hash = blockchain_service.generate_content_hash(request.document_content)
        
        if not content_hash:
            raise HTTPException(
                status_code=400,
                detail="Either content_hash or document_content must be provided"
            )
        
        # Verify certificate
        verification_result = await certificate_service.verify_certificate(
            certificate_id=request.certificate_id,
            content_hash=content_hash
        )
        
        return verification_result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Certificate verification failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify certificate: {str(e)}"
        )

@router.get("/{certificate_id}", response_model=CertificateResponse)
async def get_certificate(
    certificate_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get certificate details"""
    try:
        certificate_service = get_mailydocs_certificate_service()
        
        # Get certificate
        certificate = await certificate_service.get_certificate(certificate_id)
        
        if not certificate:
            raise HTTPException(
                status_code=404,
                detail=f"Certificate {certificate_id} not found"
            )
        
        return {
            "success": True,
            "message": "Certificate retrieved successfully",
            "certificate": certificate.dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving certificate: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve certificate: {str(e)}"
        )

@router.post("/{certificate_id}/revoke", response_model=CertificateResponse)
async def revoke_certificate(
    certificate_id: str,
    request: RevocationRequest,
    current_user: User = Depends(get_current_user)
):
    """Revoke a certificate"""
    try:
        certificate_service = get_mailydocs_certificate_service()
        
        # Revoke certificate
        success = await certificate_service.revoke_certificate(
            certificate_id=certificate_id,
            reason=request.reason,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Certificate {certificate_id} not found or could not be revoked"
            )
        
        return {
            "success": True,
            "message": "Certificate revoked successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking certificate: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revoke certificate: {str(e)}"
        )

@router.get("/document/{document_id}", response_model=CertificateResponse)
async def get_certificates_for_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all certificates for a document"""
    try:
        certificate_service = get_mailydocs_certificate_service()
        
        # Get certificates
        certificates = await certificate_service.get_certificates_for_document(document_id)
        
        return {
            "success": True,
            "message": f"Retrieved {len(certificates)} certificates",
            "certificate": {
                "document_id": document_id,
                "certificates": [cert.dict() for cert in certificates]
            }
        }
    
    except Exception as e:
        logger.error(f"Error retrieving certificates for document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve certificates: {str(e)}"
        )