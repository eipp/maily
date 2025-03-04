"""
MailyDocs Certificate Generation Service

This service handles the generation of blockchain-verified certificates for MailyDocs documents.
"""

import logging
import hashlib
import base64
import json
import io
import os
import qrcode
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..cache.redis_client import get_redis_client
from ..utils.resilience import circuit_breaker, retry_with_backoff
from .blockchain_service import get_blockchain_service
from .trust_verification_service import get_trust_verification_service
from ..utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger("api.services.mailydocs_certificate")

class CertificateMetadata(BaseModel):
    """Certificate metadata model"""
    document_id: str
    document_type: str
    document_title: str
    issuer_id: str
    issuer_name: str
    recipient_id: Optional[str] = None
    recipient_name: Optional[str] = None
    issued_at: datetime
    expires_at: Optional[datetime] = None
    additional_data: Optional[Dict[str, Any]] = None

class CertificateStatus(BaseModel):
    """Certificate status model"""
    status: str  # draft, active, revoked, expired
    created_at: datetime
    updated_at: datetime
    reason: Optional[str] = None

class MailyDocsCertificate(BaseModel):
    """MailyDocs certificate model"""
    id: str
    document_id: str
    content_hash: str
    metadata: CertificateMetadata
    status: CertificateStatus
    blockchain_id: Optional[str] = None
    blockchain_transaction: Optional[Dict[str, Any]] = None
    verification_url: Optional[str] = None
    qr_code: Optional[str] = None

class MailyDocsCertificateService:
    """Service for generating and managing MailyDocs certificates"""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.blockchain_service = get_blockchain_service()
        self.trust_verification_service = get_trust_verification_service()
        self.certificate_base_url = os.environ.get("CERTIFICATE_BASE_URL", "https://verify.maily.example.com")
        
        logger.info("MailyDocs Certificate Service initialized")
    
    async def generate_certificate(
        self,
        document_id: str,
        document_content: str,
        metadata: Dict[str, Any],
        user_id: str
    ) -> MailyDocsCertificate:
        """Generate a certificate for a MailyDocs document
        
        Args:
            document_id: The document ID
            document_content: The document content to hash and verify
            metadata: Certificate metadata
            user_id: User ID generating the certificate
            
        Returns:
            The generated certificate
        """
        try:
            logger.info(f"Generating certificate for document {document_id}")
            
            # Generate content hash
            content_hash = self.blockchain_service.generate_content_hash(document_content)
            
            # Create certificate ID
            certificate_id = f"cert-{hashlib.sha256(f'{document_id}:{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"
            
            # Create certificate metadata
            cert_metadata = CertificateMetadata(
                document_id=document_id,
                document_type=metadata.get("document_type", "pdf"),
                document_title=metadata.get("document_title", "Untitled Document"),
                issuer_id=user_id,
                issuer_name=metadata.get("issuer_name", "Maily User"),
                recipient_id=metadata.get("recipient_id"),
                recipient_name=metadata.get("recipient_name"),
                issued_at=datetime.utcnow(),
                expires_at=metadata.get("expires_at"),
                additional_data=metadata.get("additional_data", {})
            )
            
            # Create certificate status
            cert_status = CertificateStatus(
                status="draft",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Create certificate
            certificate = MailyDocsCertificate(
                id=certificate_id,
                document_id=document_id,
                content_hash=content_hash,
                metadata=cert_metadata,
                status=cert_status
            )
            
            # Store in Redis (temporary until blockchain verification completes)
            await self._store_certificate(certificate)
            
            # Verify on blockchain in background
            await self._verify_on_blockchain(certificate, document_content, user_id)
            
            # Generate verification URL and QR code
            verification_url = f"{self.certificate_base_url}/verify/{certificate_id}"
            qr_code = await self._generate_verification_qr(certificate_id, content_hash)
            
            # Update certificate with verification details
            certificate.verification_url = verification_url
            certificate.qr_code = qr_code
            
            # Update certificate in Redis
            await self._store_certificate(certificate)
            
            logger.info(f"Certificate {certificate_id} generated for document {document_id}")
            
            return certificate
            
        except Exception as e:
            logger.error(f"Error generating certificate: {e}")
            raise Exception(f"Failed to generate certificate: {str(e)}")
    
    @circuit_breaker(failure_threshold=5, reset_timeout=300)
    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=10)
    async def _verify_on_blockchain(
        self,
        certificate: MailyDocsCertificate,
        document_content: str,
        user_id: str
    ) -> None:
        """Verify certificate on blockchain
        
        Args:
            certificate: The certificate to verify
            document_content: The document content
            user_id: User ID generating the certificate
        """
        try:
            logger.info(f"Verifying certificate {certificate.id} on blockchain")
            
            # Prepare metadata for blockchain
            blockchain_metadata = {
                "certificate_id": certificate.id,
                "document_id": certificate.document_id,
                "document_type": certificate.metadata.document_type,
                "document_title": certificate.metadata.document_title,
                "issuer_id": certificate.metadata.issuer_id,
                "issuer_name": certificate.metadata.issuer_name,
                "recipient_id": certificate.metadata.recipient_id,
                "recipient_name": certificate.metadata.recipient_name,
                "issued_at": certificate.metadata.issued_at.isoformat(),
                "expires_at": certificate.metadata.expires_at.isoformat() if certificate.metadata.expires_at else None,
                "verification_type": "mailydocs_certificate"
            }
            
            # Store content on blockchain
            blockchain_verification = await self.blockchain_service.verify_content(
                content_hash=certificate.content_hash,
                metadata=blockchain_metadata,
                user_id=user_id
            )
            
            # Create token on blockchain
            recipient = certificate.metadata.recipient_id or "public"
            token_metadata = {
                "certificate_id": certificate.id,
                "document_id": certificate.document_id,
                "content_hash": certificate.content_hash,
                "certificate_type": "mailydocs",
                "issuer_id": certificate.metadata.issuer_id,
                "issuer_name": certificate.metadata.issuer_name
            }
            
            blockchain_token = await self.blockchain_service.create_token(
                recipient=recipient,
                metadata=token_metadata,
                user_id=user_id
            )
            
            # Update certificate with blockchain details
            certificate.blockchain_id = blockchain_token.get("id")
            certificate.blockchain_transaction = {
                "transaction_id": blockchain_verification.get("transaction_id"),
                "block_number": blockchain_verification.get("block_number"),
                "timestamp": blockchain_verification.get("timestamp"),
                "network": blockchain_verification.get("network"),
                "contract_address": blockchain_verification.get("contract_address"),
                "token_id": blockchain_token.get("id")
            }
            
            # Update certificate status
            certificate.status = CertificateStatus(
                status="active",
                created_at=certificate.status.created_at,
                updated_at=datetime.utcnow()
            )
            
            # Update certificate in Redis
            await self._store_certificate(certificate)
            
            logger.info(f"Certificate {certificate.id} verified on blockchain")
            
        except Exception as e:
            logger.error(f"Error verifying certificate on blockchain: {e}")
            
            # Update certificate status to reflect error
            certificate.status = CertificateStatus(
                status="error",
                created_at=certificate.status.created_at,
                updated_at=datetime.utcnow(),
                reason=str(e)
            )
            
            # Update certificate in Redis
            await self._store_certificate(certificate)
            
            # Re-raise exception
            raise
    
    async def get_certificate(self, certificate_id: str) -> Optional[MailyDocsCertificate]:
        """Get certificate by ID
        
        Args:
            certificate_id: Certificate ID
            
        Returns:
            Certificate if found, None otherwise
        """
        try:
            # Get certificate from Redis
            certificate_key = f"mailydocs:certificate:{certificate_id}"
            certificate_data = await self.redis.get(certificate_key)
            
            if not certificate_data:
                logger.warning(f"Certificate {certificate_id} not found")
                return None
            
            # Parse certificate data
            certificate_dict = json.loads(certificate_data)
            
            # Convert to MailyDocsCertificate model
            certificate = MailyDocsCertificate.parse_obj(certificate_dict)
            
            return certificate
            
        except Exception as e:
            logger.error(f"Error getting certificate: {e}")
            return None
    
    async def verify_certificate(
        self,
        certificate_id: str,
        content_hash: str
    ) -> Dict[str, Any]:
        """Verify certificate against document content
        
        Args:
            certificate_id: Certificate ID
            content_hash: Document content hash
            
        Returns:
            Verification result
        """
        try:
            # Get certificate
            certificate = await self.get_certificate(certificate_id)
            
            if not certificate:
                return {
                    "verified": False,
                    "message": f"Certificate {certificate_id} not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Check if content hash matches
            if certificate.content_hash != content_hash:
                return {
                    "verified": False,
                    "message": "Content hash does not match certificate",
                    "timestamp": datetime.utcnow().isoformat(),
                    "certificate": certificate.dict()
                }
            
            # Check certificate status
            if certificate.status.status != "active":
                return {
                    "verified": False,
                    "message": f"Certificate is not active (status: {certificate.status.status})",
                    "timestamp": datetime.utcnow().isoformat(),
                    "certificate": certificate.dict()
                }
            
            # Check if certificate has expired
            if certificate.metadata.expires_at and datetime.utcnow() > certificate.metadata.expires_at:
                return {
                    "verified": False,
                    "message": "Certificate has expired",
                    "timestamp": datetime.utcnow().isoformat(),
                    "certificate": certificate.dict()
                }
            
            # If certificate has blockchain verification, verify on blockchain
            if certificate.blockchain_id:
                try:
                    blockchain_verification = await self.blockchain_service.verify_certificate(
                        certificate_id=certificate.blockchain_id,
                        content_hash=content_hash
                    )
                    
                    if not blockchain_verification.get("verified", False):
                        return {
                            "verified": False,
                            "message": "Blockchain verification failed",
                            "blockchain_message": blockchain_verification.get("message"),
                            "timestamp": datetime.utcnow().isoformat(),
                            "certificate": certificate.dict()
                        }
                        
                except Exception as e:
                    logger.error(f"Blockchain verification error: {e}")
                    # Continue with local verification even if blockchain verification fails
            
            # If we got here, certificate is valid
            return {
                "verified": True,
                "message": "Certificate verified successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "certificate": certificate.dict(),
                "blockchain_verification": certificate.blockchain_transaction
            }
            
        except Exception as e:
            logger.error(f"Error verifying certificate: {e}")
            return {
                "verified": False,
                "message": f"Error verifying certificate: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def revoke_certificate(
        self,
        certificate_id: str,
        reason: str,
        user_id: str
    ) -> bool:
        """Revoke a certificate
        
        Args:
            certificate_id: Certificate ID
            reason: Revocation reason
            user_id: User ID revoking the certificate
            
        Returns:
            True if certificate was revoked, False otherwise
        """
        try:
            # Get certificate
            certificate = await self.get_certificate(certificate_id)
            
            if not certificate:
                logger.warning(f"Certificate {certificate_id} not found for revocation")
                return False
            
            # Check if certificate belongs to user or user is admin
            # In a real implementation, check user permissions
            
            # Update certificate status
            certificate.status = CertificateStatus(
                status="revoked",
                created_at=certificate.status.created_at,
                updated_at=datetime.utcnow(),
                reason=reason
            )
            
            # Update certificate in Redis
            await self._store_certificate(certificate)
            
            # If certificate has blockchain ID, attempt to revoke on blockchain
            # This would require an additional method on blockchain_service
            
            logger.info(f"Certificate {certificate_id} revoked by user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error revoking certificate: {e}")
            return False
    
    async def get_certificates_for_document(
        self,
        document_id: str
    ) -> List[MailyDocsCertificate]:
        """Get all certificates for a document
        
        Args:
            document_id: Document ID
            
        Returns:
            List of certificates
        """
        try:
            # Get certificate IDs for document
            document_certs_key = f"mailydocs:document_certificates:{document_id}"
            certificate_ids = await self.redis.get(document_certs_key)
            
            if not certificate_ids:
                return []
            
            # Parse certificate IDs
            cert_ids = json.loads(certificate_ids)
            
            # Get certificates
            certificates = []
            for cert_id in cert_ids:
                certificate = await self.get_certificate(cert_id)
                if certificate:
                    certificates.append(certificate)
            
            return certificates
            
        except Exception as e:
            logger.error(f"Error getting certificates for document: {e}")
            return []
    
    async def _store_certificate(self, certificate: MailyDocsCertificate) -> None:
        """Store certificate in Redis
        
        Args:
            certificate: Certificate to store
        """
        try:
            # Convert certificate to dict
            certificate_dict = certificate.dict()
            
            # Store certificate
            certificate_key = f"mailydocs:certificate:{certificate.id}"
            await self.redis.set(
                certificate_key,
                json.dumps(certificate_dict),
                expire=86400 * 365  # 1 year
            )
            
            # Add certificate ID to document certificates
            document_certs_key = f"mailydocs:document_certificates:{certificate.document_id}"
            certificate_ids = await self.redis.get(document_certs_key)
            
            if certificate_ids:
                cert_ids = json.loads(certificate_ids)
                if certificate.id not in cert_ids:
                    cert_ids.append(certificate.id)
            else:
                cert_ids = [certificate.id]
                
            await self.redis.set(
                document_certs_key,
                json.dumps(cert_ids),
                expire=86400 * 365  # 1 year
            )
            
        except Exception as e:
            logger.error(f"Error storing certificate: {e}")
            raise
    
    async def _generate_verification_qr(self, certificate_id: str, content_hash: str) -> str:
        """Generate QR code for certificate verification
        
        Args:
            certificate_id: Certificate ID
            content_hash: Content hash
            
        Returns:
            QR code as base64 data URL
        """
        try:
            # Create verification URL
            verification_url = f"{self.certificate_base_url}/verify/{certificate_id}?hash={content_hash}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{qr_base64}"
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            return ""

# Singleton instance
_instance = None

def get_mailydocs_certificate_service():
    """Get singleton instance of MailyDocsCertificateService"""
    global _instance
    if _instance is None:
        _instance = MailyDocsCertificateService()
    return _instance