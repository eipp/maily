"""
Blockchain Router for Interactive Trust Verification

This router provides API endpoints for interacting with the blockchain verification system.
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import logging

from ..services.auth_service import get_current_user
from ..models.user import User
from ..services.blockchain_service import get_blockchain_service
from ..services.trust_verification_service import get_trust_verification_service

logger = logging.getLogger("api.routers.blockchain")

router = APIRouter(prefix="/v1/blockchain")

class VerifyContentRequest(BaseModel):
    """Request model for verifying content"""
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class CreateTokenRequest(BaseModel):
    """Request model for creating a token"""
    recipient: str
    metadata: Dict[str, Any]

class VerificationResponse(BaseModel):
    """Response model for verification operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

@router.post("/verify", response_model=VerificationResponse)
async def verify_content(
    request: VerifyContentRequest,
    current_user: User = Depends(get_current_user)
):
    """Verify content and store on blockchain"""
    try:
        # Get blockchain service
        blockchain_service = get_blockchain_service()
        
        # Generate content hash
        content_hash = blockchain_service.generate_content_hash(request.content)
        
        # Verify content on blockchain
        verification_data = await blockchain_service.verify_content(
            content_hash=content_hash,
            metadata=request.metadata,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Content verified successfully",
            "data": verification_data
        }
    except Exception as e:
        logger.error(f"Failed to verify content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verification/{content_hash}", response_model=VerificationResponse)
async def get_verification(
    content_hash: str,
    current_user: User = Depends(get_current_user)
):
    """Get verification data for a content hash"""
    try:
        # Get blockchain service
        blockchain_service = get_blockchain_service()
        
        # Get verification data
        verification_data = await blockchain_service.get_verification(content_hash)
        
        if not verification_data:
            return {
                "success": False,
                "message": "No verification data found for this content hash",
                "data": None
            }
        
        return {
            "success": True,
            "message": "Verification data retrieved successfully",
            "data": verification_data
        }
    except Exception as e:
        logger.error(f"Failed to get verification data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transaction/{transaction_id}", response_model=VerificationResponse)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get transaction details"""
    try:
        # Get blockchain service
        blockchain_service = get_blockchain_service()
        
        # Get transaction data
        transaction_data = await blockchain_service.get_transaction(transaction_id)
        
        if not transaction_data:
            return {
                "success": False,
                "message": f"Transaction {transaction_id} not found",
                "data": None
            }
        
        return {
            "success": True,
            "message": "Transaction retrieved successfully",
            "data": transaction_data
        }
    except Exception as e:
        logger.error(f"Failed to get transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/block/{block_number}", response_model=VerificationResponse)
async def get_block(
    block_number: int,
    current_user: User = Depends(get_current_user)
):
    """Get block details"""
    try:
        # Get blockchain service
        blockchain_service = get_blockchain_service()
        
        # Get block data
        block_data = await blockchain_service.get_block(block_number)
        
        if not block_data:
            return {
                "success": False,
                "message": f"Block {block_number} not found",
                "data": None
            }
        
        return {
            "success": True,
            "message": "Block retrieved successfully",
            "data": block_data
        }
    except Exception as e:
        logger.error(f"Failed to get block: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tokens", response_model=VerificationResponse)
async def create_token(
    request: CreateTokenRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a token for a recipient"""
    try:
        # Get blockchain service
        blockchain_service = get_blockchain_service()
        
        # Create token
        token_data = await blockchain_service.create_token(
            recipient=request.recipient,
            metadata=request.metadata,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Token created successfully",
            "data": token_data
        }
    except Exception as e:
        logger.error(f"Failed to create token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tokens/{token_id}", response_model=VerificationResponse)
async def get_token(
    token_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get token details"""
    try:
        # Get blockchain service
        blockchain_service = get_blockchain_service()
        
        # Get token data
        token_data = await blockchain_service.get_token(token_id)
        
        if not token_data:
            return {
                "success": False,
                "message": f"Token {token_id} not found",
                "data": None
            }
        
        return {
            "success": True,
            "message": "Token retrieved successfully",
            "data": token_data
        }
    except Exception as e:
        logger.error(f"Failed to get token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tokens", response_model=VerificationResponse)
async def get_tokens_for_recipient(
    recipient: str,
    current_user: User = Depends(get_current_user)
):
    """Get all tokens for a recipient"""
    try:
        # Get blockchain service
        blockchain_service = get_blockchain_service()
        
        # Get tokens
        tokens = await blockchain_service.get_tokens_for_recipient(recipient)
        
        return {
            "success": True,
            "message": f"Retrieved {len(tokens)} tokens",
            "data": {
                "tokens": tokens
            }
        }
    except Exception as e:
        logger.error(f"Failed to get tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-certificate", response_model=VerificationResponse)
async def verify_certificate(
    certificate_id: str = Body(...),
    content_hash: str = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Verify a certificate against the blockchain"""
    try:
        # Get blockchain service
        blockchain_service = get_blockchain_service()
        
        # Verify certificate
        verification_result = await blockchain_service.verify_certificate(
            certificate_id=certificate_id,
            content_hash=content_hash
        )
        
        return {
            "success": verification_result["verified"],
            "message": verification_result["message"],
            "data": verification_result.get("verification_data")
        }
    except Exception as e:
        logger.error(f"Failed to verify certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/canvas/{canvas_id}/verification", response_model=VerificationResponse)
async def get_canvas_verification(
    canvas_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get verification data for a canvas"""
    try:
        # Get trust verification service
        trust_service = get_trust_verification_service()
        
        # Get verification data
        verification_data = await trust_service.get_verification_data(canvas_id)
        
        return {
            "success": True,
            "message": "Verification data retrieved successfully",
            "data": verification_data
        }
    except Exception as e:
        logger.error(f"Failed to get canvas verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/canvas/{canvas_id}/verify", response_model=VerificationResponse)
async def verify_canvas(
    canvas_id: str,
    content: str = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Verify canvas content and store on blockchain"""
    try:
        # Get trust verification service
        trust_service = get_trust_verification_service()
        
        # Verify canvas content
        verification_data = await trust_service.verify_canvas_content(
            canvas_id=canvas_id,
            content=content,
            user_id=current_user.id
        )
        
        return {
            "success": verification_data["status"]["status"] == "verified",
            "message": verification_data["status"]["message"],
            "data": verification_data
        }
    except Exception as e:
        logger.error(f"Failed to verify canvas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/canvas/{canvas_id}/badge", response_model=VerificationResponse)
async def get_verification_badge(
    canvas_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get verification badge for a canvas"""
    try:
        # Get trust verification service
        trust_service = get_trust_verification_service()
        
        # Get verification badge
        badge = await trust_service.generate_verification_badge(canvas_id)
        
        return {
            "success": True,
            "message": "Verification badge generated successfully",
            "data": badge
        }
    except Exception as e:
        logger.error(f"Failed to get verification badge: {e}")
        raise HTTPException(status_code=500, detail=str(e))
