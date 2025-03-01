#!/usr/bin/env python3
"""
Blockchain diagnostics tool for Maily blockchain infrastructure.
Tests connection to blockchain providers, contract validity, and transaction capabilities.
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import requests

# Add project paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

try:
    # Import services directly from the project
    from services.blockchain import BlockchainService
    from config.settings import get_settings
except ImportError:
    print("Failed to import project modules. Make sure you're running from the project root.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("blockchain-diagnostics")

# Get settings
settings = get_settings()

class BlockchainDiagnostics:
    """Diagnostic tool for blockchain services."""

    def __init__(self, verbose: bool = False):
        """Initialize the diagnostics tool.

        Args:
            verbose: Whether to enable verbose output
        """
        self.verbose = verbose
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": os.environ.get("ENVIRONMENT", "development"),
            "tests": {},
            "summary": {
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "skipped": 0
            }
        }

        # Initialize blockchain service
        try:
            self.blockchain_service = BlockchainService()
            self.results["config"] = {
                "provider_url": self.mask_url(self.blockchain_service.provider_url),
                "network": self.blockchain_service.network,
                "contract_address": self.blockchain_service.contract_address,
                "enabled": self.blockchain_service.enabled,
                "gas_price_strategy": self.blockchain_service.gas_price_strategy
            }
        except Exception as e:
            logger.error(f"Failed to initialize blockchain service: {e}")
            self.blockchain_service = None
            self.results["config"] = {
                "error": str(e),
                "provider_url": settings.BLOCKCHAIN_PROVIDER_URL,
                "enabled": settings.BLOCKCHAIN_ENABLED
            }

    def mask_url(self, url: str) -> str:
        """Mask sensitive information in URLs.

        Args:
            url: URL to mask

        Returns:
            Masked URL
        """
        if not url:
            return ""

        # Mask API keys in the URL
        if "infura.io" in url and "/v3/" in url:
            parts = url.split("/v3/")
            if len(parts) > 1:
                return f"{parts[0]}/v3/****{parts[1][-4:]}"

        return url

    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run all diagnostic tests.

        Returns:
            Dictionary of test results
        """
        logger.info("Starting blockchain diagnostics")

        # Check if blockchain is enabled
        await self.test_blockchain_enabled()

        # Skip remaining tests if blockchain is not enabled
        if not self.blockchain_service or not self.blockchain_service.enabled:
            logger.warning("Skipping remaining tests as blockchain is not enabled")
            self.record_result("blockchain_configuration", "skipped", "Blockchain is not enabled")
            return self.results

        # Run tests
        await self.test_provider_connection()
        await self.test_contract_validity()
        await self.test_account_setup()
        await self.test_network_status()
        await self.test_gas_price()

        # Generate summary
        self.summarize_results()

        return self.results

    def record_result(self, test_name: str, status: str, message: str, details: Any = None) -> None:
        """Record a test result.

        Args:
            test_name: Name of the test
            status: "passed", "failed", "warning", or "skipped"
            message: Result message
            details: Additional details (optional)
        """
        self.results["tests"][test_name] = {
            "status": status,
            "message": message,
        }

        if details:
            self.results["tests"][test_name]["details"] = details

        # Update summary counters
        if status == "passed":
            self.results["summary"]["passed"] += 1
        elif status == "failed":
            self.results["summary"]["failed"] += 1
        elif status == "warning":
            self.results["summary"]["warnings"] += 1
        elif status == "skipped":
            self.results["summary"]["skipped"] += 1

        # Log result
        if status == "passed":
            logger.info(f"✅ {test_name}: {message}")
        elif status == "failed":
            logger.error(f"❌ {test_name}: {message}")
        elif status == "warning":
            logger.warning(f"⚠️ {test_name}: {message}")
        else:
            logger.info(f"⏭️ {test_name}: {message}")

    async def test_blockchain_enabled(self) -> None:
        """Test if blockchain is enabled and properly configured."""
        if not self.blockchain_service:
            self.record_result(
                "blockchain_enabled",
                "failed",
                "Failed to initialize blockchain service"
            )
            return

        if not self.blockchain_service.enabled:
            self.record_result(
                "blockchain_enabled",
                "warning",
                "Blockchain verification is disabled"
            )
            return

        # Check for required config
        missing_config = []
        if not self.blockchain_service.provider_url:
            missing_config.append("provider_url")
        if not self.blockchain_service.private_key:
            missing_config.append("private_key")
        if not self.blockchain_service.contract_address:
            missing_config.append("contract_address")

        if missing_config:
            self.record_result(
                "blockchain_enabled",
                "failed",
                f"Blockchain is enabled but missing configuration: {', '.join(missing_config)}"
            )
            return

        self.record_result(
            "blockchain_enabled",
            "passed",
            "Blockchain verification is enabled and configured properly"
        )

    async def test_provider_connection(self) -> None:
        """Test connection to blockchain provider."""
        if not self.blockchain_service or not self.blockchain_service.w3:
            self.record_result(
                "provider_connection",
                "failed",
                "Web3 provider not initialized"
            )
            return

        try:
            # Check if connected to the network
            connected = self.blockchain_service.w3.isConnected()

            if not connected:
                self.record_result(
                    "provider_connection",
                    "failed",
                    f"Failed to connect to provider at {self.mask_url(self.blockchain_service.provider_url)}"
                )
                return

            # Get some basic network info
            chain_id = self.blockchain_service.w3.eth.chain_id
            block_number = self.blockchain_service.w3.eth.block_number
            gas_price = self.blockchain_service.w3.eth.gas_price

            details = {
                "chain_id": chain_id,
                "block_number": block_number,
                "gas_price": gas_price,
                "connected": connected
            }

            self.record_result(
                "provider_connection",
                "passed",
                f"Successfully connected to {self.blockchain_service.network} (Chain ID: {chain_id})",
                details
            )
        except Exception as e:
            self.record_result(
                "provider_connection",
                "failed",
                f"Error connecting to provider: {str(e)}"
            )

    async def test_contract_validity(self) -> None:
        """Test if the smart contract is valid and accessible."""
        if not self.blockchain_service or not self.blockchain_service.contract:
            self.record_result(
                "contract_validity",
                "failed",
                "Contract not initialized"
            )
            return

        try:
            # Try to call a view function to verify contract
            functions = self.blockchain_service.contract.functions

            # Check if contract has expected functions
            expected_functions = ["issueCertificate", "verifyCertificate", "generateMetricsHash", "revokeCertificate"]
            missing_functions = []

            for func in expected_functions:
                if not hasattr(functions, func):
                    missing_functions.append(func)

            if missing_functions:
                self.record_result(
                    "contract_validity",
                    "failed",
                    f"Contract at {self.blockchain_service.contract_address} is missing expected functions: {', '.join(missing_functions)}"
                )
                return

            self.record_result(
                "contract_validity",
                "passed",
                f"Contract at {self.blockchain_service.contract_address} is valid and has all expected functions"
            )
        except Exception as e:
            self.record_result(
                "contract_validity",
                "failed",
                f"Error validating contract: {str(e)}"
            )

    async def test_account_setup(self) -> None:
        """Test if the account is properly set up."""
        if not self.blockchain_service or not self.blockchain_service.account:
            self.record_result(
                "account_setup",
                "failed",
                "Account not initialized"
            )
            return

        try:
            # Get account address and balance
            address = self.blockchain_service.account.address
            balance = self.blockchain_service.w3.eth.get_balance(address)

            # Check if account has enough balance for gas fees
            min_balance = 0.01 * 10**18  # 0.01 native token

            details = {
                "address": address,
                "balance": balance,
                "balance_eth": balance / 10**18
            }

            if balance < min_balance:
                self.record_result(
                    "account_setup",
                    "warning",
                    f"Account {address} has low balance ({balance / 10**18:.6f} ETH), may not be able to pay for gas",
                    details
                )
                return

            self.record_result(
                "account_setup",
                "passed",
                f"Account {address} is properly set up with sufficient balance ({balance / 10**18:.6f} ETH)",
                details
            )
        except Exception as e:
            self.record_result(
                "account_setup",
                "failed",
                f"Error checking account: {str(e)}"
            )

    async def test_network_status(self) -> None:
        """Test the status of the blockchain network."""
        if not self.blockchain_service or not self.blockchain_service.w3:
            self.record_result(
                "network_status",
                "failed",
                "Web3 provider not initialized"
            )
            return

        try:
            # Get network stats
            latest_block = self.blockchain_service.w3.eth.get_block('latest')

            # Check if network is congested
            gas_used_percent = latest_block.gasUsed / latest_block.gasLimit * 100

            details = {
                "block_number": latest_block.number,
                "timestamp": datetime.fromtimestamp(latest_block.timestamp).isoformat(),
                "gas_limit": latest_block.gasLimit,
                "gas_used": latest_block.gasUsed,
                "gas_used_percent": gas_used_percent,
                "transaction_count": len(latest_block.transactions)
            }

            if gas_used_percent > 80:
                self.record_result(
                    "network_status",
                    "warning",
                    f"Network is congested ({gas_used_percent:.2f}% gas used)",
                    details
                )
                return

            # Check block time
            network_name = self.blockchain_service.network
            if network_name == "polygon":
                expected_block_time = 2.5  # seconds
            else:
                expected_block_time = 13  # seconds

            prev_block = self.blockchain_service.w3.eth.get_block(latest_block.number - 1)
            block_time = latest_block.timestamp - prev_block.timestamp

            details["previous_block_timestamp"] = datetime.fromtimestamp(prev_block.timestamp).isoformat()
            details["block_time"] = block_time

            if block_time > expected_block_time * 2:
                self.record_result(
                    "network_status",
                    "warning",
                    f"Network may be slow (block time: {block_time:.2f}s, expected: {expected_block_time:.2f}s)",
                    details
                )
                return

            self.record_result(
                "network_status",
                "passed",
                f"Network is healthy (block time: {block_time:.2f}s, gas usage: {gas_used_percent:.2f}%)",
                details
            )
        except Exception as e:
            self.record_result(
                "network_status",
                "failed",
                f"Error checking network status: {str(e)}"
            )

    async def test_gas_price(self) -> None:
        """Test current gas prices on the network."""
        if not self.blockchain_service or not self.blockchain_service.w3:
            self.record_result(
                "gas_price",
                "failed",
                "Web3 provider not initialized"
            )
            return

        try:
            # Get gas price
            gas_price = self.blockchain_service.w3.eth.gas_price
            gas_price_gwei = gas_price / 10**9

            # Check if gas price is reasonable
            network_name = self.blockchain_service.network

            if network_name == "polygon":
                high_gas_threshold = 100  # gwei
            else:
                high_gas_threshold = 20  # gwei

            details = {
                "gas_price": gas_price,
                "gas_price_gwei": gas_price_gwei,
                "strategy": self.blockchain_service.gas_price_strategy
            }

            if gas_price_gwei > high_gas_threshold:
                self.record_result(
                    "gas_price",
                    "warning",
                    f"Gas price is high ({gas_price_gwei:.2f} gwei)",
                    details
                )
                return

            # Try to estimate gas price using blockchain service's strategy
            if self.blockchain_service.gas_price_strategy == "fast":
                strategy_price = self.blockchain_service._fast_gas_price_strategy(
                    self.blockchain_service.w3, {}
                )
                details["strategy_price"] = strategy_price
                details["strategy_price_gwei"] = strategy_price / 10**9

            elif self.blockchain_service.gas_price_strategy == "medium":
                strategy_price = self.blockchain_service._medium_gas_price_strategy(
                    self.blockchain_service.w3, {}
                )
                details["strategy_price"] = strategy_price
                details["strategy_price_gwei"] = strategy_price / 10**9

            self.record_result(
                "gas_price",
                "passed",
                f"Gas price is reasonable ({gas_price_gwei:.2f} gwei)",
                details
            )
        except Exception as e:
            self.record_result(
                "gas_price",
                "failed",
                f"Error checking gas price: {str(e)}"
            )

    def summarize_results(self) -> None:
        """Generate a summary of test results."""
        total_tests = sum(self.results["summary"].values())

        if self.results["summary"]["failed"] > 0:
            status = "FAILED"
        elif self.results["summary"]["warnings"] > 0:
            status = "WARNING"
        else:
            status = "PASSED"

        self.results["overall_status"] = status

        failed_tests = [
            name for name, result in self.results["tests"].items()
            if result["status"] == "failed"
        ]

        warning_tests = [
            name for name, result in self.results["tests"].items()
            if result["status"] == "warning"
        ]

        self.results["summary"]["total"] = total_tests
        self.results["summary"]["failed_tests"] = failed_tests
        self.results["summary"]["warning_tests"] = warning_tests

        logger.info(f"Blockchain diagnostics completed: {status}")
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {self.results['summary']['passed']}")
        logger.info(f"Failed: {self.results['summary']['failed']}")
        logger.info(f"Warnings: {self.results['summary']['warnings']}")
        logger.info(f"Skipped: {self.results['summary']['skipped']}")

        if failed_tests:
            logger.error(f"Failed tests: {', '.join(failed_tests)}")

        if warning_tests:
            logger.warning(f"Tests with warnings: {', '.join(warning_tests)}")

async def main() -> None:
    """Run blockchain diagnostics."""
    parser = argparse.ArgumentParser(description="Blockchain diagnostics tool")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--output", "-o", help="Output file for results")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="text", help="Output format")
    args = parser.parse_args()

    diagnostics = BlockchainDiagnostics(verbose=args.verbose)
    results = await diagnostics.run_diagnostics()

    # Print results
    if args.format == "json":
        print(json.dumps(results, indent=2))

    # Save results if output file specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
            logger.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())
