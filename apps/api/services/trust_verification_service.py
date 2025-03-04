"""
Trust Verification Service for Cognitive Canvas

This service provides blockchain-based verification for email content
created with Cognitive Canvas.
"""

import json
import logging
import hashlib
import base64
import qrcode
import io
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel

from packages.database.src.redis import get_redis_client, RedisClient
from ..utils.encryption import encrypt_data, decrypt_data
from ..services.blockchain_service import get_blockchain_service
from ..utils.concurrent_verification import (
    verify_concurrently, 
    verify_with_fallback,
    CircuitBreaker,
    batch_verify,
    VerificationResult
)

logger = logging.getLogger("api.services.trust_verification")

class VerificationStatus(BaseModel):
    """Verification status model"""
    status: str  # unverified, pending, verified, failed
    timestamp: datetime
    message: Optional[str] = None
    
class Certificate(BaseModel):
    """Certificate model"""
    id: str
    issuer: str
    subject: str
    issued_at: datetime
    expires_at: Optional[datetime] = None
    content_hash: str
    signature: str
    
class BlockchainRecord(BaseModel):
    """Blockchain record model"""
    transaction_id: str
    block_number: Optional[int] = None
    timestamp: Optional[datetime] = None
    network: str
    contract_address: str

class TrustVerificationService:
    """Service for providing trust verification"""
    
    def __init__(self):
        self.redis = None  # Will be initialized in initialize() method
        self.blockchain_service = get_blockchain_service()
        self.verification_cache = {}
        self.cache_expiration = 3600  # 1 hour in seconds
        self.certificate_verification_circuit_breaker = CircuitBreaker(failure_threshold=5, reset_timeout=300)
        
    async def initialize(self):
        """Initialize the service with Redis client"""
        self.redis = await get_redis_client()
        logger.info("Trust verification service initialized")
        
    async def get_verification_status(self, canvas_id: str) -> Dict[str, Any]:
        """Get verification status for a canvas"""
        try:
            # Get status from Redis
            status_key = f"canvas:{canvas_id}:verification_status"
            status_data = await self.redis.get(status_key)
            
            if not status_data:
                # Initialize default status if not exists
                default_status = {
                    "status": "unverified",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Content has not been verified yet."
                }
                
                # Store default status
                await self.redis.set(
                    status_key, 
                    json.dumps(default_status),
                    expire=86400 * 30  # 30 days
                )
                
                return default_status
            
            # Parse status data
            return json.loads(status_data)
            
        except Exception as e:
            logger.error(f"Failed to get verification status: {e}")
            # Return default status on error
            return {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Error retrieving verification status: {str(e)}"
            }
    
    async def verify_canvas_content(
        self, 
        canvas_id: str,
        content: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Verify canvas content and store on blockchain"""
        try:
            # Generate content hash
            content_hash = self.blockchain_service.generate_content_hash(content)
            
            # Create certificate
            certificate_id = f"cert-{hashlib.sha256(f'{canvas_id}:{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"
            certificate = {
                "id": certificate_id,
                "issuer": "Maily Trust Authority",
                "subject": f"Canvas {canvas_id}",
                "issued_at": datetime.utcnow().isoformat(),
                "expires_at": None,  # No expiration
                "content_hash": content_hash,
                "signature": f"0x{hashlib.sha256(f'signature:{content_hash}'.encode()).hexdigest()}"
            }
            
            # Store content hash on blockchain
            blockchain_record = await self.blockchain_service.verify_content(
                content_hash=content_hash,
                metadata={
                    "canvas_id": canvas_id,
                    "certificate_id": certificate_id,
                    "issuer": "Maily Trust Authority",
                    "verification_type": "email_content"
                },
                user_id=user_id
            )
            
            # Update verification status
            verification_status = {
                "status": "verified",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Content has been verified and recorded on the blockchain."
            }
            
            # Store verification data
            status_key = f"canvas:{canvas_id}:verification_status"
            cert_key = f"canvas:{canvas_id}:certificate"
            blockchain_key = f"canvas:{canvas_id}:blockchain"
            
            await self.redis.set(
                status_key, 
                json.dumps(verification_status),
                expire=86400 * 30  # 30 days
            )
            
            await self.redis.set(
                cert_key, 
                json.dumps(certificate),
                expire=86400 * 30  # 30 days
            )
            
            await self.redis.set(
                blockchain_key, 
                json.dumps(blockchain_record),
                expire=86400 * 30  # 30 days
            )
            
            # Generate verification data for visualization
            verification_data = {
                "status": verification_status,
                "certificate": certificate,
                "blockchain": blockchain_record,
                "qr_code": await self._generate_verification_qr(canvas_id, content_hash)
            }
            
            return verification_data
            
        except Exception as e:
            logger.error(f"Failed to verify canvas content: {e}")
            
            # Update verification status to failed
            failed_status = {
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Verification failed: {str(e)}"
            }
            
            status_key = f"canvas:{canvas_id}:verification_status"
            await self.redis.set(
                status_key, 
                json.dumps(failed_status),
                expire=86400 * 30  # 30 days
            )
            
            # Return failed status
            return {
                "status": failed_status,
                "certificate": None,
                "blockchain": None,
                "qr_code": None
            }
    
    async def get_verification_data(self, canvas_id: str) -> Dict[str, Any]:
        """Get complete verification data for a canvas using parallel operations"""
        try:
            # Check cache first
            cache_key = f"verification_data:{canvas_id}"
            if cache_key in self.verification_cache:
                cached_data, timestamp = self.verification_cache[cache_key]
                if (datetime.utcnow() - timestamp).total_seconds() < self.cache_expiration:
                    logger.info(f"Using cached verification data for canvas {canvas_id}")
                    return cached_data
            
            # Define async tasks for parallel execution
            async def get_status():
                status_key = f"canvas:{canvas_id}:verification_status"
                status_data = await self.redis.get(status_key)
                if status_data:
                    return json.loads(status_data)
                return {
                    "status": "unverified",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Content has not been verified yet."
                }
            
            async def get_certificate():
                cert_key = f"canvas:{canvas_id}:certificate"
                cert_data = await self.redis.get(cert_key)
                return json.loads(cert_data) if cert_data else None
            
            async def get_blockchain_data(content_hash):
                verification_data = await self.blockchain_service.get_verification(content_hash)
                if verification_data:
                    return {
                        "transaction_id": verification_data.get("transaction_id"),
                        "block_number": verification_data.get("block_number"),
                        "timestamp": verification_data.get("timestamp"),
                        "network": verification_data.get("network"),
                        "contract_address": verification_data.get("contract_address")
                    }
                return None
            
            # Execute status and certificate retrieval in parallel
            status_task = asyncio.create_task(get_status())
            certificate_task = asyncio.create_task(get_certificate())
            
            # Wait for both to complete
            status, certificate = await asyncio.gather(status_task, certificate_task)
            
            # Conditionally get blockchain data and generate QR code in parallel
            blockchain = None
            qr_code = None
            
            if certificate and certificate.get("content_hash"):
                content_hash = certificate.get("content_hash")
                blockchain_task = asyncio.create_task(get_blockchain_data(content_hash))
                qr_task = asyncio.create_task(self._generate_verification_qr(canvas_id, content_hash))
                
                blockchain, qr_code = await asyncio.gather(blockchain_task, qr_task)
            
            # Construct result
            result = {
                "status": status,
                "certificate": certificate,
                "blockchain": blockchain,
                "qr_code": qr_code
            }
            
            # Cache result
            self.verification_cache[cache_key] = (result, datetime.utcnow())
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get verification data: {e}")
            # Return default data on error
            return {
                "status": {
                    "status": "error",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Error retrieving verification data: {str(e)}"
                },
                "certificate": None,
                "blockchain": None,
                "qr_code": None
            }
    
    async def generate_verification_badge(self, canvas_id: str) -> Dict[str, Any]:
        """Generate verification badge for embedding in emails"""
        try:
            # Get verification data
            verification_data = await self.get_verification_data(canvas_id)
            
            # Generate badge data
            badge = {
                "verified": verification_data["status"]["status"] == "verified",
                "issuer": verification_data.get("certificate", {}).get("issuer", "Maily Trust Authority"),
                "timestamp": verification_data["status"]["timestamp"],
                "verification_url": f"https://verify.maily.example.com/{canvas_id}",
                "qr_code": verification_data["qr_code"]
            }
            
            return badge
            
        except Exception as e:
            logger.error(f"Failed to generate verification badge: {e}")
            # Return default badge on error
            return {
                "verified": False,
                "issuer": "Maily Trust Authority",
                "timestamp": datetime.utcnow().isoformat(),
                "verification_url": f"https://verify.maily.example.com/{canvas_id}",
                "qr_code": None
            }
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash of content for verification"""
        return hashlib.sha256(content.encode()).hexdigest()
        
    # Circuit breaker implementation for blockchain operations
    def circuit_breaker(failure_threshold=3, reset_timeout=60):
        """
        Circuit breaker decorator for blockchain operations.
        
        Args:
            failure_threshold: Number of failures before opening the circuit
            reset_timeout: Seconds before attempting to reset circuit
            
        Returns:
            Decorated function
        """
        def decorator(func):
            # State tracking
            state = {
                "is_open": False,
                "failures": 0,
                "last_failure": None
            }
            
            async def wrapper(*args, **kwargs):
                now = datetime.utcnow()
                
                # Check if circuit is open
                if state["is_open"]:
                    # Check if reset timeout has elapsed
                    if state["last_failure"] and (now - state["last_failure"]).total_seconds() > reset_timeout:
                        # Allow a single request through to test if the service is back
                        logger.info("Circuit half-open, testing service availability")
                        state["is_open"] = False
                    else:
                        # Circuit is open and timeout hasn't elapsed
                        logger.warning(f"Circuit open, skipping blockchain operation: {func.__name__}")
                        return {"status": "skipped", "reason": "circuit_open"}
                
                try:
                    # Call the original function
                    result = await func(*args, **kwargs)
                    
                    # Reset failure count on success
                    state["failures"] = 0
                    return result
                except Exception as e:
                    # Increment failure count
                    state["failures"] += 1
                    state["last_failure"] = now
                    
                    # Check if threshold is reached
                    if state["failures"] >= failure_threshold:
                        logger.error(f"Circuit opened after {failure_threshold} failures in {func.__name__}")
                        state["is_open"] = True
                    
                    # Re-raise the exception
                    raise
            
            return wrapper
        return decorator
    
    @CircuitBreaker(failure_threshold=5, reset_timeout=300)
    async def verify_certificate_on_blockchain(self, certificate_id: str, content_hash: str) -> Dict[str, Any]:
        """
        Verify a certificate directly on the blockchain with circuit breaker protection
        
        Args:
            certificate_id: Certificate ID to verify
            content_hash: Content hash to verify
            
        Returns:
            Verification result
        """
        return await self.blockchain_service.verify_certificate(certificate_id, content_hash)
    
    async def batch_verify_certificates(self, certificates: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Verify multiple certificates in parallel batches
        
        Args:
            certificates: List of certificate data objects with 'id' and 'content_hash' fields
            
        Returns:
            Dictionary mapping certificate IDs to verification results
        """
        if not certificates:
            return {}
        
        # Create a verification function for a single certificate
        async def verify_single_certificate(cert_data):
            certificate_id = cert_data.get('id')
            content_hash = cert_data.get('content_hash')
            
            # Check cache first
            cache_key = f"verification:{certificate_id}:{content_hash}"
            if cache_key in self.verification_cache:
                cached_result, timestamp = self.verification_cache[cache_key]
                if (datetime.utcnow() - timestamp).total_seconds() < self.cache_expiration:
                    logger.info(f"Using cached verification for certificate {certificate_id}")
                    return certificate_id, cached_result
            
            try:
                # Try to verify on blockchain
                result = await self.verify_certificate_on_blockchain(certificate_id, content_hash)
                
                # Cache the result
                self.verification_cache[cache_key] = (result, datetime.utcnow())
                
                return certificate_id, result
            except Exception as e:
                logger.error(f"Failed to verify certificate {certificate_id}: {e}")
                return certificate_id, {"verified": False, "message": str(e)}
        
        # Process certificates in batches
        batch_size = 10
        concurrency_limit = 5
        results = {}
        
        # Create batches
        for i in range(0, len(certificates), batch_size):
            batch = certificates[i:i+batch_size]
            
            # Create tasks for each certificate in the batch
            tasks = [verify_single_certificate(cert) for cert in batch]
            
            # Process batch concurrently
            batch_semaphore = asyncio.Semaphore(concurrency_limit)
            
            async def process_with_semaphore(cert_task):
                async with batch_semaphore:
                    return await cert_task
            
            # Create tasks with semaphore
            batch_tasks = [process_with_semaphore(task) for task in tasks]
            
            # Execute batch and collect results
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch verification error: {result}")
                    continue
                    
                cert_id, verification_data = result
                results[cert_id] = verification_data
        
        return results
        
    async def verify_multiple_sources(self, canvas_id: str, content_hash: str) -> Dict[str, Any]:
        """
        Verify content using multiple verification sources in parallel
        
        Args:
            canvas_id: Canvas ID to verify
            content_hash: Content hash to verify
            
        Returns:
            Verification results from all sources
        """
        # Define verification functions for different sources
        verifications = [
            ("blockchain", self.blockchain_service.get_verification, {"content_hash": content_hash}),
            ("certificate", self.blockchain_service.verify_certificate, {"certificate_id": f"cert-{canvas_id}", "content_hash": content_hash}),
            ("redis", self._get_cached_verification, {"canvas_id": canvas_id, "content_hash": content_hash})
        ]
        
        # Execute verifications concurrently
        verification_results = await verify_concurrently(
            verification_funcs=verifications,
            timeout=5.0,
            min_success=1
        )
        
        # Combine and normalize results
        combined_result = {
            "verified": False,
            "sources": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Process results from each source
        for source, result in verification_results.items():
            source_result = {
                "verified": False,
                "duration_ms": result.duration_ms,
                "error": str(result.error) if result.error else None
            }
            
            if result.success:
                source_result["verified"] = True
                source_result["data"] = result.data
                combined_result["verified"] |= True  # Mark as verified if any source succeeded
                
            combined_result["sources"][source] = source_result
        
        return combined_result
    
    async def _get_cached_verification(self, canvas_id: str, content_hash: str) -> Dict[str, Any]:
        """Get cached verification data from Redis"""
        verification_key = f"canvas:{canvas_id}:verification:cache:{content_hash}"
        cached_data = await self.redis.get(verification_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        raise ValueError("No cached verification data found")
    
    async def _generate_verification_qr(self, canvas_id: str, content_hash: str) -> str:
        """Generate QR code for verification"""
        try:
            # Create verification URL
            verification_url = f"https://verify.maily.example.com/{canvas_id}?hash={content_hash}"
            
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

def get_trust_verification_service():
    """Get singleton instance of TrustVerificationService"""
    global _instance
    if _instance is None:
        _instance = TrustVerificationService()
    return _instance
