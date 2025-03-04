"""
Blockchain Service for Interactive Trust Verification

This service provides blockchain-based verification for email content using the Polygon blockchain.
It implements circuit breaker patterns, memory caching, and resilience mechanisms for production reliability.
"""

import json
import logging
import hashlib
import base64
import time
import asyncio
import functools
from typing import Dict, Any, List, Optional, Tuple, Callable, MutableMapping
from datetime import datetime, timedelta
from pydantic import BaseModel
from functools import wraps, lru_cache
from collections import OrderedDict, defaultdict
from eth_account.messages import encode_defunct

# Try importing Web3 for real blockchain implementation
try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

from ..utils.encryption import encrypt_data, decrypt_data
from ..cache.redis_client import get_redis_client
from ..utils.resilience import circuit_breaker, retry_with_backoff
from ..config.settings import settings

logger = logging.getLogger("api.services.blockchain")

# Mock blockchain transaction data for simulation
# In a real implementation, this would use ethers.js or web3.py to interact with the blockchain
MOCK_TRANSACTIONS = {}
MOCK_BLOCKS = {}
MOCK_BLOCK_NUMBER = 12345678

class TimedCache:
    """
    Time-based cache implementation for blockchain data
    
    Provides an in-memory cache with expiring entries based on time.
    Thread-safe for concurrent access.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize a new timed cache
        
        Args:
            max_size: Maximum number of items to store in cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._expiry: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache if it exists and is not expired
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        async with self._lock:
            # Check if key exists and is not expired
            if key in self._cache:
                if key in self._expiry:
                    # Check if expired
                    if datetime.utcnow() > self._expiry[key]:
                        # Remove expired item
                        self._remove_item(key)
                        return None
                
                # Move to end to track LRU
                value = self._cache[key]
                self._cache.move_to_end(key)
                return value
                
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with expiration
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Time-to-live in seconds, or None to use default
        """
        ttl = ttl if ttl is not None else self.default_ttl
        
        async with self._lock:
            # Check if we need to evict for size
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Remove oldest item (first in OrderedDict)
                self._cache.popitem(last=False)
            
            # Set value
            self._cache[key] = value
            self._cache.move_to_end(key)
            
            # Set expiry time
            self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
    
    async def delete(self, key: str) -> None:
        """
        Delete a key from the cache
        
        Args:
            key: Cache key to delete
        """
        async with self._lock:
            self._remove_item(key)
    
    def _remove_item(self, key: str) -> None:
        """
        Remove an item from the cache (internal, no locking)
        
        Args:
            key: Cache key to remove
        """
        if key in self._cache:
            del self._cache[key]
        
        if key in self._expiry:
            del self._expiry[key]
    
    async def clear(self) -> None:
        """Clear all items from the cache"""
        async with self._lock:
            self._cache.clear()
            self._expiry.clear()
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired items from the cache
        
        Returns:
            Number of items removed
        """
        count = 0
        now = datetime.utcnow()
        
        async with self._lock:
            # Find expired keys
            expired_keys = [
                key for key, expiry in self._expiry.items() 
                if now > expiry
            ]
            
            # Remove expired items
            for key in expired_keys:
                self._remove_item(key)
                count += 1
                
        return count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            stats = {
                "size": len(self._cache),
                "max_size": self.max_size,
                "utilization": len(self._cache) / self.max_size if self.max_size > 0 else 0,
                "default_ttl": self.default_ttl
            }
        
        return stats


def async_lru_cache(maxsize: int = 128, ttl: int = 3600):
    """
    LRU cache decorator for async functions with TTL
    
    Args:
        maxsize: Maximum cache size
        ttl: Time-to-live in seconds
        
    Returns:
        Cached async function
    """
    cache = {}
    timestamps = {}
    make_key = lambda *args, **kwargs: hash(str(args) + str(sorted(kwargs.items())))
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = make_key(*args, **kwargs)
            
            # Check if result in cache and not expired
            now = time.time()
            if key in cache:
                last_update = timestamps[key]
                if now - last_update < ttl:
                    # Cache hit, return cached result
                    return cache[key]
            
            # Cache miss or expired, call function
            result = await func(*args, **kwargs)
            
            # Update cache
            cache[key] = result
            timestamps[key] = now
            
            # Enforce size limit
            if len(cache) > maxsize:
                # Find oldest entry
                oldest_key = min(timestamps.items(), key=lambda x: x[1])[0]
                # Remove it
                del cache[oldest_key]
                del timestamps[oldest_key]
            
            return result
        return wrapper
    return decorator

class BlockchainService:
    """Service for interacting with the Polygon blockchain"""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.contract_address = "0x1234567890123456789012345678901234567890"
        self.network = "polygon"
        self.gas_limit = 50000  # Maximum gas limit for transactions
        
        # Initialize cache system for blockchain data
        self.verification_cache = TimedCache(max_size=5000, default_ttl=3600)  # 1 hour TTL
        self.certificate_cache = TimedCache(max_size=1000, default_ttl=7200)   # 2 hour TTL
        self.transaction_cache = TimedCache(max_size=2000, default_ttl=86400)  # 24 hour TTL
        self.block_cache = TimedCache(max_size=500, default_ttl=604800)        # 1 week TTL
        
        # Start background task for cache maintenance
        self._schedule_cache_maintenance()
        
        logger.info("BlockchainService initialized with caching support")
    
    def _schedule_cache_maintenance(self):
        """Schedule periodic cache maintenance task"""
        async def maintenance_task():
            while True:
                try:
                    # Run cleanup every 15 minutes
                    await asyncio.sleep(900)
                    await self._cleanup_caches()
                except Exception as e:
                    logger.error(f"Error in cache maintenance task: {e}")
                    # Sleep a bit before trying again
                    await asyncio.sleep(60)
        
        # Run in background
        asyncio.create_task(maintenance_task())
    
    async def _cleanup_caches(self):
        """Clean up expired items from all caches"""
        verification_count = await self.verification_cache.cleanup_expired()
        certificate_count = await self.certificate_cache.cleanup_expired()
        transaction_count = await self.transaction_cache.cleanup_expired() 
        block_count = await self.block_cache.cleanup_expired()
        
        total_count = verification_count + certificate_count + transaction_count + block_count
        
        logger.info(f"Cache maintenance completed: {total_count} expired items removed")
        
        # Log cache stats
        v_stats = await self.verification_cache.get_stats()
        c_stats = await self.certificate_cache.get_stats()
        t_stats = await self.transaction_cache.get_stats()
        b_stats = await self.block_cache.get_stats()
        
        logger.debug(f"Cache stats: verification={v_stats['size']}/{v_stats['max_size']}, "
                     f"certificate={c_stats['size']}/{c_stats['max_size']}, "
                     f"transaction={t_stats['size']}/{t_stats['max_size']}, "
                     f"block={b_stats['size']}/{b_stats['max_size']}")
        
    @circuit_breaker(failure_threshold=5, reset_timeout=300)
    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=10)
    async def verify_content(
        self, 
        content_hash: str,
        metadata: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Verify content by storing its hash on the blockchain"""
        try:
            if not WEB3_AVAILABLE:
                raise ImportError("Web3 library is not available. Please install with: pip install web3")
            
            # Initialize Web3 connection
            w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
            
            # Apply middleware for Polygon (PoS chain)
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check if connected
            if not w3.is_connected():
                raise ConnectionError(f"Failed to connect to blockchain node at {settings.POLYGON_RPC_URL}")
            
            # Get account from private key
            account = w3.eth.account.from_key(settings.BLOCKCHAIN_PRIVATE_KEY)
            
            # Initialize the verification contract
            contract = w3.eth.contract(
                address=self.contract_address, 
                abi=settings.VERIFICATION_CONTRACT_ABI
            )
            
            # Prepare transaction parameters
            nonce = w3.eth.get_transaction_count(account.address)
            
            # Get gas price with 10% buffer
            gas_price = w3.eth.gas_price
            gas_price_with_buffer = int(gas_price * 1.1)
            
            # Prepare metadata for on-chain storage
            # For larger metadata, we'd use IPFS and only store the hash
            metadata_json = json.dumps(metadata)
            metadata_hash = hashlib.sha256(metadata_json.encode()).hexdigest()
            
            # Prepare transaction for content verification
            tx = contract.functions.verifyContent(
                content_hash,
                metadata_hash,
                str(user_id)
            ).build_transaction({
                'from': account.address,
                'gas': self.gas_limit,
                'gasPrice': gas_price_with_buffer,
                'nonce': nonce,
            })
            
            # Sign the transaction
            signed_tx = account.sign_transaction(tx)
            
            # Send the transaction
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status != 1:
                raise Exception(f"Transaction failed with status {receipt.status}")
            
            # Get block information
            block = w3.eth.get_block(receipt.blockNumber)
            
            # Construct transaction data for our records
            transaction_id = tx_hash.hex()
            block_number = receipt.blockNumber
            
            # Extract events from receipt (if any)
            events = []
            if hasattr(contract.events, 'ContentVerified'):
                try:
                    content_verified_events = contract.events.ContentVerified().process_receipt(receipt)
                    events.extend(content_verified_events)
                except Exception as e:
                    logger.warning(f"Error processing ContentVerified events: {e}")
            
            # Store in Redis for persistence and fast retrieval
            verification_key = f"blockchain:verification:{content_hash}"
            await self.redis.set(
                verification_key,
                json.dumps({
                    "content_hash": content_hash,
                    "transaction_id": transaction_id,
                    "block_number": block_number,
                    "timestamp": datetime.utcnow().isoformat(),
                    "network": self.network,
                    "contract_address": self.contract_address,
                    "metadata": metadata,
                    "events": [str(e) for e in events],
                }),
                expire=86400 * 365  # 1 year
            )
            
            # Return verification data
            return {
                "transaction_id": transaction_id,
                "block_number": block_number,
                "timestamp": datetime.fromtimestamp(block.timestamp).isoformat(),
                "network": self.network,
                "contract_address": self.contract_address,
                "status": "verified" if receipt.status == 1 else "failed",
            }
            
        except Exception as e:
            logger.error(f"Failed to verify content on blockchain: {e}")
            raise
    
    @async_lru_cache(maxsize=500, ttl=3600)
    async def get_verification(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get verification data for a content hash with caching"""
        try:
            # Check memory cache first
            cache_key = f"verification:{content_hash}"
            cached_data = await self.verification_cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for verification data: {content_hash}")
                return cached_data
            
            # Check Redis if not in memory cache
            verification_key = f"blockchain:verification:{content_hash}"
            verification_data = await self.redis.get(verification_key)
            
            if verification_data:
                parsed_data = json.loads(verification_data)
                
                # Store in memory cache for future requests
                await self.verification_cache.set(cache_key, parsed_data)
                
                return parsed_data
            
            logger.debug(f"Verification data not found for hash: {content_hash}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get verification data: {e}")
            return None
    
    @async_lru_cache(maxsize=500, ttl=86400)  # Cache for 24 hours
    @circuit_breaker(failure_threshold=5, reset_timeout=300)
    async def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction details with caching"""
        try:
            # Check memory cache first
            cache_key = f"transaction:{transaction_id}"
            cached_data = await self.transaction_cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for transaction: {transaction_id}")
                return cached_data
            
            # Initialize Web3 and query blockchain
            if not WEB3_AVAILABLE:
                raise ImportError("Web3 library is not available. Please install with: pip install web3")
            
            # Initialize Web3 connection
            w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
            
            # Apply middleware for Polygon (PoS chain)
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check if connected
            if not w3.is_connected():
                raise ConnectionError(f"Failed to connect to blockchain node at {settings.POLYGON_RPC_URL}")
            
            # Query transaction
            tx_hash = transaction_id
            if not tx_hash.startswith('0x'):
                tx_hash = f"0x{tx_hash}"
                
            # Get transaction
            transaction = w3.eth.get_transaction(tx_hash)
            
            if not transaction:
                logger.debug(f"Transaction not found on blockchain: {transaction_id}")
                return None
                
            # Get transaction receipt for additional data
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            
            # Format transaction data
            transaction_data = {
                "hash": transaction_id,
                "from": transaction['from'],
                "to": transaction['to'],
                "value": str(transaction['value']),
                "gasPrice": str(transaction['gasPrice']),
                "gas": str(transaction['gas']),
                "nonce": transaction['nonce'],
                "input": transaction['input'],
                "blockHash": transaction['blockHash'].hex(),
                "blockNumber": transaction['blockNumber'],
                "transactionIndex": transaction['transactionIndex'],
            }
            
            # Add receipt data if available
            if receipt:
                transaction_data.update({
                    "status": receipt['status'],
                    "gasUsed": str(receipt['gasUsed']),
                    "effectiveGasPrice": str(receipt.get('effectiveGasPrice', 0)),
                    "cumulativeGasUsed": str(receipt['cumulativeGasUsed']),
                    "logs": [log.hex() if isinstance(log, bytes) else str(log) for log in receipt.get('logs', [])],
                })
            
            # Get block for timestamp
            try:
                block = w3.eth.get_block(transaction['blockNumber'])
                transaction_data["timestamp"] = datetime.fromtimestamp(block['timestamp']).isoformat()
            except Exception as e:
                logger.warning(f"Could not get block timestamp for transaction {transaction_id}: {e}")
                transaction_data["timestamp"] = datetime.utcnow().isoformat()
            
            # Store in memory cache
            await self.transaction_cache.set(cache_key, transaction_data)
            
            # Return formatted transaction data
            return transaction_data
            
        except Exception as e:
            logger.error(f"Failed to get transaction {transaction_id}: {e}")
            return None
    
    @async_lru_cache(maxsize=200, ttl=604800)  # Cache for 1 week
    @circuit_breaker(failure_threshold=5, reset_timeout=300)
    async def get_block(self, block_number: int) -> Optional[Dict[str, Any]]:
        """Get block details with caching"""
        try:
            # Check memory cache first
            cache_key = f"block:{block_number}"
            cached_data = await self.block_cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for block: {block_number}")
                return cached_data
            
            # Initialize Web3 and query blockchain
            if not WEB3_AVAILABLE:
                raise ImportError("Web3 library is not available. Please install with: pip install web3")
            
            # Initialize Web3 connection
            w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
            
            # Apply middleware for Polygon (PoS chain)
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check if connected
            if not w3.is_connected():
                raise ConnectionError(f"Failed to connect to blockchain node at {settings.POLYGON_RPC_URL}")
            
            # Get block
            block = w3.eth.get_block(block_number, full_transactions=False)
            
            if not block:
                logger.debug(f"Block not found: {block_number}")
                return None
            
            # Format block data
            block_data = {
                "number": block['number'],
                "hash": block['hash'].hex(),
                "parentHash": block['parentHash'].hex(),
                "nonce": block['nonce'].hex() if hasattr(block['nonce'], 'hex') else str(block['nonce']),
                "sha3Uncles": block['sha3Uncles'].hex(),
                "logsBloom": block['logsBloom'].hex(),
                "transactionsRoot": block['transactionsRoot'].hex(),
                "stateRoot": block['stateRoot'].hex(),
                "receiptsRoot": block['receiptsRoot'].hex(),
                "miner": block['miner'],
                "difficulty": str(block['difficulty']),
                "totalDifficulty": str(block['totalDifficulty']),
                "extraData": block['extraData'].hex(),
                "size": block['size'],
                "gasLimit": block['gasLimit'],
                "gasUsed": block['gasUsed'],
                "timestamp": datetime.fromtimestamp(block['timestamp']).isoformat(),
                "transactions": [tx.hex() if isinstance(tx, bytes) else tx for tx in block['transactions']],
                "uncles": [uncle.hex() if isinstance(uncle, bytes) else uncle for uncle in block['uncles']],
            }
            
            # Store in memory cache (blocks are immutable, so longer TTL)
            await self.block_cache.set(cache_key, block_data, ttl=604800)  # 1 week
            
            # Return formatted block data
            return block_data
            
        except Exception as e:
            logger.error(f"Failed to get block {block_number}: {e}")
            return None
    
    @circuit_breaker(failure_threshold=5, reset_timeout=300)
    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=10)
    async def create_token(
        self, 
        recipient: str,
        metadata: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Create a token for a recipient using the certificate contract"""
        try:
            if not WEB3_AVAILABLE:
                raise ImportError("Web3 library is not available. Please install with: pip install web3")
            
            # Initialize Web3 connection
            w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
            
            # Apply middleware for Polygon (PoS chain)
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check if connected
            if not w3.is_connected():
                raise ConnectionError(f"Failed to connect to blockchain node at {settings.POLYGON_RPC_URL}")
            
            # Get account from private key
            account = w3.eth.account.from_key(settings.BLOCKCHAIN_PRIVATE_KEY)
            
            # Initialize the certificate contract
            contract = w3.eth.contract(
                address=settings.CERTIFICATE_CONTRACT_ADDRESS, 
                abi=settings.CERTIFICATE_CONTRACT_ABI
            )
            
            # Prepare metadata for storage
            # For larger metadata, store as JSON in a content-addressable system (IPFS/Arweave)
            # and only store the content hash on-chain
            metadata_str = json.dumps(metadata)
            metadata_hash = f"hash:{hashlib.sha256(metadata_str.encode()).hexdigest()}"
            
            # Store the full metadata in our own storage
            metadata_key = f"blockchain:metadata:{metadata_hash}"
            await self.redis.set(
                metadata_key,
                metadata_str,
                expire=86400 * 365 * 5  # 5 years
            )
            
            # Current time for issuance
            now = int(time.time())
            
            # Expiry time (1 year by default)
            expiry = now + 31536000  # 1 year in seconds
            
            # Generate a signature for the certificate
            # In real implementation, this would use the account's private key to sign
            signature = w3.eth.account.sign_message(
                encode_defunct(text=f"{recipient}:{metadata_hash}:{now}:{expiry}"),
                private_key=settings.BLOCKCHAIN_PRIVATE_KEY
            ).signature.hex()
            
            # Prepare transaction parameters
            nonce = w3.eth.get_transaction_count(account.address)
            
            # Get gas price with 10% buffer
            gas_price = w3.eth.gas_price
            gas_price_with_buffer = int(gas_price * 1.1)
            
            # Determine certificate type from metadata
            certificate_type = metadata.get('certificate_type', 0)  # Default to type 0
            
            # Prepare transaction for certificate issuance
            tx = contract.functions.issueCertificate(
                certificate_type,
                account.address,  # Issuer is our service account
                recipient,
                now,  # Issuance timestamp
                expiry,  # Expiry timestamp
                metadata_hash,  # Metadata URI/hash
                signature  # Cryptographic signature
            ).build_transaction({
                'from': account.address,
                'gas': 300000,  # Gas limit
                'gasPrice': gas_price_with_buffer,
                'nonce': nonce,
            })
            
            # Sign the transaction
            signed_tx = account.sign_transaction(tx)
            
            # Send the transaction
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status != 1:
                raise Exception(f"Transaction failed with status {receipt.status}")
            
            # Get certificate ID from event logs
            certificate_id = None
            if receipt.logs:
                # Parse logs for CertificateIssued event
                try:
                    certificate_events = contract.events.CertificateIssued().process_receipt(receipt)
                    if certificate_events:
                        certificate_id = certificate_events[0]['args']['certificateId']
                except Exception as e:
                    logger.warning(f"Error extracting certificate ID from events: {e}")
            
            # If we couldn't get certificate ID from events, generate a deterministic one
            if not certificate_id:
                certificate_id = f"cert-{hashlib.sha256(f'{recipient}:{now}:{tx_hash.hex()}'.encode()).hexdigest()[:16]}"
                logger.warning(f"Could not extract certificate ID from events, using deterministic ID: {certificate_id}")
            
            # Format token data
            token_data = {
                "id": certificate_id,
                "recipient": recipient,
                "creator": user_id,
                "issuer": account.address,
                "metadata": metadata,
                "metadataHash": metadata_hash,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": datetime.fromtimestamp(expiry).isoformat(),
                "transaction_id": tx_hash.hex(),
                "network": self.network,
                "contract_address": settings.CERTIFICATE_CONTRACT_ADDRESS,
                "block_number": receipt.blockNumber,
                "status": "active",
                "signature": signature,
            }
            
            # Store token data in Redis for quick lookups
            token_key = f"blockchain:token:{certificate_id}"
            await self.redis.set(
                token_key,
                json.dumps(token_data),
                expire=86400 * 365 * 2  # 2 years
            )
            
            # Index by recipient for quick lookups
            recipient_key = f"blockchain:recipient:{recipient}"
            existing_tokens = await self.redis.get(recipient_key)
            if existing_tokens:
                token_ids = json.loads(existing_tokens)
                if certificate_id not in token_ids:
                    token_ids.append(certificate_id)
            else:
                token_ids = [certificate_id]
                
            await self.redis.set(
                recipient_key,
                json.dumps(token_ids),
                expire=86400 * 365 * 2  # 2 years
            )
            
            # Return token data
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to create token: {e}")
            raise
    
    @circuit_breaker(failure_threshold=5, reset_timeout=300)
    async def get_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get token details with blockchain fallback"""
        try:
            # Try to get from Redis cache first
            token_key = f"blockchain:token:{token_id}"
            token_data = await self.redis.get(token_key)
            
            if token_data:
                return json.loads(token_data)
            
            # If not in cache, try to retrieve from the blockchain
            if WEB3_AVAILABLE and settings.BLOCKCHAIN_ENABLED:
                # Initialize Web3 connection
                w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
                
                # Apply middleware for Polygon (PoS chain)
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                
                # Check if connected
                if not w3.is_connected():
                    logger.error(f"Failed to connect to blockchain node at {settings.POLYGON_RPC_URL}")
                    return None
                
                # Initialize the certificate contract
                contract = w3.eth.contract(
                    address=settings.CERTIFICATE_CONTRACT_ADDRESS, 
                    abi=settings.CERTIFICATE_CONTRACT_ABI
                )
                
                try:
                    # Get certificate from blockchain
                    cert_data = contract.functions.getCertificate(token_id).call()
                    
                    # Extract the recipient from the certificate
                    recipient = cert_data[2]  # subject field
                    
                    # Format the certificate data
                    token = {
                        "id": token_id,
                        "recipient": recipient,
                        "issuer": cert_data[1],  # issuer address
                        "metadata": {"certificate_type": cert_data[0]},  # certificateType
                        "created_at": datetime.fromtimestamp(cert_data[3]).isoformat(),  # issuedAt
                        "expires_at": datetime.fromtimestamp(cert_data[4]).isoformat(),  # expiresAt
                        "status": self._get_status_string(cert_data[5]),  # status
                        "metadataHash": cert_data[6],  # metadataURI
                        "signature": cert_data[7],  # signature
                        "network": self.network,
                        "contract_address": settings.CERTIFICATE_CONTRACT_ADDRESS,
                    }
                    
                    # Try to get full metadata from our storage
                    try:
                        metadata_key = f"blockchain:metadata:{cert_data[6]}"
                        metadata_str = await self.redis.get(metadata_key)
                        if metadata_str:
                            token["metadata"] = json.loads(metadata_str)
                    except Exception as e:
                        logger.warning(f"Failed to get metadata for certificate {token_id}: {e}")
                    
                    # Cache the token data for future requests
                    await self.redis.set(
                        token_key,
                        json.dumps(token),
                        expire=86400 * 7  # 1 week
                    )
                    
                    # Update recipient index
                    recipient_key = f"blockchain:recipient:{recipient}"
                    existing_tokens = await self.redis.get(recipient_key)
                    if existing_tokens:
                        token_ids = json.loads(existing_tokens)
                        if token_id not in token_ids:
                            token_ids.append(token_id)
                            await self.redis.set(
                                recipient_key,
                                json.dumps(token_ids),
                                expire=86400 * 7  # 1 week
                            )
                    else:
                        await self.redis.set(
                            recipient_key,
                            json.dumps([token_id]),
                            expire=86400 * 7  # 1 week
                        )
                    
                    return token
                except Exception as e:
                    logger.error(f"Error getting certificate {token_id} from blockchain: {e}")
            
            logger.debug(f"Token not found: {token_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get token: {e}")
            return None
    
    @circuit_breaker(failure_threshold=5, reset_timeout=300)
    async def get_tokens_for_recipient(self, recipient: str) -> List[Dict[str, Any]]:
        """Get all tokens for a recipient"""
        try:
            # Check the recipient index first (much more efficient than scanning all tokens)
            recipient_key = f"blockchain:recipient:{recipient}"
            cached_token_ids = await self.redis.get(recipient_key)
            
            if cached_token_ids:
                # We have a cached list of token IDs for this recipient
                token_ids = json.loads(cached_token_ids)
                tokens = []
                
                # Get each token by ID
                for token_id in token_ids:
                    token_key = f"blockchain:token:{token_id}"
                    token_data = await self.redis.get(token_key)
                    if token_data:
                        tokens.append(json.loads(token_data))
                
                return tokens
            
            # If we don't have a cached list, query the blockchain directly
            if WEB3_AVAILABLE and settings.BLOCKCHAIN_ENABLED:
                # Initialize Web3 connection
                w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
                
                # Apply middleware for Polygon (PoS chain)
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                
                # Check if connected
                if not w3.is_connected():
                    logger.error(f"Failed to connect to blockchain node at {settings.POLYGON_RPC_URL}")
                    return []
                
                # Initialize the certificate contract
                contract = w3.eth.contract(
                    address=settings.CERTIFICATE_CONTRACT_ADDRESS, 
                    abi=settings.CERTIFICATE_CONTRACT_ABI
                )
                
                try:
                    # Get certificates by subject (recipient) from the contract
                    certificate_ids = contract.functions.getCertificatesBySubject(recipient).call()
                    
                    if not certificate_ids:
                        return []
                    
                    # Store the certificate IDs in Redis for future lookups
                    await self.redis.set(
                        recipient_key,
                        json.dumps(certificate_ids),
                        expire=86400 * 7  # 1 week
                    )
                    
                    # Get each certificate's details
                    tokens = []
                    for cert_id in certificate_ids:
                        try:
                            # Try to get from cache first
                            token_key = f"blockchain:token:{cert_id}"
                            cached_token = await self.redis.get(token_key)
                            
                            if cached_token:
                                tokens.append(json.loads(cached_token))
                                continue
                            
                            # Get from blockchain if not cached
                            cert_data = contract.functions.getCertificate(cert_id).call()
                            
                            # Format certificate data
                            token = {
                                "id": cert_id,
                                "recipient": recipient,
                                "issuer": cert_data[1],  # issuer address
                                "metadata": {"certificate_type": cert_data[0]},  # certificateType
                                "created_at": datetime.fromtimestamp(cert_data[3]).isoformat(),  # issuedAt
                                "expires_at": datetime.fromtimestamp(cert_data[4]).isoformat(),  # expiresAt
                                "status": self._get_status_string(cert_data[5]),  # status
                                "metadataHash": cert_data[6],  # metadataURI
                                "signature": cert_data[7],  # signature
                                "network": self.network,
                                "contract_address": settings.CERTIFICATE_CONTRACT_ADDRESS,
                            }
                            
                            # Try to get the full metadata from our storage
                            try:
                                metadata_key = f"blockchain:metadata:{cert_data[6]}"
                                metadata_str = await self.redis.get(metadata_key)
                                if metadata_str:
                                    token["metadata"] = json.loads(metadata_str)
                            except Exception as e:
                                logger.warning(f"Failed to get metadata for certificate {cert_id}: {e}")
                            
                            tokens.append(token)
                            
                            # Cache the token data
                            await self.redis.set(
                                token_key,
                                json.dumps(token),
                                expire=86400 * 7  # 1 week
                            )
                        except Exception as e:
                            logger.error(f"Error getting certificate {cert_id}: {e}")
                    
                    return tokens
                    
                except Exception as e:
                    logger.error(f"Error querying certificates for recipient {recipient}: {e}")
            
            # Fallback to scanning Redis (less efficient, but works as backup)
            logger.warning(f"Falling back to Redis scan for recipient {recipient}")
            token_keys = await self.redis.keys("blockchain:token:*")
            tokens = []
            
            for key in token_keys:
                token_data = await self.redis.get(key)
                if token_data:
                    token = json.loads(token_data)
                    if token.get("recipient") == recipient:
                        tokens.append(token)
            
            # If we found tokens this way, cache the IDs for future lookups
            if tokens:
                token_ids = [token["id"] for token in tokens]
                await self.redis.set(
                    recipient_key,
                    json.dumps(token_ids),
                    expire=86400 * 7  # 1 week
                )
            
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to get tokens for recipient: {e}")
            return []
    
    def _get_status_string(self, status_code: int) -> str:
        """Convert status code to string"""
        status_map = {
            0: "pending",
            1: "active",
            2: "revoked",
            3: "expired"
        }
        return status_map.get(status_code, "unknown")
    
    def generate_content_hash(self, content: str) -> str:
        """Generate hash of content for verification"""
        return hashlib.sha256(content.encode()).hexdigest()
        
    def get_verification_url(self, certificate_id: str) -> str:
        """Get public verification URL for a certificate"""
        # Use the correct production URL based on environment
        base_url = getattr(settings, 'VERIFICATION_BASE_URL', 'https://verify.maily.ai')
        return f"{base_url}/certificate/{certificate_id}"
        
    def get_token_reward_url(self, token_id: str) -> str:
        """Get token reward URL"""
        # Use the correct production URL based on environment
        base_url = getattr(settings, 'TOKEN_REWARD_URL', 'https://rewards.maily.ai')
        return f"{base_url}/token/{token_id}"
    
    @circuit_breaker(failure_threshold=5, reset_timeout=300)
    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=10)
    async def verify_certificate(
        self, 
        certificate_id: str,
        content_hash: str
    ) -> Dict[str, Any]:
        """Verify a certificate against the blockchain with circuit breaker and caching"""
        try:
            # Check memory cache first
            cache_key = f"certificate_verification:{certificate_id}:{content_hash}"
            cached_result = await self.certificate_cache.get(cache_key)
            
            if cached_result:
                logger.debug(f"Cache hit for certificate verification: {certificate_id}")
                return cached_result
            
            # First, get both the certificate and verification data
            certificate_data = await self.get_token(certificate_id)
            verification_data = await self.get_verification(content_hash)
            
            # If no certificate data, return error
            if not certificate_data:
                result = {
                    "verified": False,
                    "message": f"Certificate with ID {certificate_id} not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Cache negative results for a shorter period
                await self.certificate_cache.set(cache_key, result, ttl=1800)  # 30 minutes
                return result
            
            # If no verification data, try to verify directly on blockchain
            if not verification_data and WEB3_AVAILABLE and settings.BLOCKCHAIN_ENABLED:
                # Initialize Web3 connection
                w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
                
                # Apply middleware for Polygon (PoS chain)
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                
                # Check if connected
                if not w3.is_connected():
                    logger.error(f"Failed to connect to blockchain node at {settings.POLYGON_RPC_URL}")
                    return {
                        "verified": False,
                        "message": "Failed to connect to blockchain node",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                # Initialize the certificate contract
                contract = w3.eth.contract(
                    address=settings.CERTIFICATE_CONTRACT_ADDRESS, 
                    abi=settings.CERTIFICATE_CONTRACT_ABI
                )
                
                try:
                    # Verify certificate on blockchain
                    is_valid = contract.functions.verifyCertificate(certificate_id).call()
                    
                    # Get metadata to check content hash
                    # Check if the content hash matches the one in the metadata (if available)
                    metadata = certificate_data.get("metadata", {})
                    metadata_content_hash = metadata.get("content_hash")
                    
                    content_hash_matches = metadata_content_hash == content_hash
                    
                    if is_valid and content_hash_matches:
                        result = {
                            "verified": True,
                            "message": "Certificate verified successfully on blockchain",
                            "certificate": certificate_data,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        # Cache positive results for longer
                        await self.certificate_cache.set(cache_key, result, ttl=7200)  # 2 hours
                        return result
                    elif is_valid and not content_hash_matches:
                        result = {
                            "verified": False,
                            "message": "Certificate is valid but content hash doesn't match",
                            "certificate": certificate_data,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        # Cache negative results for a shorter period
                        await self.certificate_cache.set(cache_key, result, ttl=1800)  # 30 minutes
                        return result
                    else:
                        result = {
                            "verified": False,
                            "message": "Certificate verification failed on blockchain",
                            "certificate": certificate_data,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        # Cache negative results for a shorter period
                        await self.certificate_cache.set(cache_key, result, ttl=1800)  # 30 minutes
                        return result
                except Exception as e:
                    logger.error(f"Error verifying certificate on blockchain: {e}")
            
            # If we have verification data, check if certificate ID matches
            if verification_data and verification_data.get("metadata", {}).get("certificate_id") == certificate_id:
                result = {
                    "verified": True,
                    "message": "Certificate verified successfully",
                    "certificate": certificate_data,
                    "verification_data": verification_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Cache positive results for longer
                await self.certificate_cache.set(cache_key, result, ttl=7200)  # 2 hours
                return result
            
            # If nothing matches, return failure
            result = {
                "verified": False,
                "message": "Certificate could not be verified for this content",
                "certificate": certificate_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache negative results for a shorter period
            await self.certificate_cache.set(cache_key, result, ttl=1800)  # 30 minutes
            return result
            
        except Exception as e:
            logger.error(f"Failed to verify certificate: {e}")
            
            # Create error result
            error_result = {
                "verified": False,
                "message": f"Error verifying certificate: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            
            # Still cache error results, but for a shorter time
            await self.certificate_cache.set(cache_key, error_result, ttl=300)  # 5 minutes
            
            return error_result

# Singleton instance
_instance = None

def get_blockchain_service():
    """Get singleton instance of BlockchainService"""
    global _instance
    if _instance is None:
        _instance = BlockchainService()
    return _instance
