#!/usr/bin/env python3
"""
Enhance Blockchain Security Script

This script implements security enhancements for the blockchain integration in the Maily platform.
It focuses on improving private key management by integrating with HashiCorp Vault,
implementing transaction validation, and adding monitoring for blockchain operations.

Usage:
    python enhance_blockchain_security.py [--dry-run] [--verbose]

Options:
    --dry-run   Show changes without applying them
    --verbose   Show detailed information during execution
"""

import os
import re
import sys
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("blockchain-security")

# Paths to blockchain-related files
BLOCKCHAIN_FILES = {
    "service": "apps/api/services/blockchain.py",
    "web_service": "apps/web/services/BlockchainService.ts",
    "config": "apps/api/config/blockchain.py",
    "monitoring": "infrastructure/prometheus/blockchain-alerts.yml",
}

# Vault integration code template
VAULT_INTEGRATION_CODE = """
from apps.api.services.vault_service import VaultService
from packages.error_handling.python.error import BlockchainError as SecurityError
from web3 import Web3
from web3.middleware import geth_poa_middleware
import logging

logger = logging.getLogger(__name__)

class SecureBlockchainService:
    """Enhanced blockchain service with improved security."""

    def __init__(self, vault_service=None):
        """Initialize blockchain service with Vault integration."""
        self.vault_service = vault_service or VaultService()
        self.provider_url = settings.BLOCKCHAIN_PROVIDER_URL
        self.contract_address = settings.BLOCKCHAIN_CONTRACT_ADDRESS
        self.network = settings.BLOCKCHAIN_NETWORK
        self.enabled = settings.BLOCKCHAIN_ENABLED
        self.w3 = None
        self.contract = None
        self.last_gas_price = None
        self.gas_price_update_time = 0

        if self.enabled:
            try:
                # Setup Web3 connection
                self.w3 = Web3(Web3.HTTPProvider(self.provider_url))

                # Add middleware for PoA chains like Polygon
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

                # Setup contract
                self.contract = self.w3.eth.contract(
                    address=Web3.toChecksumAddress(self.contract_address),
                    abi=TRUST_CERTIFICATE_ABI
                )

                logger.info(f"Blockchain service initialized for network {self.network}")
            except Exception as e:
                logger.error(f"Failed to initialize blockchain service: {e}")
                self.enabled = False

    async def get_private_key(self, key_name="main"):
        """Securely retrieve private key from Vault."""
        try:
            secret = await self.vault_service.get_secret(f"blockchain/private-keys/{key_name}")
            return secret["private_key"]
        except Exception as e:
            logger.error(f"Failed to retrieve private key from Vault: {e}")
            raise SecurityError("Failed to access blockchain credentials")

    async def register_document(self, document_hash, metadata):
        """Register a document on the blockchain with enhanced security."""
        if not self.enabled:
            logger.warning("Blockchain service is disabled, skipping document registration")
            return None

        try:
            # Get private key securely from Vault
            private_key = await self.get_private_key()

            # Create transaction with optimal gas price
            gas_price = await self.get_optimal_gas_price()

            # Prepare transaction
            tx = self.contract.functions.registerDocument(
                document_hash,
                json.dumps(metadata)
            ).buildTransaction({
                'from': self.w3.eth.account.from_key(private_key).address,
                'nonce': self.w3.eth.getTransactionCount(
                    self.w3.eth.account.from_key(private_key).address
                ),
                'gasPrice': gas_price,
            })

            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)

            # Send transaction
            tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)

            # Wait for transaction receipt
            receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)

            # Validate transaction success
            if receipt.status != 1:
                raise Exception(f"Transaction failed with status {receipt.status}")

            # Log successful transaction
            logger.info(
                f"Document registered on blockchain",
                extra={
                    "document_hash": document_hash,
                    "tx_hash": tx_hash.hex(),
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "network": self.network,
                }
            )

            return {
                "tx_hash": tx_hash.hex(),
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
            }
        except Exception as e:
            logger.error(
                f"Failed to register document on blockchain: {e}",
                extra={
                    "document_hash": document_hash,
                    "network": self.network,
                    "error": str(e),
                }
            )
            raise

    async def verify_document(self, document_hash):
        """Verify a document on the blockchain with enhanced security."""
        if not self.enabled:
            logger.warning("Blockchain service is disabled, skipping document verification")
            return False

        try:
            # Call the contract to verify the document
            result = self.contract.functions.verifyDocument(document_hash).call()

            # Log verification attempt
            logger.info(
                f"Document verification attempt",
                extra={
                    "document_hash": document_hash,
                    "verified": result,
                    "network": self.network,
                }
            )

            return result
        except Exception as e:
            logger.error(
                f"Failed to verify document on blockchain: {e}",
                extra={
                    "document_hash": document_hash,
                    "network": self.network,
                    "error": str(e),
                }
            )
            return False

    async def revoke_certificate(self, certificate_id):
        """Revoke a certificate on the blockchain with enhanced security."""
        if not self.enabled:
            logger.warning("Blockchain service is disabled, skipping certificate revocation")
            return None

        try:
            # Get private key securely from Vault
            private_key = await self.get_private_key()

            # Create transaction with optimal gas price
            gas_price = await self.get_optimal_gas_price()

            # Prepare transaction
            tx = self.contract.functions.revokeCertificate(
                certificate_id
            ).buildTransaction({
                'from': self.w3.eth.account.from_key(private_key).address,
                'nonce': self.w3.eth.getTransactionCount(
                    self.w3.eth.account.from_key(private_key).address
                ),
                'gasPrice': gas_price,
            })

            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)

            # Send transaction
            tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)

            # Wait for transaction receipt
            receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)

            # Validate transaction success
            if receipt.status != 1:
                raise Exception(f"Transaction failed with status {receipt.status}")

            # Log successful transaction
            logger.info(
                f"Certificate revoked on blockchain",
                extra={
                    "certificate_id": certificate_id,
                    "tx_hash": tx_hash.hex(),
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "network": self.network,
                }
            )

            return {
                "tx_hash": tx_hash.hex(),
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
            }
        except Exception as e:
            logger.error(
                f"Failed to revoke certificate on blockchain: {e}",
                extra={
                    "certificate_id": certificate_id,
                    "network": self.network,
                    "error": str(e),
                }
            )
            raise

    async def get_optimal_gas_price(self):
        """Get optimal gas price with caching to prevent excessive API calls."""
        import time

        # Cache gas price for 2 minutes to prevent excessive API calls
        current_time = time.time()
        if self.last_gas_price and (current_time - self.gas_price_update_time) < 120:
            return self.last_gas_price

        try:
            # Get current gas price from the network
            gas_price = self.w3.eth.gasPrice

            # Add 10% to ensure transaction goes through
            gas_price = int(gas_price * 1.1)

            # Update cache
            self.last_gas_price = gas_price
            self.gas_price_update_time = current_time

            return gas_price
        except Exception as e:
            logger.error(f"Failed to get gas price: {e}")

            # If we have a cached price, use it as fallback
            if self.last_gas_price:
                return self.last_gas_price

            # Otherwise use a reasonable default
            return self.w3.toWei(50, 'gwei')
"""

# Vault service implementation template
VAULT_SERVICE_CODE = """
import os
import hvac
import logging
from typing import Dict, Any, Optional
from fastapi import Depends
from functools import lru_cache

logger = logging.getLogger(__name__)

class VaultService:
    """Service for interacting with HashiCorp Vault."""

    def __init__(self):
        """Initialize Vault client."""
        self.enabled = os.getenv("VAULT_ENABLED", "false").lower() == "true"
        self.vault_url = os.getenv("VAULT_URL", "http://vault:8200")
        self.token = os.getenv("VAULT_TOKEN")
        self.client = None

        if self.enabled:
            try:
                self.client = hvac.Client(url=self.vault_url, token=self.token)
                if not self.client.is_authenticated():
                    logger.error("Failed to authenticate with Vault")
                    self.enabled = False
                else:
                    logger.info("Successfully connected to Vault")
            except Exception as e:
                logger.error(f"Failed to connect to Vault: {e}")
                self.enabled = False

    async def get_secret(self, path: str) -> Dict[str, Any]:
        """Get a secret from Vault.

        Args:
            path: Path to the secret in Vault

        Returns:
            Dictionary containing the secret data

        Raises:
            Exception: If the secret cannot be retrieved
        """
        if not self.enabled:
            logger.warning(f"Vault is disabled, using fallback for {path}")
            return self._get_fallback_secret(path)

        try:
            # Get secret from Vault
            secret = self.client.secrets.kv.v2.read_secret_version(path=path)
            return secret["data"]["data"]
        except Exception as e:
            logger.error(f"Failed to get secret from Vault: {e}")
            return self._get_fallback_secret(path)

    async def set_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """Set a secret in Vault.

        Args:
            path: Path to the secret in Vault
            data: Data to store

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning(f"Vault is disabled, cannot set secret at {path}")
            return False

        try:
            # Set secret in Vault
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
            )
            logger.info(f"Secret set at {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret in Vault: {e}")
            return False

    async def rotate_key(self, path: str) -> Optional[Dict[str, Any]]:
        """Rotate a key in Vault.

        Args:
            path: Path to the key in Vault

        Returns:
            New key data if successful, None otherwise
        """
        if not self.enabled:
            logger.warning(f"Vault is disabled, cannot rotate key at {path}")
            return None

        try:
            # Get current key
            current_key = await self.get_secret(path)

            # Generate new key
            import secrets
            new_key = {
                "private_key": "0x" + secrets.token_hex(32),
                "created_at": datetime.datetime.utcnow().isoformat(),
                "previous_key": current_key.get("private_key"),
            }

            # Store new key
            success = await self.set_secret(path, new_key)
            if success:
                logger.info(f"Key rotated at {path}")
                return new_key
            else:
                logger.error(f"Failed to rotate key at {path}")
                return None
        except Exception as e:
            logger.error(f"Failed to rotate key: {e}")
            return None

    def _get_fallback_secret(self, path: str) -> Dict[str, Any]:
        """Get a fallback secret when Vault is disabled or unavailable.

        This is only for development and testing. In production, Vault should
        always be enabled and available.

        Args:
            path: Path to the secret in Vault

        Returns:
            Dictionary containing fallback secret data
        """
        # In production, this should raise an exception
        if os.getenv("ENVIRONMENT", "development") == "production":
            raise Exception(f"Vault is required in production")

        # For development, use fallback secrets
        if path == "blockchain/private-keys/main":
            return {
                "private_key": os.getenv("BLOCKCHAIN_PRIVATE_KEY", "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
                "created_at": "2023-01-01T00:00:00Z",
            }

        # Default fallback
        return {
            "data": f"Fallback secret for {path}",
            "created_at": "2023-01-01T00:00:00Z",
        }

@lru_cache()
def get_vault_service() -> VaultService:
    """Get a singleton instance of VaultService."""
    return VaultService()
"""

# Prometheus alerts for blockchain monitoring
PROMETHEUS_ALERTS = """
groups:
- name: blockchain-alerts
  rules:
  - alert: BlockchainTransactionFailed
    expr: rate(blockchain_transaction_failed_total[5m]) > 0
    for: 1m
    labels:
      severity: critical
      service: blockchain
    annotations:
      summary: "Blockchain transaction failed"
      description: "{{ $value }} blockchain transactions failed in the last 5 minutes"

  - alert: BlockchainServiceUnavailable
    expr: blockchain_service_available == 0
    for: 5m
    labels:
      severity: critical
      service: blockchain
    annotations:
      summary: "Blockchain service unavailable"
      description: "Blockchain service has been unavailable for 5 minutes"

  - alert: BlockchainHighGasPrice
    expr: blockchain_gas_price > 100000000000
    for: 15m
    labels:
      severity: warning
      service: blockchain
    annotations:
      summary: "High gas price detected"
      description: "Gas price has been above 100 Gwei for 15 minutes"

  - alert: BlockchainTransactionDelayed
    expr: blockchain_transaction_pending_seconds > 300
    for: 5m
    labels:
      severity: warning
      service: blockchain
    annotations:
      summary: "Blockchain transaction delayed"
      description: "Blockchain transactions have been pending for more than 5 minutes"

  - alert: BlockchainKeyRotationOverdue
    expr: time() - blockchain_key_last_rotated_timestamp > 2592000
    for: 1h
    labels:
      severity: warning
      service: blockchain
    annotations:
      summary: "Blockchain key rotation overdue"
      description: "Blockchain keys have not been rotated in over 30 days"
"""

class BlockchainSecurityEnhancer:
    """Class to enhance blockchain security in the codebase."""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        """Initialize the enhancer.

        Args:
            dry_run: If True, show changes without applying them
            verbose: If True, show detailed information during execution
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.root_dir = self._find_root_dir()
        self.files_updated = 0

    def _find_root_dir(self) -> Path:
        """Find the root directory of the project."""
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            if (current_dir / "README.md").exists() and (current_dir / "apps").exists():
                return current_dir
            current_dir = current_dir.parent

        # If we can't find the root directory, use the current directory
        return Path.cwd()

    def _log(self, message: str):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            logger.info(message)

    def enhance_blockchain_security(self):
        """Enhance blockchain security across the codebase."""
        logger.info("Enhancing blockchain security...")

        # Create Vault service
        self._create_vault_service()

        # Update blockchain service
        self._update_blockchain_service()

        # Add monitoring
        self._add_blockchain_monitoring()

        logger.info(f"Blockchain security enhancement complete. {self.files_updated} files updated.")

    def _create_vault_service(self):
        """Create or update the Vault service."""
        vault_service_path = self.root_dir / "apps/api/services/vault_service.py"

        # Create directory if it doesn't exist
        vault_service_path.parent.mkdir(parents=True, exist_ok=True)

        if vault_service_path.exists():
            logger.info(f"Vault service already exists at {vault_service_path}")
            # Update existing vault service
            existing_code = vault_service_path.read_text()
            if "rotate_key" not in existing_code:
                logger.info("Updating existing Vault service with key rotation functionality")
                if not self.dry_run:
                    vault_service_path.write_text(VAULT_SERVICE_CODE)
                    self.files_updated += 1
                else:
                    self._log(f"Would update Vault service at {vault_service_path} (dry run)")
        else:
            logger.info(f"Creating Vault service at {vault_service_path}")
            if not self.dry_run:
                vault_service_path.write_text(VAULT_SERVICE_CODE)
                self.files_updated += 1
            else:
                self._log(f"Would create Vault service at {vault_service_path} (dry run)")

    def _update_blockchain_service(self):
        """Update the blockchain service with enhanced security."""
        blockchain_service_path = self.root_dir / BLOCKCHAIN_FILES["service"]

        if not blockchain_service_path.exists():
            logger.warning(f"Blockchain service not found at {blockchain_service_path}")
            return

        logger.info(f"Updating blockchain service at {blockchain_service_path}")

        # Read existing service to extract any custom code
        existing_code = blockchain_service_path.read_text()

        # Extract contract ABI
        abi_match = re.search(r'TRUST_CERTIFICATE_ABI\s*=\s*(\[.*?\])', existing_code, re.DOTALL)
        abi_code = "TRUST_CERTIFICATE_ABI = []"
        if abi_match:
            abi_code = f"TRUST_CERTIFICATE_ABI = {abi_match.group(1)}"

        # Extract settings import
        settings_import = "from apps.api.config.settings import settings"
        settings_match = re.search(r'from\s+[\w.]+\s+import\s+settings', existing_code)
        if settings_match:
            settings_import = settings_match.group(0)

        # Create enhanced blockchain service
        enhanced_code = f"""
{settings_import}
import datetime
{abi_code}

{VAULT_INTEGRATION_CODE}
"""

        if not self.dry_run:
            blockchain_service_path.write_text(enhanced_code)
            self.files_updated += 1
        else:
            self._log(f"Would update blockchain service at {blockchain_service_path} (dry run)")

    def _add_blockchain_monitoring(self):
        """Add blockchain monitoring configuration."""
        monitoring_path = self.root_dir / BLOCKCHAIN_FILES["monitoring"]

        # Create directory if it doesn't exist
        monitoring_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Adding blockchain monitoring at {monitoring_path}")

        if not self.dry_run:
            monitoring_path.write_text(PROMETHEUS_ALERTS)
            self.files_updated += 1
        else:
            self._log(f"Would add blockchain monitoring at {monitoring_path} (dry run)")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Enhance blockchain security in the Maily platform.")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying them")
    parser.add_argument("--verbose", action="store_true", help="Show detailed information during execution")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    enhancer = BlockchainSecurityEnhancer(dry_run=args.dry_run, verbose=args.verbose)

    if args.dry_run:
        logger.info("Dry run mode. No changes will be applied.")

    enhancer.enhance_blockchain_security()

if __name__ == "__main__":
    main()
