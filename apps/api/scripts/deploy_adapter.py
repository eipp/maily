#!/usr/bin/env python3
"""
Deployment script for the adapter service in compatibility mode.

This script:
1. Sets up the adapter service with authentication bridge
2. Implements endpoint routing between implementations
3. Sets up model conversion for request/response data
4. Starts the adapter service
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Deploy adapter service in compatibility mode")
    parser.add_argument(
        "--mode",
        choices=["unified", "bridge", "standardized"],
        default="unified",
        help="Deployment mode: unified (both implementations), bridge (adapter bridge), or standardized (fixed with standardization)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the service on"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the service to"
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Logging level"
    )
    return parser.parse_args()

def deploy_adapter(mode, host, port, log_level):
    """
    Deploy the adapter service.

    Args:
        mode: Deployment mode (unified, bridge, or standardized)
        host: Host to bind the service to
        port: Port to run the service on
        log_level: Logging level
    """
    # Get the path to the API directory
    script_dir = Path(__file__).resolve().parent
    api_dir = script_dir.parent

    # Deployment modes
    if mode == "unified":
        logger.info(f"Deploying unified adapter service on {host}:{port}")
        adapter_script = api_dir / "main_adapter.py"
    elif mode == "bridge":
        logger.info(f"Deploying adapter bridge service on {host}:{port}")
        adapter_script = api_dir / "adapter_bridge.py"
    elif mode == "standardized":
        logger.info(f"Deploying standardized fixed implementation on {host}:{port}")
        adapter_script = api_dir / "api_standardization.py"
    else:
        logger.error(f"Unknown deployment mode: {mode}")
        return 1

    # Make the script executable if it's not already
    if not os.access(adapter_script, os.X_OK):
        logger.info(f"Making {adapter_script} executable")
        os.chmod(adapter_script, 0o755)

    # Build the command
    cmd = [
        str(adapter_script),
        "--host", host,
        "--port", str(port),
        "--log-level", log_level
    ]

    # Run the command
    logger.info(f"Starting adapter service with command: {' '.join(cmd)}")
    try:
        return subprocess.call(cmd)
    except Exception as e:
        logger.error(f"Failed to start adapter service: {e}")
        return 1

def main():
    """Main entry point."""
    args = parse_arguments()
    return deploy_adapter(args.mode, args.host, args.port, args.log_level)

if __name__ == "__main__":
    sys.exit(main())
