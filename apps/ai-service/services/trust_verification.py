"""
Interactive Trust Verification Service

This service provides blockchain-based verification with interactive certificates,
QR codes, and token rewards.
"""

import logging
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..utils.redis_client import get_redis_client
from ..utils.database import db_create_certificate, db_get_certificate, db_update_certificate, db_delete_certificate, db_list_certificates

logger = logging.getLogger("ai_service.services.trust_verification")

# Constants
CERTIFICATE_KEY_PREFIX = "trust_verification:certificate:"
TOKEN_KEY_PREFIX = "trust_verification:token:"
QR_CODE_KEY_PREFIX = "trust_verification:qr_code:"
VERIFICATION_STATUS = ["pending", "verified", "rejected", "expired"]

class TrustVerification:
    """Service for blockchain-based verification with interactive certificates"""
    
    def __init__(self):
        self.redis = get_redis_client()
    
    async def create_certificate(
        self,
        email_id: str,
        campaign_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new verification certificate"""
        try:
            # Generate certificate ID
            certificate_id = f"cert_{uuid.uuid4().hex[:8]}"
            
            # Create certificate object
            certificate = {
                "id": certificate_id,
                "email_id": email_id,
                "campaign_id": campaign_id,
                "user_id": user_id,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "status": "pending",
                "blockchain_tx": None,
                "verification_count": 0,
                "token_rewards": [],
                "qr_codes": []
            }
            
            # Store certificate in Redis for fast access
            certificate_key = f"{CERTIFICATE_KEY_PREFIX}{certificate_id}"
            await self.redis.set(certificate_key, json.dumps(certificate), ex=86400)  # 24 hour cache
            
            # Store certificate in database for persistence
            await db_create_certificate(certificate)
            
            # Generate QR code for the certificate
            qr_code_id = await self._generate_qr_code(certificate_id)
            
            # Update certificate with QR code
            certificate["qr_codes"].append(qr_code_id)
            await self.redis.set(certificate_key, json.dumps(certificate), ex=86400)
            await db_update_certificate(certificate)
            
            return certificate_id
            
        except Exception as e:
            logger.error(f"Failed to create certificate: {e}")
            raise
    
    async def get_certificate(self, certificate_id: str) -> Optional[Dict[str, Any]]:
        """Get a verification certificate by ID"""
        try:
            # Try to get certificate from Redis first
            certificate_key = f"{CERTIFICATE_KEY_PREFIX}{certificate_id}"
            certificate_data = await self.redis.get(certificate_key)
            
            if certificate_data:
                return json.loads(certificate_data)
            
            # If not in Redis, get from database
            certificate = await db_get_certificate(certificate_id)
            
            if certificate:
                # Cache in Redis for future requests
                await self.redis.set(certificate_key, json.dumps(certificate), ex=86400)  # 24 hour cache
            
            return certificate
            
        except Exception as e:
            logger.error(f"Failed to get certificate: {e}")
            return None
    
    async def verify_certificate(
        self,
        certificate_id: str,
        verification_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Verify a certificate on the blockchain"""
        try:
            # Get current certificate
            certificate = await self.get_certificate(certificate_id)
            
            if not certificate:
                return False
            
            # Simulate blockchain verification
            # In a real implementation, this would interact with the blockchain
            blockchain_tx = f"0x{uuid.uuid4().hex}"
            
            # Update certificate
            certificate["status"] = "verified"
            certificate["blockchain_tx"] = blockchain_tx
            certificate["verification_count"] += 1
            certificate["updated_at"] = datetime.utcnow().isoformat()
            
            if verification_data:
                if "metadata" not in certificate:
                    certificate["metadata"] = {}
                certificate["metadata"]["verification_data"] = verification_data
            
            # Update in Redis
            certificate_key = f"{CERTIFICATE_KEY_PREFIX}{certificate_id}"
            await self.redis.set(certificate_key, json.dumps(certificate), ex=86400)  # 24 hour cache
            
            # Update in database
            await db_update_certificate(certificate)
            
            # Generate token reward
            token_id = await self._generate_token_reward(certificate_id)
            
            # Update certificate with token reward
            certificate["token_rewards"].append(token_id)
            await self.redis.set(certificate_key, json.dumps(certificate), ex=86400)
            await db_update_certificate(certificate)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify certificate: {e}")
            return False
    
    async def get_certificate_by_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get a verification certificate by email ID"""
        try:
            # This would typically query the database
            # For now, we'll simulate by listing all certificates and filtering
            certificates = await db_list_certificates()
            
            for cert in certificates:
                if cert["email_id"] == email_id:
                    # Cache in Redis for future requests
                    certificate_key = f"{CERTIFICATE_KEY_PREFIX}{cert['id']}"
                    await self.redis.set(certificate_key, json.dumps(cert), ex=86400)  # 24 hour cache
                    return cert
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get certificate by email: {e}")
            return None
    
    async def get_certificate_by_qr_code(self, qr_code_id: str) -> Optional[Dict[str, Any]]:
        """Get a verification certificate by QR code ID"""
        try:
            # Get QR code data
            qr_code_key = f"{QR_CODE_KEY_PREFIX}{qr_code_id}"
            qr_code_data = await self.redis.get(qr_code_key)
            
            if not qr_code_data:
                return None
            
            qr_code = json.loads(qr_code_data)
            certificate_id = qr_code["certificate_id"]
            
            # Get certificate
            return await self.get_certificate(certificate_id)
            
        except Exception as e:
            logger.error(f"Failed to get certificate by QR code: {e}")
            return None
    
    async def list_certificates(
        self,
        user_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List verification certificates"""
        try:
            # Get certificates from database
            certificates = await db_list_certificates(user_id, campaign_id, status, limit, offset)
            
            # Cache in Redis for future requests
            for cert in certificates:
                certificate_key = f"{CERTIFICATE_KEY_PREFIX}{cert['id']}"
                await self.redis.set(certificate_key, json.dumps(cert), ex=86400)  # 24 hour cache
            
            return certificates
            
        except Exception as e:
            logger.error(f"Failed to list certificates: {e}")
            return []
    
    async def get_token_balance(self, user_id: str) -> int:
        """Get token balance for a user"""
        try:
            # This would typically query the blockchain or a database
            # For now, we'll simulate by counting tokens
            tokens = await self._list_tokens_by_user(user_id)
            return len(tokens)
            
        except Exception as e:
            logger.error(f"Failed to get token balance: {e}")
            return 0
    
    async def transfer_token(
        self,
        token_id: str,
        from_user_id: str,
        to_user_id: str
    ) -> bool:
        """Transfer a token from one user to another"""
        try:
            # Get token data
            token_key = f"{TOKEN_KEY_PREFIX}{token_id}"
            token_data = await self.redis.get(token_key)
            
            if not token_data:
                return False
            
            token = json.loads(token_data)
            
            # Verify ownership
            if token["user_id"] != from_user_id:
                return False
            
            # Update token
            token["user_id"] = to_user_id
            token["updated_at"] = datetime.utcnow().isoformat()
            token["transfer_history"].append({
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update in Redis
            await self.redis.set(token_key, json.dumps(token), ex=86400)  # 24 hour cache
            
            # In a real implementation, this would update the database and blockchain
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer token: {e}")
            return False
    
    async def _generate_qr_code(self, certificate_id: str) -> str:
        """Generate a QR code for a certificate"""
        try:
            # Generate QR code ID
            qr_code_id = f"qr_{uuid.uuid4().hex[:8]}"
            
            # Get base URL (or use production URL default)
            import os
            base_url = os.environ.get('VERIFICATION_BASE_URL', 'https://verify.maily.ai')
            
            # Create QR code object
            qr_code = {
                "id": qr_code_id,
                "certificate_id": certificate_id,
                "created_at": datetime.utcnow().isoformat(),
                "url": f"{base_url}/qr/{qr_code_id}",
                "scan_count": 0,
                "last_scanned_at": None
            }
            
            # Store QR code in Redis
            qr_code_key = f"{QR_CODE_KEY_PREFIX}{qr_code_id}"
            await self.redis.set(qr_code_key, json.dumps(qr_code), ex=86400)  # 24 hour cache
            
            # In a real implementation, this would also store in the database
            
            return qr_code_id
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            raise
    
    async def _generate_token_reward(self, certificate_id: str) -> str:
        """Generate a token reward for a verified certificate"""
        try:
            # Get certificate
            certificate = await self.get_certificate(certificate_id)
            
            if not certificate:
                raise ValueError(f"Certificate not found: {certificate_id}")
            
            # Generate token ID
            token_id = f"token_{uuid.uuid4().hex[:8]}"
            
            # Create token object
            token = {
                "id": token_id,
                "certificate_id": certificate_id,
                "user_id": certificate["user_id"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "value": 1,  # Simple token value
                "blockchain_tx": certificate["blockchain_tx"],
                "transfer_history": []
            }
            
            # Store token in Redis
            token_key = f"{TOKEN_KEY_PREFIX}{token_id}"
            await self.redis.set(token_key, json.dumps(token), ex=86400)  # 24 hour cache
            
            # In a real implementation, this would also store in the database
            # and interact with the blockchain
            
            return token_id
            
        except Exception as e:
            logger.error(f"Failed to generate token reward: {e}")
            raise
    
    async def _list_tokens_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """List tokens owned by a user"""
        try:
            # This would typically query the database
            # For now, we'll simulate by scanning Redis keys
            token_keys = await self.redis.keys(f"{TOKEN_KEY_PREFIX}*")
            tokens = []
            
            for key in token_keys:
                token_data = await self.redis.get(key)
                if token_data:
                    token = json.loads(token_data)
                    if token["user_id"] == user_id:
                        tokens.append(token)
            
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to list tokens by user: {e}")
            return []

# Singleton instance
_trust_verification_instance = None

def get_trust_verification():
    """Get the singleton instance of TrustVerification"""
    global _trust_verification_instance
    if _trust_verification_instance is None:
        _trust_verification_instance = TrustVerification()
    return _trust_verification_instance
