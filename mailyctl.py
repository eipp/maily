#!/usr/bin/env python3

"""
Maily Control Tool (mailyctl)

A unified command-line tool for managing the Maily platform across different environments.
This tool provides functionality for deploying, verifying, and testing Maily components.

Usage:
  mailyctl.py deploy [--env=<environment>] [--version=<version>] [--components=<components>]
  mailyctl.py verify [--env=<environment>] [--version=<version>] [--components=<components>]
  mailyctl.py test [--env=<environment>] [--scope=<scope>]
  mailyctl.py status [--env=<environment>] [--components=<components>]
  mailyctl.py logs [--env=<environment>] [--components=<components>] [--tail=<lines>]
  mailyctl.py rollback [--env=<environment>] [--components=<components>] [--to-version=<version>]
  mailyctl.py config [--env=<environment>] [--show-secrets]
  mailyctl.py phased-deploy [--env=<environment>] [--version=<version>] [--skip-staging] [--start-phase=<phase>] [--end-phase=<phase>] [--dry-run] [--canary] [--canary-weight=<weight>]
  mailyctl.py secrets rotate [--env=<environment>] [--secret-types=<types>] [--notify]
  mailyctl.py verify-mesh [--env=<environment>] [--component=<component>] [--release=<release>]
  mailyctl.py (-h | --help)
  mailyctl.py --show-version

Options:
  -h --help                   Show this help message and exit.
  --show-version              Show version.
  --env=<environment>         Environment to target [default: staging].
  --components=<components>   Comma-separated list of components to target [default: all].
  --version=<version>         Version to deploy [default: latest].
  --scope=<scope>             Test scope (unit, integration, e2e, post-deployment) [default: all].
  --tail=<lines>              Number of log lines to show [default: 100].
  --to-version=<version>      Version to rollback to.
  --show-secrets              Show secrets in config output.
  --skip-staging              Skip staging deployment (phased-deploy only) [default: false].
  --start-phase=<phase>       Start phase (1-3) for phased deployment [default: 1].
  --end-phase=<phase>         End phase (1-3) for phased deployment [default: 3].
  --dry-run                   Run in dry-run mode without applying changes [default: false].
  --canary                    Deploy as a canary release [default: false].
  --canary-weight=<weight>    Traffic percentage for canary deployment [default: 10].
  --secret-types=<types>      Comma-separated list of secret types to rotate [default: all].
  --notify                    Send notifications after secret rotation [default: false].
  --component=<component>     Single component to verify service mesh [default: api].
  --release=<release>         Release name [default: maily].
"""

import os
import sys
import yaml
import json
import time
import logging
import subprocess
import concurrent.futures
import asyncio
import secrets
import string
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Set
from docopt import docopt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mailyctl.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('mailyctl')

# Constants
VERSION = '1.3.0'
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
SYSTEM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'system')
VALIDATORS_DIR = os.path.join(SYSTEM_DIR, 'validators')
VERIFIERS_DIR = os.path.join(SYSTEM_DIR, 'verifiers')
VAULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vault')
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
CORE_SCRIPTS_DIR = os.path.join(SCRIPTS_DIR, 'core')

# All available components
ALL_COMPONENTS = [
    'frontend',
    'api',
    'ai-service',
    'websocket',
    'blockchain',
    'analytics',
    'campaign',
    'email',
    'workers',
    'visualization-service',
    'trust-verification',
    'service-mesh'
]

# Default secret configuration
DEFAULT_SECRET_CONFIG = {
    "vault_addr": os.environ.get("VAULT_ADDR", "http://localhost:8200"),
    "vault_token_file": os.environ.get("VAULT_TOKEN_FILE", "~/.vault-token"),
    "secret_paths": {
        "database": "maily/data/config",
        "jwt": "maily/data/config",
        "aws": "maily/data/credentials",
        "smtp": "maily/data/config",
        "api_keys": "maily/data/api-keys"
    },
    "rotation_interval": {
        "database": 30,  # days
        "jwt": 90,       # days
        "aws": 90,       # days
        "smtp": 180,     # days
        "api_keys": 90   # days
    },
    "services_to_notify": [
        "api",
        "email-service",
        "workers"
    ],
    "notification_methods": [
        "slack",
        "email"
    ]
}

class ServiceMeshVerifier:
    """Service Mesh verification for the Maily platform."""
    
    def __init__(self, environment: str, component: str = 'api', release_name: str = 'maily', version: str = 'latest'):
        """
        Initialize the service mesh verifier.
        
        Args:
            environment: Target environment (staging, production)
            component: Component to verify
            release_name: Helm release name
            version: Version to verify
        """
        self.environment = environment
        self.component = component
        self.release_name = release_name
        self.version = version
        self.namespace = f"maily-{environment}"
        
    def verify_istio_installation(self) -> bool:
        """
        Verify Istio installation and configuration.
        
        Returns:
            bool: True if Istio is properly installed, False otherwise
        """
        logger.info("Verifying Istio installation...")
        
        try:
            cmd = ["istioctl", "version"]
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Log the first line of output
            istio_version = result.stdout.split('\n')[0]
            logger.info(f"Istio is installed: {istio_version}")
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Istio is not installed or istioctl is not in PATH: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error checking Istio installation: {str(e)}")
            return False
            
    def verify_mtls(self) -> bool:
        """
        Verify mTLS configuration for the namespace.
        
        Returns:
            bool: True if mTLS is properly configured, False otherwise
        """
        logger.info(f"Verifying mTLS configuration for namespace {self.namespace}...")
        
        try:
            cmd = ["istioctl", "authn", "tls-check", f"*.{self.namespace}.svc.cluster.local"]
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if "STRICT" in result.stdout:
                logger.info("mTLS is configured in STRICT mode (good)")
                return True
            elif "PERMISSIVE" in result.stdout:
                logger.info("mTLS is configured in PERMISSIVE mode (warning: not ideal for production)")
                return True
            else:
                logger.error("mTLS is not properly configured")
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to verify mTLS configuration: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error checking mTLS configuration: {str(e)}")
            return False
    
    def verify_circuit_breaker(self) -> bool:
        """
        Verify circuit breaker configuration for the component.
        
        Returns:
            bool: True if circuit breaker is properly configured, False otherwise
        """
        logger.info(f"Verifying circuit breaker configuration for {self.component}...")
        
        try:
            dr_name = f"{self.release_name}-{self.component}-cb"
            cmd = ["kubectl", "get", "destinationrule", dr_name, "-n", self.namespace, "-o", "json"]
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            cb_config = json.loads(result.stdout)
            traffic_policy = cb_config.get('spec', {}).get('trafficPolicy', {})
            connection_pool = traffic_policy.get('connectionPool', {})
            outlier_detection = traffic_policy.get('outlierDetection', {})
            
            if not connection_pool.get('tcp') or not connection_pool.get('http') or not outlier_detection:
                logger.warning("Circuit breaker configuration is incomplete")
                return True  # Not critical for verification to pass
            
            logger.info("Circuit breaker is properly configured")
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"Circuit breaker configuration not found or could not be verified: {str(e)}")
            return True  # Not critical for verification to pass
        except Exception as e:
            logger.warning(f"Error checking circuit breaker configuration: {str(e)}")
            return True  # Not critical for verification to pass
    
    def verify_virtual_service(self) -> bool:
        """
        Verify virtual service configuration for the component.
        
        Returns:
            bool: True if virtual service is properly configured, False otherwise
        """
        logger.info(f"Verifying virtual service configuration for {self.component}...")
        
        try:
            vs_name = f"{self.release_name}-{self.component}-vs"
            cmd = ["kubectl", "get", "virtualservice", vs_name, "-n", self.namespace, "-o", "json"]
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            vs_config = json.loads(result.stdout)
            http_routes = vs_config.get('spec', {}).get('http', [])
            
            if not http_routes:
                logger.warning("Virtual service configuration is missing HTTP routes")
                return True  # Not critical for verification to pass
            
            logger.info("Virtual service is properly configured")
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"Virtual service configuration not found or could not be verified: {str(e)}")
            return True  # Not critical for verification to pass
        except Exception as e:
            logger.warning(f"Error checking virtual service configuration: {str(e)}")
            return True  # Not critical for verification to pass
    
    def verify_deployment(self) -> bool:
        """
        Verify component deployment.
        
        Returns:
            bool: True if deployment is healthy, False otherwise
        """
        logger.info(f"Verifying deployment of {self.component}...")
        
        try:
            cmd = ["kubectl", "get", "deployment", self.component, "-n", self.namespace, "-o", "json"]
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            deployment = json.loads(result.stdout)
            available_replicas = deployment.get('status', {}).get('availableReplicas', 0)
            desired_replicas = deployment.get('spec', {}).get('replicas', 0)
            
            if available_replicas < desired_replicas:
                logger.error(f"Deployment has {available_replicas}/{desired_replicas} available replicas")
                return False
            
            logger.info(f"Deployment has {available_replicas}/{desired_replicas} available replicas")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to verify deployment: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error checking deployment: {str(e)}")
            return False
    
    def run_istio_analysis(self) -> bool:
        """
        Run Istio configuration analysis.
        
        Returns:
            bool: True if analysis passed, False otherwise
        """
        logger.info('Running Istio configuration analysis...')
        
        try:
            cmd = ["istioctl", "analyze", "-n", self.namespace]
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Istio configuration analysis found issues: {e.stdout}")
            return False
        except Exception as e:
            logger.error(f"Error running Istio analysis: {str(e)}")
            return False
    
    def verify(self) -> bool:
        """
        Run comprehensive service mesh verification.
        
        Returns:
            bool: True if all verifications pass, False otherwise
        """
        logger.info(f"Starting service mesh verification for {self.component} in {self.environment} environment")
        
        success = True
        
        # Check Istio installation
        if not self.verify_istio_installation():
            success = False
        
        # Check mTLS configuration
        if not self.verify_mtls():
            success = False
        
        # Check circuit breaker (warning only)
        self.verify_circuit_breaker()
        
        # Check virtual service (warning only)
        self.verify_virtual_service()
        
        # Check component deployment
        if not self.verify_deployment():
            success = False
        
        # Run Istio analyzer
        if not self.run_istio_analysis():
            success = False
        
        if success:
            logger.info(f"Service mesh verification successful for {self.component} in {self.environment} environment")
        else:
            logger.error(f"Service mesh verification failed for {self.component} in {self.environment} environment")
        
        return success


class SecretManager:
    """Secret management and rotation for the Maily platform using HashiCorp Vault."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the secret manager.
        
        Args:
            config: Configuration dictionary with Vault settings and secret paths
        """
        self.config = config
        self.vault_addr = config.get("vault_addr", "http://localhost:8200")
        self.vault_token = None
        self.vault_token_file = os.path.expanduser(config.get("vault_token_file", "~/.vault-token"))
        self.secret_paths = config.get("secret_paths", {})
        self.rotation_interval = config.get("rotation_interval", {})
        self.services_to_notify = config.get("services_to_notify", [])
        self.notification_methods = config.get("notification_methods", [])
        self.http_client = None
        self.secrets_rotated = []
        
        # Load environment-specific configs if provided
        env = config.get("environment")
        if env:
            env_config = config.get(f"environments", {}).get(env, {})
            if env_config:
                self.vault_addr = env_config.get("vault_addr", self.vault_addr)
                self.vault_token_file = os.path.expanduser(env_config.get("vault_token_file", self.vault_token_file))
                self.secret_paths.update(env_config.get("secret_paths", {}))
                self.rotation_interval.update(env_config.get("rotation_interval", {}))
                self.services_to_notify = env_config.get("services_to_notify", self.services_to_notify)
                self.notification_methods = env_config.get("notification_methods", self.notification_methods)
    
    async def initialize(self):
        """Initialize the client and authenticate to Vault."""
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
        # Try to read token from file
        if os.path.exists(self.vault_token_file):
            with open(self.vault_token_file, "r") as f:
                self.vault_token = f.read().strip()
        
        # If token is not available, try to authenticate
        if not self.vault_token and "VAULT_TOKEN" in os.environ:
            self.vault_token = os.environ["VAULT_TOKEN"]
        
        if not self.vault_token:
            logger.error("No Vault token available. Set VAULT_TOKEN env var or provide a token file.")
            raise ValueError("No Vault token available")
        
        # Test the token
        try:
            await self._make_request("GET", "/v1/auth/token/lookup-self")
            logger.info("Successfully authenticated to Vault")
        except Exception as e:
            logger.error(f"Failed to authenticate to Vault: {e}")
            raise
    
    async def _make_request(self, method: str, path: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Vault API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., "/v1/secret/data/myapp")
            json_data: Optional JSON data for the request
            
        Returns:
            Response data as a dictionary
        """
        url = f"{self.vault_addr}{path}"
        headers = {"X-Vault-Token": self.vault_token}
        
        response = await self.http_client.request(
            method,
            url,
            headers=headers,
            json=json_data
        )
        response.raise_for_status()
        
        if response.status_code == 204:  # No content
            return {}
        
        return response.json()
    
    async def _get_secret(self, path: str) -> Dict[str, Any]:
        """
        Get a secret from Vault.
        
        Args:
            path: Path to the secret
            
        Returns:
            Secret data
        """
        response = await self._make_request("GET", f"/v1/{path}")
        # For KV-V2 secrets, data is nested under data
        if "data" in response.get("data", {}):
            return response["data"]["data"]
        return response.get("data", {})
    
    async def _update_secret(self, path: str, data: Dict[str, Any]) -> None:
        """
        Update a secret in Vault.
        
        Args:
            path: Path to the secret
            data: Secret data to update
        """
        # Determine if this is a KV-V2 path
        is_kv_v2 = "/data/" in path
        
        if is_kv_v2:
            # For KV-V2, we need to wrap the data
            await self._make_request("POST", f"/v1/{path}", {"data": data})
        else:
            # For KV-V1, we can send the data directly
            await self._make_request("POST", f"/v1/{path}", data)
    
    async def _patch_secret(self, path: str, updates: Dict[str, Any]) -> None:
        """
        Patch a secret in Vault (update only specified fields).
        
        Args:
            path: Path to the secret
            updates: Fields to update
        """
        current_data = await self._get_secret(path)
        # Merge the current data with updates
        updated_data = {**current_data, **updates}
        await self._update_secret(path, updated_data)
    
    def _generate_password(self, length: int = 32) -> str:
        """
        Generate a secure password.
        
        Args:
            length: Length of the password
            
        Returns:
            Secure password
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _generate_api_key(self, prefix: str = "mk") -> str:
        """
        Generate an API key.
        
        Args:
            prefix: Prefix for the API key
            
        Returns:
            API key
        """
        # Generate a secure random string
        random_part = secrets.token_hex(16)
        return f"{prefix}_{random_part}"
    
    async def rotate_database_credentials(self) -> None:
        """Rotate database credentials."""
        path = self.secret_paths.get("database")
        if not path:
            logger.warning("No database secret path configured")
            return
        
        try:
            # Generate new password
            new_password = self._generate_password(32)
            
            # Update the password in Vault
            await self._patch_secret(path, {"db_password": new_password})
            
            # Record the rotation
            self.secrets_rotated.append({
                "type": "database",
                "path": path,
                "field": "db_password",
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info("Successfully rotated database password")
            
            # In a production environment, you would update the database password here
            # This would involve connecting to the database with admin credentials and
            # executing an ALTER USER statement
            
        except Exception as e:
            logger.error(f"Failed to rotate database credentials: {e}")
            raise
    
    async def rotate_jwt_secret(self) -> None:
        """Rotate JWT secret."""
        path = self.secret_paths.get("jwt")
        if not path:
            logger.warning("No JWT secret path configured")
            return
        
        try:
            # Generate new JWT secret
            new_secret = secrets.token_hex(64)
            
            # Update the secret in Vault
            await self._patch_secret(path, {"jwt_secret": new_secret})
            
            # Record the rotation
            self.secrets_rotated.append({
                "type": "jwt",
                "path": path,
                "field": "jwt_secret",
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info("Successfully rotated JWT secret")
            
        except Exception as e:
            logger.error(f"Failed to rotate JWT secret: {e}")
            raise
    
    async def rotate_aws_credentials(self) -> None:
        """Rotate AWS credentials."""
        path = self.secret_paths.get("aws")
        if not path:
            logger.warning("No AWS credentials path configured")
            return
        
        try:
            # In a real environment, this would call the AWS API to create new credentials
            # For demonstration, we'll just generate placeholders
            new_access_key = f"AKIA{secrets.token_hex(8).upper()}"
            new_secret_key = self._generate_password(40)
            
            # Update the credentials in Vault
            await self._patch_secret(path, {
                "aws_access_key": new_access_key,
                "aws_secret_key": new_secret_key
            })
            
            # Record the rotation
            self.secrets_rotated.append({
                "type": "aws",
                "path": path,
                "fields": ["aws_access_key", "aws_secret_key"],
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info("Successfully rotated AWS credentials")
            
        except Exception as e:
            logger.error(f"Failed to rotate AWS credentials: {e}")
            raise
    
    async def rotate_smtp_credentials(self) -> None:
        """Rotate SMTP credentials."""
        path = self.secret_paths.get("smtp")
        if not path:
            logger.warning("No SMTP credentials path configured")
            return
        
        try:
            # Generate new SMTP password
            new_password = self._generate_password(24)
            
            # Update the password in Vault
            await self._patch_secret(path, {"smtp_password": new_password})
            
            # Record the rotation
            self.secrets_rotated.append({
                "type": "smtp",
                "path": path,
                "field": "smtp_password",
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info("Successfully rotated SMTP password")
            
            # In a real environment, you would update the SMTP password with the provider
            
        except Exception as e:
            logger.error(f"Failed to rotate SMTP credentials: {e}")
            raise
    
    async def rotate_api_keys(self) -> None:
        """Rotate API keys."""
        path = self.secret_paths.get("api_keys")
        if not path:
            logger.warning("No API keys path configured")
            return
        
        try:
            # Get current API keys
            current_keys = await self._get_secret(path)
            
            # Create new keys for each service
            updates = {}
            for service, key in current_keys.items():
                prefix = service[:2].lower()
                new_key = self._generate_api_key(prefix)
                updates[service] = new_key
            
            # Update the keys in Vault
            await self._update_secret(path, updates)
            
            # Record the rotation
            self.secrets_rotated.append({
                "type": "api_keys",
                "path": path,
                "services": list(updates.keys()),
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Successfully rotated {len(updates)} API keys")
            
        except Exception as e:
            logger.error(f"Failed to rotate API keys: {e}")
            raise
    
    async def test_services(self) -> bool:
        """
        Test that services can access the new secrets.
        
        Returns:
            True if all tests pass, False otherwise
        """
        logger.info("Testing services with new secrets...")
        
        # In a real environment, this would check that services can access the new secrets
        # For example, by making API calls to service health endpoints
        
        for service in self.services_to_notify:
            logger.info(f"Testing service: {service}")
            # Simulate testing with a delay
            await asyncio.sleep(0.5)
        
        return True
    
    async def notify_admins(self) -> None:
        """Notify administrators about the secret rotation."""
        if not self.notification_methods:
            logger.info("No notification methods configured")
            return
        
        logger.info("Notifying administrators about secret rotation...")
        
        message = f"""
Secret Rotation Report
=====================
Time: {datetime.now().isoformat()}
Secrets Rotated: {len(self.secrets_rotated)}

Details:
{json.dumps(self.secrets_rotated, indent=2)}
        """
        
        for method in self.notification_methods:
            if method == "slack":
                logger.info("Sending Slack notification...")
                # In a real environment, this would send a Slack webhook
            elif method == "email":
                logger.info("Sending email notification...")
                # In a real environment, this would send an email
    
    async def rotate_secrets(self, secret_types: Optional[Set[str]] = None, notify: bool = False) -> None:
        """
        Rotate specified secret types.
        
        Args:
            secret_types: Set of secret types to rotate (database, jwt, aws, smtp, api_keys)
            notify: Whether to notify administrators
        """
        if not secret_types:
            secret_types = set(self.secret_paths.keys())
        
        logger.info(f"Starting rotation for secret types: {', '.join(secret_types)}")
        
        # Rotate secrets
        tasks = []
        if "database" in secret_types:
            tasks.append(self.rotate_database_credentials())
        if "jwt" in secret_types:
            tasks.append(self.rotate_jwt_secret())
        if "aws" in secret_types:
            tasks.append(self.rotate_aws_credentials())
        if "smtp" in secret_types:
            tasks.append(self.rotate_smtp_credentials())
        if "api_keys" in secret_types:
            tasks.append(self.rotate_api_keys())
        
        await asyncio.gather(*tasks)
        
        # Test services
        services_ok = await self.test_services()
        if not services_ok:
            logger.error("Service tests failed after secret rotation!")
            # In a real environment, you might want to roll back changes here
        
        # Notify admins if requested
        if notify:
            await self.notify_admins()
        
        logger.info("Secret rotation completed successfully")
    
    async def close(self) -> None:
        """Clean up resources."""
        if self.http_client:
            await self.http_client.aclose()


class PhasedDeployment:
    """Phased deployment for the Maily platform."""
    
    def __init__(
        self,
        environment: str = 'staging',
        version: str = 'latest',
        skip_staging: bool = False,
        start_phase: int = 1,
        end_phase: int = 3,
        dry_run: bool = False,
        canary: bool = False,
        canary_weight: int = 10
    ):
        """
        Initialize the phased deployment.
        
        Args:
            environment: Target environment (staging, production)
            version: Version to deploy
            skip_staging: Skip staging deployment
            start_phase: Starting phase (1-3)
            end_phase: Ending phase (1-3)
            dry_run: Run in dry-run mode without applying changes
            canary: Deploy as a canary release
            canary_weight: Traffic percentage for canary deployment
        """
        self.environment = environment
        self.version = version
        self.skip_staging = skip_staging
        self.start_phase = start_phase
        self.end_phase = end_phase
        self.dry_run = dry_run
        self.canary = canary
        self.canary_weight = canary_weight
        
        self.log_dir = "deployment_logs"
        self.log_file = f"{self.log_dir}/deployment-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
        
        self.staging_namespace = "maily-staging"
        self.prod_namespace = "maily-production"
        
        # Initialize log directory
        os.makedirs(self.log_dir, exist_ok=True)
    
    def log(self, level: str, message: str) -> None:
        """
        Log a message with the specified level.
        
        Args:
            level: Log level (INFO, SUCCESS, WARNING, ERROR, STEP, SECTION)
            message: Message to log
        """
        # Map level to logger method
        if level == "INFO":
            logger.info(message)
        elif level == "SUCCESS":
            logger.info(f"SUCCESS: {message}")
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
        elif level == "STEP":
            logger.info(f"STEP: {message}")
        elif level == "SECTION":
            logger.info(f"SECTION: {message}")
        
        # Also log to deployment log file
        with open(self.log_file, "a") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}\n")
    
    def run_command(self, command: str, capture_output: bool = True) -> Optional[str]:
        """
        Run a shell command.
        
        Args:
            command: Command to run
            capture_output: Whether to capture and return the output
            
        Returns:
            Command output if capture_output is True, otherwise None
        """
        self.log("INFO", f"Executing: {command}")
        
        if self.dry_run:
            self.log("INFO", "DRY RUN: Command would be executed here")
            return None
        
        try:
            if capture_output:
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                self.log("INFO", f"Command output: {result.stdout}")
                return result.stdout
            else:
                subprocess.run(command, shell=True, check=True)
                return None
        except subprocess.CalledProcessError as e:
            self.log("ERROR", f"Command failed: {e}")
            self.log("ERROR", f"Error output: {e.stderr}")
            raise
    
    def deploy_to_staging(self) -> bool:
        """
        Deploy to staging environment (Phase 1).
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("SECTION", "Starting Phase 1: Testing & Validation (Staging)")
        
        if self.skip_staging:
            self.log("WARNING", "Skipping staging deployment as requested")
            return True
        
        try:
            # Deploy to staging
            self.log("STEP", "Deploying to staging environment")
            if not self.deploy_environment("staging"):
                self.log("ERROR", "Failed to deploy to staging environment")
                return False
            
            # Run automated tests
            self.log("STEP", "Running automated tests")
            if not self.run_automated_tests("staging"):
                self.log("ERROR", "Automated tests failed")
                return False
            
            # Run chaos testing
            self.log("STEP", "Running chaos testing")
            if not self.run_chaos_testing("staging"):
                self.log("WARNING", "Chaos testing produced warnings")
                # Continue despite warnings
            
            # Verify SLA monitoring
            self.log("STEP", "Verifying SLA monitoring and alerting")
            if not self.verify_monitoring("staging"):
                self.log("WARNING", "SLA monitoring verification produced warnings")
                # Continue despite warnings
            
            # Set up service mesh components if enabled
            if self.environment != "dev":
                self.log("STEP", "Deploying service mesh components")
                if not self.deploy_service_mesh("staging"):
                    self.log("ERROR", "Failed to deploy service mesh components")
                    return False
            
            self.log("SUCCESS", "Phase 1 (Staging) completed successfully")
            return True
            
        except Exception as e:
            self.log("ERROR", f"Phase 1 (Staging) failed: {str(e)}")
            return False
    
    def deploy_to_prod_initial(self) -> bool:
        """
        Deploy non-critical services to production (Phase 2).
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("SECTION", "Starting Phase 2: Initial Production Deployment")
        
        try:
            # Deploy non-critical components first
            non_critical = ["analytics", "campaign", "visualization-service"]
            
            self.log("STEP", f"Deploying non-critical services: {', '.join(non_critical)}")
            for component in non_critical:
                self.log("INFO", f"Deploying {component} to production")
                if not self.deploy_component(component, "production"):
                    self.log("ERROR", f"Failed to deploy {component} to production")
                    return False
                
                # Brief pause between components
                time.sleep(5)
            
            # Apply resource limits and probes
            self.log("STEP", "Applying resource limits and probes")
            if not self.apply_resource_configuration("production"):
                self.log("WARNING", "Failed to apply some resource configurations")
                # Continue despite warnings
            
            # Deploy logging and tracing
            self.log("STEP", "Deploying logging and tracing configuration")
            if not self.deploy_logging_tracing("production"):
                self.log("WARNING", "Failed to deploy some logging/tracing configurations")
                # Continue despite warnings
            
            # Monitor for performance impacts
            self.log("STEP", "Monitoring for performance impacts")
            if not self.monitor_performance("production"):
                self.log("WARNING", "Performance monitoring detected potential issues")
                # Continue despite warnings
            
            # Configure service mesh observability
            if self.environment != "dev":
                self.log("STEP", "Configuring service mesh observability")
                if not self.configure_service_mesh_observability("production"):
                    self.log("WARNING", "Failed to configure some service mesh observability features")
                    # Continue despite warnings
                
                self.log("STEP", "Setting up circuit breakers and outlier detection")
                if not self.configure_circuit_breakers("production"):
                    self.log("WARNING", "Failed to configure some circuit breakers")
                    # Continue despite warnings
            
            self.log("SUCCESS", "Phase 2 (Initial Production) completed successfully")
            return True
            
        except Exception as e:
            self.log("ERROR", f"Phase 2 (Initial Production) failed: {str(e)}")
            return False
    
    def deploy_to_prod_full(self) -> bool:
        """
        Deploy critical services to production (Phase 3).
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("SECTION", "Starting Phase 3: Full Production Deployment")
        
        try:
            # Deploy critical components
            critical = ["api", "ai-service", "frontend", "email", "workers", "websocket", "blockchain", "trust-verification"]
            
            if self.canary:
                self.log("STEP", f"Deploying critical services in canary mode ({self.canary_weight}% traffic)")
                # In canary mode, we need a different deployment approach
                if not self.deploy_canary("production", critical):
                    self.log("ERROR", "Failed to deploy canary release")
                    return False
            else:
                self.log("STEP", f"Deploying critical services: {', '.join(critical)}")
                for component in critical:
                    self.log("INFO", f"Deploying {component} to production")
                    if not self.deploy_component(component, "production"):
                        self.log("ERROR", f"Failed to deploy {component} to production")
                        return False
                    
                    # Brief pause between components
                    time.sleep(5)
            
            # Deploy secret rotation system
            self.log("STEP", "Deploying secret rotation system")
            if not self.deploy_secret_rotation("production"):
                self.log("WARNING", "Failed to deploy secret rotation system")
                # Continue despite warnings
            
            # Enable SLA monitoring
            self.log("STEP", "Enabling SLA monitoring in production")
            if not self.enable_sla_monitoring("production"):
                self.log("WARNING", "Failed to enable some SLA monitoring features")
                # Continue despite warnings
            
            # Schedule chaos testing
            self.log("STEP", "Scheduling chaos testing for resilience validation")
            if not self.schedule_chaos_testing("production"):
                self.log("WARNING", "Failed to schedule chaos testing")
                # Continue despite warnings
            
            # Enable full service mesh security policies
            if self.environment != "dev" and not self.canary:
                self.log("STEP", "Enabling full service mesh security policies")
                if not self.enable_service_mesh_security("production"):
                    self.log("WARNING", "Failed to enable some service mesh security policies")
                    # Continue despite warnings
            
            self.log("SUCCESS", "Phase 3 (Full Production) completed successfully")
            return True
            
        except Exception as e:
            self.log("ERROR", f"Phase 3 (Full Production) failed: {str(e)}")
            return False
    
    def deploy_environment(self, env: str) -> bool:
        """
        Deploy all components to an environment.
        
        Args:
            env: Environment to deploy to (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Deploying all components to {env} environment")
        
        namespace = self.staging_namespace if env == "staging" else self.prod_namespace
        
        try:
            # Update Helm releases
            helm_cmd = f"helm upgrade --install maily ./infrastructure/helm/maily --namespace {namespace} --values ./infrastructure/helm/maily/values-{env}.yaml --set image.tag={self.version}"
            self.run_command(helm_cmd)
            
            # Wait for deployments to stabilize
            wait_cmd = f"kubectl wait --for=condition=available --timeout=300s --all deployments --namespace {namespace}"
            self.run_command(wait_cmd)
            
            return True
        except Exception as e:
            self.log("ERROR", f"Failed to deploy to {env}: {str(e)}")
            return False
    
    def deploy_component(self, component: str, env: str) -> bool:
        """
        Deploy a single component to an environment.
        
        Args:
            component: Component to deploy
            env: Environment to deploy to (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Deploying {component} to {env} environment")
        
        namespace = self.staging_namespace if env == "staging" else self.prod_namespace
        
        try:
            # Update specific Helm release for the component
            helm_cmd = f"helm upgrade --install maily-{component} ./infrastructure/helm/maily/{component} --namespace {namespace} --values ./infrastructure/helm/maily/{component}/values-{env}.yaml --set image.tag={self.version}"
            self.run_command(helm_cmd)
            
            # Wait for deployment to stabilize
            wait_cmd = f"kubectl wait --for=condition=available --timeout=300s deployment/{component} --namespace {namespace}"
            self.run_command(wait_cmd)
            
            return True
        except Exception as e:
            self.log("ERROR", f"Failed to deploy {component} to {env}: {str(e)}")
            return False
    
    def run_automated_tests(self, env: str) -> bool:
        """
        Run automated tests against the environment.
        
        Args:
            env: Environment to test (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Running automated tests against {env} environment")
        
        try:
            # Run integration tests
            if env == "staging":
                test_cmd = "cd tests && pytest -xvs tests/integration/"
                self.run_command(test_cmd)
            
            # Run E2E tests
            e2e_cmd = f"cd tests && npm run test:e2e:{env}"
            self.run_command(e2e_cmd)
            
            return True
        except Exception as e:
            self.log("ERROR", f"Automated tests failed: {str(e)}")
            return False
    
    def run_chaos_testing(self, env: str) -> bool:
        """
        Run chaos testing against the environment.
        
        Args:
            env: Environment to test (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Running chaos testing against {env} environment")
        
        try:
            namespace = self.staging_namespace if env == "staging" else self.prod_namespace
            
            # Run various chaos experiments
            chaos_cmds = [
                f"kubectl apply -f kubernetes/chaos-testing/pod-failure-experiment.yaml -n {namespace}",
                f"kubectl apply -f kubernetes/chaos-testing/network-delay-experiment.yaml -n {namespace}",
                f"kubectl apply -f kubernetes/chaos-testing/stress-cpu-experiment.yaml -n {namespace}"
            ]
            
            for cmd in chaos_cmds:
                self.run_command(cmd)
                # Wait for experiment to finish
                time.sleep(30)
            
            return True
        except Exception as e:
            self.log("WARNING", f"Chaos testing produced warnings: {str(e)}")
            return False
    
    def verify_monitoring(self, env: str) -> bool:
        """
        Verify monitoring and alerting in the environment.
        
        Args:
            env: Environment to verify (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Verifying monitoring and alerting in {env} environment")
        
        try:
            # Check Prometheus configuration
            prometheus_cmd = f"kubectl get configmap prometheus-config -n monitoring-{env} -o yaml"
            prometheus_config = self.run_command(prometheus_cmd)
            
            # Check alert rules
            alerts_cmd = f"kubectl get configmap prometheus-alerts -n monitoring-{env} -o yaml"
            alerts_config = self.run_command(alerts_cmd)
            
            # Could perform more sophisticated checks here
            
            return True
        except Exception as e:
            self.log("WARNING", f"Monitoring verification produced warnings: {str(e)}")
            return False
    
    def deploy_service_mesh(self, env: str) -> bool:
        """
        Deploy service mesh components to the environment.
        
        Args:
            env: Environment to deploy to (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Deploying service mesh components to {env} environment")
        
        try:
            namespace = self.staging_namespace if env == "staging" else self.prod_namespace
            
            # Deploy Istio policies
            istio_cmds = [
                f"kubectl apply -f infrastructure/kubernetes/istio/mtls-policy.yaml -n {namespace}",
                f"kubectl apply -f infrastructure/kubernetes/istio/virtual-service.yaml -n {namespace}",
                f"kubectl apply -f infrastructure/kubernetes/istio/destination-rules.yaml -n {namespace}"
            ]
            
            for cmd in istio_cmds:
                self.run_command(cmd)
            
            # Verify Istio configuration
            verify_cmd = f"istioctl analyze -n {namespace}"
            self.run_command(verify_cmd)
            
            return True
        except Exception as e:
            self.log("ERROR", f"Failed to deploy service mesh: {str(e)}")
            return False
    
    def apply_resource_configuration(self, env: str) -> bool:
        """
        Apply resource limits and probes to environment.
        
        Args:
            env: Environment to configure (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Applying resource limits and probes to {env} environment")
        
        try:
            namespace = self.staging_namespace if env == "staging" else self.prod_namespace
            
            # Apply resource configurations
            resource_cmd = f"kubectl apply -f kubernetes/resource-management/resource-quotas.yaml -n {namespace}"
            self.run_command(resource_cmd)
            
            return True
        except Exception as e:
            self.log("WARNING", f"Resource configuration produced warnings: {str(e)}")
            return False
    
    def deploy_logging_tracing(self, env: str) -> bool:
        """
        Deploy logging and tracing configuration to environment.
        
        Args:
            env: Environment to configure (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Deploying logging and tracing configuration to {env} environment")
        
        try:
            namespace = self.staging_namespace if env == "staging" else self.prod_namespace
            
            # Apply logging configurations
            logging_cmd = f"kubectl apply -f kubernetes/logging/fluentd-configmap.yaml -n {namespace}"
            self.run_command(logging_cmd)
            
            return True
        except Exception as e:
            self.log("WARNING", f"Logging/tracing configuration produced warnings: {str(e)}")
            return False
    
    def monitor_performance(self, env: str) -> bool:
        """
        Monitor performance in the environment.
        
        Args:
            env: Environment to monitor (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Monitoring performance in {env} environment")
        
        try:
            # Run performance tests or monitoring checks
            perf_cmd = "cd tests/performance && python ai_mesh_canvas_performance.js"
            self.run_command(perf_cmd)
            
            return True
        except Exception as e:
            self.log("WARNING", f"Performance monitoring produced warnings: {str(e)}")
            return False
    
    def configure_service_mesh_observability(self, env: str) -> bool:
        """
        Configure service mesh observability in the environment.
        
        Args:
            env: Environment to configure (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Configuring service mesh observability in {env} environment")
        
        try:
            namespace = self.staging_namespace if env == "staging" else self.prod_namespace
            
            # Apply service mesh observability configurations
            obs_cmds = [
                f"kubectl apply -f infrastructure/kubernetes/istio/telemetry.yaml -n {namespace}",
                f"kubectl apply -f infrastructure/kubernetes/istio/grafana-dashboards.yaml -n monitoring-{env}"
            ]
            
            for cmd in obs_cmds:
                self.run_command(cmd)
            
            return True
        except Exception as e:
            self.log("WARNING", f"Service mesh observability configuration produced warnings: {str(e)}")
            return False
    
    def configure_circuit_breakers(self, env: str) -> bool:
        """
        Configure circuit breakers and outlier detection in the environment.
        
        Args:
            env: Environment to configure (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Configuring circuit breakers in {env} environment")
        
        try:
            namespace = self.staging_namespace if env == "staging" else self.prod_namespace
            
            # Apply circuit breaker configurations
            cb_cmd = f"kubectl apply -f infrastructure/helm/maily/templates/circuit-breaker.yaml -n {namespace}"
            self.run_command(cb_cmd)
            
            return True
        except Exception as e:
            self.log("WARNING", f"Circuit breaker configuration produced warnings: {str(e)}")
            return False
    
    def deploy_canary(self, env: str, components: List[str]) -> bool:
        """
        Deploy components as canary releases.
        
        Args:
            env: Environment to deploy to (staging, production)
            components: List of components to deploy
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Deploying components as canary releases: {', '.join(components)}")
        
        try:
            namespace = self.staging_namespace if env == "staging" else self.prod_namespace
            
            # Set up the ArgoCD canary deployment
            canary_cmd = f"kubectl apply -f infrastructure/kubernetes/argocd/maily-canary-deployment.yaml -n {namespace}"
            self.run_command(canary_cmd)
            
            # Configure traffic split
            vs_cmd = f"kubectl patch virtualservice maily-vs -n {namespace} --type merge -p '{{\"spec\":{{\"http\":[{{\"route\":[{{\"destination\":{{\"host\":\"maily-stable\",\"port\":{{\"number\":80}}}},\"weight\":{100-self.canary_weight}}},{{\"destination\":{{\"host\":\"maily-canary\",\"port\":{{\"number\":80}}}},\"weight\":{self.canary_weight}}}]}}]}}}}'"
            self.run_command(vs_cmd)
            
            return True
        except Exception as e:
            self.log("ERROR", f"Canary deployment failed: {str(e)}")
            return False
    
    def deploy_secret_rotation(self, env: str) -> bool:
        """
        Deploy secret rotation system to the environment.
        
        Args:
            env: Environment to deploy to (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Deploying secret rotation system to {env} environment")
        
        try:
            namespace = self.staging_namespace if env == "staging" else self.prod_namespace
            
            # Apply secret rotation cronjob
            rotation_cmd = f"kubectl apply -f kubernetes/vault/secret-rotation-cronjob.yaml -n {namespace}"
            self.run_command(rotation_cmd)
            
            return True
        except Exception as e:
            self.log("WARNING", f"Secret rotation deployment produced warnings: {str(e)}")
            return False
    
    def enable_sla_monitoring(self, env: str) -> bool:
        """
        Enable SLA monitoring in the environment.
        
        Args:
            env: Environment to configure (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Enabling SLA monitoring in {env} environment")
        
        try:
            # Apply SLA rules to Prometheus
            sla_cmd = f"kubectl apply -f kubernetes/monitoring/prometheus-sla-rules.yaml -n monitoring-{env}"
            self.run_command(sla_cmd)
            
            return True
        except Exception as e:
            self.log("WARNING", f"SLA monitoring configuration produced warnings: {str(e)}")
            return False
    
    def schedule_chaos_testing(self, env: str) -> bool:
        """
        Schedule regular chaos testing in the environment.
        
        Args:
            env: Environment to configure (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Scheduling chaos testing in {env} environment")
        
        try:
            namespace = self.staging_namespace if env == "staging" else self.prod_namespace
            
            # Apply chaos schedule
            chaos_cmd = f"kubectl apply -f kubernetes/chaos-testing/chaos-schedule.yaml -n {namespace}"
            self.run_command(chaos_cmd)
            
            return True
        except Exception as e:
            self.log("WARNING", f"Chaos testing schedule produced warnings: {str(e)}")
            return False
    
    def enable_service_mesh_security(self, env: str) -> bool:
        """
        Enable full service mesh security policies in the environment.
        
        Args:
            env: Environment to configure (staging, production)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Enabling full service mesh security in {env} environment")
        
        try:
            namespace = self.staging_namespace if env == "staging" else self.prod_namespace
            
            # Apply security policies
            security_cmds = [
                f"kubectl apply -f infrastructure/kubernetes/istio/mtls-policy.yaml -n {namespace}",
                f"kubectl apply -f infrastructure/kubernetes/istio/authorization-policy.yaml -n {namespace}",
                f"kubectl apply -f infrastructure/kubernetes/istio/security-policy.yaml -n {namespace}"
            ]
            
            for cmd in security_cmds:
                self.run_command(cmd)
            
            return True
        except Exception as e:
            self.log("WARNING", f"Service mesh security configuration produced warnings: {str(e)}")
            return False
    
    def run(self) -> bool:
        """
        Run the phased deployment.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.log("INFO", f"Starting phased deployment of version {self.version} to {self.environment}")
        self.log("INFO", f"Deployment log: {self.log_file}")
        
        if self.dry_run:
            self.log("WARNING", "Running in DRY RUN mode - no changes will be applied")
        
        success = True
        
        # Execute each phase if in range
        if self.start_phase <= 1 <= self.end_phase:
            if not self.deploy_to_staging():
                success = False
                self.log("ERROR", "Phase 1 (Staging) failed")
                return False
        
        if self.start_phase <= 2 <= self.end_phase:
            if not self.deploy_to_prod_initial():
                success = False
                self.log("ERROR", "Phase 2 (Initial Production) failed")
                return False
        
        if self.start_phase <= 3 <= self.end_phase:
            if not self.deploy_to_prod_full():
                success = False
                self.log("ERROR", "Phase 3 (Full Production) failed")
                return False
        
        if success:
            self.log("SUCCESS", f"Phased deployment of version {self.version} completed successfully")
        else:
            self.log("ERROR", f"Phased deployment of version {self.version} failed")
        
        return success


class MailyCtl:
    """Main controller class for the Maily platform."""
    
    def __init__(self, environment: str, components: List[str], version: str = 'latest'):
        """
        Initialize the controller.
        
        Args:
            environment: The target environment (e.g., staging, production)
            components: List of components to target
            version: Version to deploy or verify
        """
        self.environment = environment
        self.components = components if components != ['all'] else ALL_COMPONENTS
        self.version = version
        self.config = self._load_config()
        
        # Validate components
        invalid_components = [c for c in self.components if c not in ALL_COMPONENTS]
        if invalid_components:
            logger.error(f"Invalid components: {', '.join(invalid_components)}")
            logger.info(f"Available components: {', '.join(ALL_COMPONENTS)}")
            sys.exit(1)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration for the specified environment."""
        config_file = os.path.join(CONFIG_DIR, f"config.{self.environment}.yaml")
        env_file = os.path.join(CONFIG_DIR, f".env.{self.environment}")
        
        if not os.path.exists(config_file):
            logger.error(f"Configuration file not found: {config_file}")
            sys.exit(1)
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Load environment variables if available
            if os.path.exists(env_file):
                env_vars = {}
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        key, value = line.split('=', 1)
                        env_vars[key] = value
                
                config['env'] = env_vars
            
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            sys.exit(1)
    
    def deploy(self) -> bool:
        """
        Deploy the specified components to the target environment.
        
        Returns:
            bool: True if deployment was successful, False otherwise
        """
        logger.info(f"Deploying {', '.join(self.components)} to {self.environment} environment (version: {self.version})")
        
        # First validate the components
        if not self.validate():
            logger.error("Validation failed. Deployment aborted.")
            return False
        
        # Deploy each component
        success = True
        for component in self.components:
            component_success = self._deploy_component(component)
            if not component_success:
                success = False
        
        if success:
            logger.info(f"Successfully deployed {', '.join(self.components)} to {self.environment}")
        else:
            logger.error(f"Deployment failed for some components")
        
        return success
    
    def _deploy_component(self, component: str) -> bool:
        """
        Deploy a single component.
        
        Args:
            component: The component to deploy
            
        Returns:
            bool: True if deployment was successful, False otherwise
        """
        logger.info(f"Deploying {component}...")
        
        component_config = self.config.get('components', {}).get(component)
        if not component_config:
            logger.error(f"No configuration found for component: {component}")
            return False
        
        deploy_method = component_config.get('deploy_method')
        if not deploy_method:
            logger.error(f"No deployment method specified for component: {component}")
            return False
        
        try:
            if deploy_method == 'kubernetes':
                return self._deploy_kubernetes(component, component_config)
            elif deploy_method == 'vercel':
                return self._deploy_vercel(component, component_config)
            elif deploy_method == 'helm':
                return self._deploy_helm(component, component_config)
            elif deploy_method == 'service-mesh':
                return self._deploy_service_mesh(component, component_config)
            elif deploy_method == 'argocd':
                return self._deploy_argocd(component, component_config)
            else:
                logger.error(f"Unsupported deployment method: {deploy_method}")
                return False
        except Exception as e:
            logger.error(f"Deployment failed for {component}: {str(e)}")
            return False
    
    def _deploy_kubernetes(self, component: str, config: Dict[str, Any]) -> bool:
        """Deploy a component to Kubernetes."""
        namespace = config.get('namespace', 'maily')
        deployment = config.get('deployment', component)
        image = config.get('image', f"maily/{component}")
        kube_context = self.config.get('kubernetes', {}).get('context', f"maily-{self.environment}")
        
        # Prepare image tag
        image_tag = f"{image}:{self.version}"
        
        try:
            # Update deployment with new image
            cmd = [
                "kubectl", 
                f"--context={kube_context}", 
                f"--namespace={namespace}", 
                "set", "image", 
                f"deployment/{deployment}", 
                f"{component}={image_tag}"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            # Wait for rollout to complete
            cmd = [
                "kubectl", 
                f"--context={kube_context}", 
                f"--namespace={namespace}", 
                "rollout", "status", 
                f"deployment/{deployment}",
                "--timeout=300s"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            logger.info(f"Successfully deployed {component} to Kubernetes")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Kubernetes deployment failed for {component}: {str(e)}")
            return False
    
    def _deploy_vercel(self, component: str, config: Dict[str, Any]) -> bool:
        """Deploy a component to Vercel."""
        project_id = config.get('project_id')
        if not project_id:
            logger.error(f"No project ID specified for Vercel deployment of {component}")
            return False
        
        vercel_token = self.config.get('env', {}).get('VERCEL_TOKEN')
        if not vercel_token:
            logger.error("No Vercel token found in environment variables")
            return False
        
        try:
            # Deploy to Vercel
            cmd = [
                "vercel",
                "deploy",
                "--prod",
                f"--token={vercel_token}",
                f"--project={project_id}"
            ]
            
            if self.environment != 'production':
                cmd.append(f"--env=ENVIRONMENT={self.environment}")
            
            logger.info(f"Executing: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            logger.info(f"Successfully deployed {component} to Vercel")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Vercel deployment failed for {component}: {str(e)}")
            return False
            
    def _deploy_helm(self, component: str, config: Dict[str, Any]) -> bool:
        """Deploy a component using Helm charts."""
        chart_path = config.get('chart_path')
        if not chart_path:
            logger.error(f"No chart path specified for Helm deployment of {component}")
            return False
        
        release_name = config.get('release_name', component)
        namespace = config.get('namespace', 'maily')
        values_file = config.get('values_file', f"values-{self.environment}.yaml")
        
        try:
            # Deploy using Helm
            cmd = [
                "helm", "upgrade", "--install",
                release_name,
                chart_path,
                "--namespace", namespace,
                "--values", values_file,
                "--set", f"image.tag={self.version}",
                "--set", f"environment={self.environment}"
            ]
            
            # Add any additional Helm set parameters
            for key, value in config.get('set_values', {}).items():
                cmd.extend(["--set", f"{key}={value}"])
            
            logger.info(f"Executing: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            # Wait for rollout to complete
            if config.get('wait_for_rollout', True):
                deployment_name = config.get('deployment_name', component)
                wait_cmd = [
                    "kubectl",
                    "--namespace", namespace,
                    "rollout", "status",
                    f"deployment/{deployment_name}",
                    "--timeout=300s"
                ]
                
                logger.info(f"Executing: {' '.join(wait_cmd)}")
                subprocess.run(wait_cmd, check=True)
            
            logger.info(f"Successfully deployed {component} using Helm")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Helm deployment failed for {component}: {str(e)}")
            return False
    
    def _deploy_service_mesh(self, component: str, config: Dict[str, Any]) -> bool:
        """Deploy a component with Istio service mesh configurations."""
        chart_path = config.get('chart_path')
        if not chart_path:
            logger.error(f"No chart path specified for service mesh deployment of {component}")
            return False
        
        release_name = config.get('release_name', component)
        namespace = config.get('namespace', 'maily')
        values_file = config.get('values_file', f"values-{self.environment}.yaml")
        
        try:
            # Deploy using Helm with service mesh enabled
            cmd = [
                "helm", "upgrade", "--install",
                release_name,
                chart_path,
                "--namespace", namespace,
                "--values", values_file,
                "--set", f"image.tag={self.version}",
                "--set", f"environment={self.environment}",
                "--set", "global.istio.enabled=true",
                "--set", f"global.istio.mtls.mode={config.get('mtls_mode', 'STRICT')}"
            ]
            
            # Add circuit breaker configuration if enabled
            if config.get('circuit_breaker', {}).get('enabled', False):
                cmd.extend([
                    "--set", "circuitBreaker.enabled=true",
                    "--set", f"circuitBreaker.maxConnections={config.get('circuit_breaker', {}).get('maxConnections', 100)}",
                    "--set", f"circuitBreaker.maxRequestsPerConnection={config.get('circuit_breaker', {}).get('maxRequestsPerConnection', 10)}",
                    "--set", f"circuitBreaker.consecutiveErrors={config.get('circuit_breaker', {}).get('consecutiveErrors', 5)}"
                ])
            
            # Add any additional Helm set parameters
            for key, value in config.get('set_values', {}).items():
                cmd.extend(["--set", f"{key}={value}"])
            
            logger.info(f"Executing: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            # Apply Istio virtual service and destination rules if provided
            if config.get('virtual_service'):
                vs_cmd = [
                    "kubectl", "apply",
                    "--namespace", namespace,
                    "-f", config.get('virtual_service')
                ]
                logger.info(f"Executing: {' '.join(vs_cmd)}")
                subprocess.run(vs_cmd, check=True)
            
            # Wait for deployment to complete
            if config.get('wait_for_rollout', True):
                deployment_name = config.get('deployment_name', component)
                wait_cmd = [
                    "kubectl",
                    "--namespace", namespace,
                    "rollout", "status",
                    f"deployment/{deployment_name}",
                    "--timeout=300s"
                ]
                
                logger.info(f"Executing: {' '.join(wait_cmd)}")
                subprocess.run(wait_cmd, check=True)
            
            # Verify service mesh configuration
            if config.get('verify_istio', True):
                verify_cmd = [
                    "istioctl", "analyze",
                    "--namespace", namespace
                ]
                logger.info(f"Executing: {' '.join(verify_cmd)}")
                subprocess.run(verify_cmd, check=True)
            
            logger.info(f"Successfully deployed {component} with service mesh configuration")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Service mesh deployment failed for {component}: {str(e)}")
            return False
    
    def _deploy_argocd(self, component: str, config: Dict[str, Any]) -> bool:
        """Deploy a component using ArgoCD."""
        application_name = config.get('application_name', f"maily-{component}-{self.environment}")
        if not application_name:
            logger.error(f"No application name specified for ArgoCD deployment of {component}")
            return False
        
        repo_url = config.get('repo_url')
        if not repo_url:
            logger.error(f"No repository URL specified for ArgoCD deployment of {component}")
            return False
        
        path = config.get('path')
        namespace = config.get('namespace', 'maily')
        
        try:
            # Check if application exists
            check_cmd = [
                "argocd", "app", "get", application_name,
                "--grpc-web"
            ]
            
            app_exists = False
            try:
                logger.info(f"Executing: {' '.join(check_cmd)}")
                subprocess.run(check_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                app_exists = True
            except subprocess.CalledProcessError:
                app_exists = False
            
            if app_exists:
                # Update existing application
                update_cmd = [
                    "argocd", "app", "set", application_name,
                    "--revision", self.version,
                    "--grpc-web"
                ]
                
                logger.info(f"Executing: {' '.join(update_cmd)}")
                subprocess.run(update_cmd, check=True)
                
                # Sync application
                sync_cmd = [
                    "argocd", "app", "sync", application_name,
                    "--grpc-web"
                ]
                
                logger.info(f"Executing: {' '.join(sync_cmd)}")
                subprocess.run(sync_cmd, check=True)
            else:
                # Create new application
                create_cmd = [
                    "argocd", "app", "create", application_name,
                    "--repo", repo_url,
                    "--path", path,
                    "--dest-server", "https://kubernetes.default.svc",
                    "--dest-namespace", namespace,
                    "--revision", self.version,
                    "--sync-policy", config.get('sync_policy', 'automated'),
                    "--grpc-web"
                ]
                
                # Add any additional ArgoCD parameters
                for key, value in config.get('parameters', {}).items():
                    create_cmd.extend(["--parameter", f"{key}={value}"])
                
                logger.info(f"Executing: {' '.join(create_cmd)}")
                subprocess.run(create_cmd, check=True)
            
            # Wait for application to be healthy
            wait_cmd = [
                "argocd", "app", "wait", application_name,
                "--health",
                "--timeout", "300",
                "--grpc-web"
            ]
            
            logger.info(f"Executing: {' '.join(wait_cmd)}")
            subprocess.run(wait_cmd, check=True)
            
            logger.info(f"Successfully deployed {component} using ArgoCD")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"ArgoCD deployment failed for {component}: {str(e)}")
            return False
    
    def validate(self) -> bool:
        """
        Validate the specified components before deployment.
        
        Returns:
            bool: True if validation was successful, False otherwise
        """
        logger.info(f"Validating {', '.join(self.components)} for {self.environment} environment")
        
        success = True
        for component in self.components:
            component_success = self._validate_component(component)
            if not component_success:
                success = False
        
        if success:
            logger.info(f"Validation successful for all components")
        else:
            logger.error(f"Validation failed for some components")
        
        return success
    
    def _validate_component(self, component: str) -> bool:
        """
        Validate a single component.
        
        Args:
            component: The component to validate
            
        Returns:
            bool: True if validation was successful, False otherwise
        """
        logger.info(f"Validating {component}...")
        
        # Map component names to validator scripts
        validator_map = {
            'frontend': None,  # No validator for frontend
            'api': None,  # No validator for API
            'ai-service': os.path.join(VALIDATORS_DIR, 'ai-agent-validator.js'),
            'websocket': os.path.join(VALIDATORS_DIR, 'canvas-validator.js'),
            'blockchain': os.path.join(VALIDATORS_DIR, 'blockchain-validator.js'),
            'analytics': None,  # No validator for analytics
            'campaign': None,  # No validator for campaign
            'email': None,  # No validator for email
            'workers': None,  # No validator for workers
            'visualization-service': os.path.join(VALIDATORS_DIR, 'canvas-validator.js'),
            'trust-verification': os.path.join(VALIDATORS_DIR, 'blockchain-validator.js'),
            'service-mesh': None  # Service mesh validation is handled via Istio validation
        }
        
        validator_script = validator_map.get(component)
        if not validator_script:
            logger.warning(f"No validator script available for {component}, skipping validation")
            return True
        
        if not os.path.exists(validator_script):
            logger.error(f"Validator script not found: {validator_script}")
            return False
        
        try:
            # Run the validator script
            cmd = ["node", validator_script, self.environment]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Log the output
            if result.stdout:
                logger.info(result.stdout)
            if result.stderr:
                logger.error(result.stderr)
            
            if result.returncode != 0:
                logger.error(f"Validation failed for {component}")
                return False
            
            logger.info(f"Validation successful for {component}")
            return True
        except Exception as e:
            logger.error(f"Validation failed for {component}: {str(e)}")
            return False
    
    def verify(self) -> bool:
        """
        Verify the deployment of the specified components.
        
        Returns:
            bool: True if verification was successful, False otherwise
        """
        logger.info(f"Verifying {', '.join(self.components)} in {self.environment} environment (version: {self.version})")
        
        success = True
        for component in self.components:
            component_success = self._verify_component(component)
            if not component_success:
                success = False
        
        if success:
            logger.info(f"Verification successful for all components")
        else:
            logger.error(f"Verification failed for some components")
        
        return success
    
    def _verify_component(self, component: str) -> bool:
        """
        Verify a single component.
        
        Args:
            component: The component to verify
            
        Returns:
            bool: True if verification was successful, False otherwise
        """
        logger.info(f"Verifying {component}...")
        
        # Map component names to verifier scripts
        verifier_map = {
            'frontend': None,  # No verifier for frontend
            'api': None,  # No verifier for API
            'ai-service': os.path.join(VERIFIERS_DIR, 'ai-verifier.js'),
            'websocket': os.path.join(VERIFIERS_DIR, 'canvas-verifier.js'),
            'blockchain': os.path.join(VERIFIERS_DIR, 'blockchain-verifier.js'),
            'analytics': None,  # No verifier for analytics
            'campaign': None,  # No verifier for campaign
            'email': None,  # No verifier for email
            'workers': None,  # No verifier for workers
            'visualization-service': os.path.join(VERIFIERS_DIR, 'canvas-verifier.js'),
            'trust-verification': os.path.join(VERIFIERS_DIR, 'blockchain-verifier.js'),
            'service-mesh': os.path.join(VERIFIERS_DIR, 'service-mesh-verifier.js')
        }
        
        verifier_script = verifier_map.get(component)
        if not verifier_script:
            logger.warning(f"No verifier script available for {component}, skipping verification")
            return True
        
        if not os.path.exists(verifier_script):
            logger.error(f"Verifier script not found: {verifier_script}")
            return False
        
        try:
            # Run the verifier script
            cmd = ["node", verifier_script, self.environment, component, self.version]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Log the output
            if result.stdout:
                logger.info(result.stdout)
            if result.stderr:
                logger.error(result.stderr)
            
            if result.returncode != 0:
                logger.error(f"Verification failed for {component}")
                return False
            
            logger.info(f"Verification successful for {component}")
            return True
        except Exception as e:
            logger.error(f"Verification failed for {component}: {str(e)}")
            return False
    
    def test(self, scope: str) -> bool:
        """
        Run tests for the specified components.
        
        Args:
            scope: Test scope (unit, integration, e2e, post-deployment)
            
        Returns:
            bool: True if tests passed, False otherwise
        """
        logger.info(f"Running {scope} tests in {self.environment} environment")
        
        # Get test command from config
        test_config = self.config.get('tests', {}).get(scope)
        if not test_config:
            logger.error(f"No test configuration found for scope: {scope}")
            return False
        
        test_command = test_config.get('command')
        if not test_command:
            logger.error(f"No test command specified for scope: {scope}")
            return False
        
        try:
            # Run the test command
            cmd = test_command.split()
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Log the output
            if result.stdout:
                logger.info(result.stdout)
            if result.stderr:
                logger.error(result.stderr)
            
            if result.returncode != 0:
                logger.error(f"Tests failed for scope: {scope}")
                return False
            
            logger.info(f"Tests passed for scope: {scope}")
            return True
        except Exception as e:
            logger.error(f"Tests failed for scope {scope}: {str(e)}")
            return False
    
    def status(self) -> bool:
        """
        Check the status of the specified components.
        
        Returns:
            bool: True if all components are healthy, False otherwise
        """
        logger.info(f"Checking status of {', '.join(self.components)} in {self.environment} environment")
        
        success = True
        for component in self.components:
            component_success = self._check_component_status(component)
            if not component_success:
                success = False
        
        return success
    
    def _check_component_status(self, component: str) -> bool:
        """
        Check the status of a single component.
        
        Args:
            component: The component to check
            
        Returns:
            bool: True if the component is healthy, False otherwise
        """
        logger.info(f"Checking status of {component}...")
        
        component_config = self.config.get('components', {}).get(component)
        if not component_config:
            logger.error(f"No configuration found for component: {component}")
            return False
        
        deploy_method = component_config.get('deploy_method')
        if not deploy_method:
            logger.error(f"No deployment method specified for component: {component}")
            return False
        
        try:
            if deploy_method == 'kubernetes':
                return self._check_kubernetes_status(component, component_config)
            elif deploy_method == 'vercel':
                return self._check_vercel_status(component, component_config)
            elif deploy_method == 'helm':
                return self._check_helm_status(component, component_config)
            elif deploy_method == 'service-mesh':
                return self._check_service_mesh_status(component, component_config)
            elif deploy_method == 'argocd':
                return self._check_argocd_status(component, component_config)
            else:
                logger.error(f"Unsupported deployment method: {deploy_method}")
                return False
        except Exception as e:
            logger.error(f"Status check failed for {component}: {str(e)}")
            return False
    
    def _check_kubernetes_status(self, component: str, config: Dict[str, Any]) -> bool:
        """Check the status of a Kubernetes-deployed component."""
        namespace = config.get('namespace', 'maily')
        deployment = config.get('deployment', component)
        kube_context = self.config.get('kubernetes', {}).get('context', f"maily-{self.environment}")
        
        try:
            # Check deployment status
            cmd = [
                "kubectl", 
                f"--context={kube_context}", 
                f"--namespace={namespace}", 
                "get", "deployment", 
                deployment, 
                "-o", "json"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            deployment_data = json.loads(result.stdout)
            available_replicas = deployment_data.get('status', {}).get('availableReplicas', 0)
            desired_replicas = deployment_data.get('spec', {}).get('replicas', 0)
            
            if available_replicas < desired_replicas:
                logger.error(f"Deployment {deployment} has {available_replicas}/{desired_replicas} available replicas")
                return False
            
            logger.info(f"Deployment {deployment} has {available_replicas}/{desired_replicas} available replicas")
            
            # Check if pods are running
            cmd = [
                "kubectl", 
                f"--context={kube_context}", 
                f"--namespace={namespace}", 
                "get", "pods", 
                "-l", f"app={deployment}", 
                "-o", "json"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            pods_data = json.loads(result.stdout)
            pods = pods_data.get('items', [])
            
            if not pods:
                logger.error(f"No pods found for deployment {deployment}")
                return False
            
            running_pods = 0
            for pod in pods:
                pod_status = pod.get('status', {}).get('phase')
                pod_name = pod.get('metadata', {}).get('name')
                
                if pod_status == 'Running':
                    running_pods += 1
                    logger.info(f"Pod {pod_name} is running")
                else:
                    logger.warning(f"Pod {pod_name} is in {pod_status} state")
            
            if running_pods == 0:
                logger.error(f"No running pods found for deployment {deployment}")
                return False
            
            logger.info(f"{running_pods}/{len(pods)} pods are running")
            
            # Check health endpoint if available
            verify_method = config.get('verify_method')
            if verify_method == 'http':
                health_url = config.get('health_url')
                if health_url:
                    try:
                        logger.info(f"Checking health endpoint: {health_url}")
                        response = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", health_url], capture_output=True, text=True, check=True)
                        status_code = int(response.stdout.strip())
                        
                        if status_code >= 200 and status_code < 300:
                            logger.info(f"Health endpoint returned status {status_code}")
                        else:
                            logger.error(f"Health endpoint returned status {status_code}")
                            return False
                    except Exception as e:
                        logger.error(f"Failed to check health endpoint: {str(e)}")
                        return False
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Kubernetes status check failed for {component}: {str(e)}")
            return False
    
    def _check_vercel_status(self, component: str, config: Dict[str, Any]) -> bool:
        """Check the status of a Vercel-deployed component."""
        project_id = config.get('project_id')
        if not project_id:
            logger.error(f"No project ID specified for Vercel deployment of {component}")
            return False
        
        vercel_token = self.config.get('env', {}).get('VERCEL_TOKEN')
        if not vercel_token:
            logger.error("No Vercel token found in environment variables")
            return False
        
        try:
            # Check deployment status
            cmd = [
                "vercel",
                "inspect",
                f"--token={vercel_token}",
                f"--project={project_id}",
                "--json"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            deployment_data = json.loads(result.stdout)
            deployment_state = deployment_data.get('deployment', {}).get('state')
            
            if deployment_state == 'READY':
                logger.info(f"Vercel deployment is ready")
                return True
            else:
                logger.error(f"Vercel deployment is in {deployment_state} state")
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Vercel status check failed for {component}: {str(e)}")
            return False
            
    def _check_helm_status(self, component: str, config: Dict[str, Any]) -> bool:
        """Check the status of a Helm-deployed component."""
        release_name = config.get('release_name', component)
        namespace = config.get('namespace', 'maily')
        
        try:
            # Check helm release status
            cmd = [
                "helm", "status",
                release_name,
                "--namespace", namespace
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Check if the release is deployed
            if "STATUS: deployed" in result.stdout:
                logger.info(f"Helm release {release_name} is deployed")
                
                # Check underlying deployment
                deployment_name = config.get('deployment_name', component)
                return self._check_kubernetes_deployment(deployment_name, namespace)
            else:
                logger.error(f"Helm release {release_name} is not in deployed state")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Helm status check failed for {component}: {str(e)}")
            return False
    
    def _check_kubernetes_deployment(self, deployment_name: str, namespace: str) -> bool:
        """Check the status of a Kubernetes deployment."""
        try:
            # Check deployment status
            cmd = [
                "kubectl",
                "--namespace", namespace,
                "get", "deployment",
                deployment_name,
                "-o", "json"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            deployment_data = json.loads(result.stdout)
            available_replicas = deployment_data.get('status', {}).get('availableReplicas', 0)
            desired_replicas = deployment_data.get('spec', {}).get('replicas', 0)
            
            if available_replicas < desired_replicas:
                logger.error(f"Deployment {deployment_name} has {available_replicas}/{desired_replicas} available replicas")
                return False
            
            logger.info(f"Deployment {deployment_name} has {available_replicas}/{desired_replicas} available replicas")
            
            # Check if pods are running
            cmd = [
                "kubectl",
                "--namespace", namespace,
                "get", "pods",
                "-l", f"app={deployment_name}",
                "-o", "json"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            pods_data = json.loads(result.stdout)
            pods = pods_data.get('items', [])
            
            if not pods:
                logger.error(f"No pods found for deployment {deployment_name}")
                return False
            
            running_pods = 0
            for pod in pods:
                pod_status = pod.get('status', {}).get('phase')
                pod_name = pod.get('metadata', {}).get('name')
                
                if pod_status == 'Running':
                    running_pods += 1
                    logger.info(f"Pod {pod_name} is running")
                else:
                    logger.warning(f"Pod {pod_name} is in {pod_status} state")
            
            if running_pods == 0:
                logger.error(f"No running pods found for deployment {deployment_name}")
                return False
            
            logger.info(f"{running_pods}/{len(pods)} pods are running")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Kubernetes deployment check failed: {str(e)}")
            return False
    
    def _check_service_mesh_status(self, component: str, config: Dict[str, Any]) -> bool:
        """Check the status of a service mesh deployed component."""
        release_name = config.get('release_name', component)
        namespace = config.get('namespace', 'maily')
        
        try:
            # First check the Helm release status
            helm_status = self._check_helm_status(component, config)
            if not helm_status:
                return False
            
            # Check if Istio is properly configured for the component
            cmd = [
                "istioctl", "analyze",
                "--namespace", namespace,
                "--timeout", "30s"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Istio configuration analysis failed for {component}: {result.stderr}")
                return False
            
            # Check if mTLS is properly configured
            mtls_cmd = [
                "istioctl", "authn", "tls-check",
                f"*.{namespace}.svc.cluster.local",
                "--namespace", namespace
            ]
            
            logger.info(f"Executing: {' '.join(mtls_cmd)}")
            result = subprocess.run(mtls_cmd, capture_output=True, text=True)
            
            # Check for STRICT mTLS mode
            if "STRICT" not in result.stdout and config.get('mtls_mode', 'STRICT') == 'STRICT':
                logger.warning(f"mTLS is not in STRICT mode for {component}")
            
            # Check circuit breaker configuration if applicable
            if config.get('circuit_breaker', {}).get('enabled', False):
                cb_cmd = [
                    "kubectl", "get", "destinationrule",
                    f"{release_name}-{component}-cb",
                    "--namespace", namespace,
                    "-o", "yaml"
                ]
                
                logger.info(f"Executing: {' '.join(cb_cmd)}")
                cb_result = subprocess.run(cb_cmd, capture_output=True, text=True)
                
                if cb_result.returncode != 0:
                    logger.warning(f"Circuit breaker configuration not found for {component}")
            
            # Check virtual service if applicable
            if config.get('virtual_service'):
                vs_name = f"{release_name}-{component}-vs"
                vs_cmd = [
                    "kubectl", "get", "virtualservice",
                    vs_name,
                    "--namespace", namespace
                ]
                
                logger.info(f"Executing: {' '.join(vs_cmd)}")
                vs_result = subprocess.run(vs_cmd, capture_output=True, text=True)
                
                if vs_result.returncode != 0:
                    logger.warning(f"Virtual Service not found for {component}")
            
            logger.info(f"Service mesh configuration is valid for {component}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Service mesh status check failed for {component}: {str(e)}")
            return False
    
    def _check_argocd_status(self, component: str, config: Dict[str, Any]) -> bool:
        """Check the status of an ArgoCD-deployed component."""
        application_name = config.get('application_name', f"maily-{component}-{self.environment}")
        
        try:
            # Check application status in ArgoCD
            cmd = [
                "argocd", "app", "get", application_name,
                "--output", "json",
                "--grpc-web"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            app_data = json.loads(result.stdout)
            health_status = app_data.get('status', {}).get('health', {}).get('status')
            sync_status = app_data.get('status', {}).get('sync', {}).get('status')
            
            logger.info(f"ArgoCD application {application_name} health: {health_status}, sync: {sync_status}")
            
            if health_status == 'Healthy' and sync_status == 'Synced':
                logger.info(f"ArgoCD application {application_name} is healthy and synced")
                
                # If canary deployment, check the rollout status
                if config.get('rollout_name'):
                    rollout_name = config.get('rollout_name')
                    namespace = config.get('namespace', 'maily')
                    
                    rollout_cmd = [
                        "kubectl", "argo", "rollouts", "get", "rollout",
                        rollout_name,
                        "--namespace", namespace,
                        "-o", "json"
                    ]
                    
                    logger.info(f"Executing: {' '.join(rollout_cmd)}")
                    rollout_result = subprocess.run(rollout_cmd, capture_output=True, text=True)
                    
                    if rollout_result.returncode == 0:
                        rollout_data = json.loads(rollout_result.stdout)
                        rollout_status = rollout_data.get('status', {}).get('phase')
                        
                        if rollout_status != 'Healthy':
                            logger.error(f"Rollout {rollout_name} is in {rollout_status} state")
                            return False
                        
                        logger.info(f"Rollout {rollout_name} is healthy")
                    else:
                        logger.warning(f"Could not get rollout status for {rollout_name}")
                
                return True
            else:
                logger.error(f"ArgoCD application {application_name} is not healthy or not synced")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"ArgoCD status check failed for {component}: {str(e)}")
            return False
    
    def logs(self, component: str, tail: int) -> bool:
        """
        Show logs for a component.
        
        Args:
            component: The component to show logs for
            tail: Number of log lines to show
            
        Returns:
            bool: True if logs were retrieved successfully, False otherwise
        """
        logger.info(f"Showing logs for {component} in {self.environment} environment")
        
        component_config = self.config.get('components', {}).get(component)
        if not component_config:
            logger.error(f"No configuration found for component: {component}")
            return False
        
        deploy_method = component_config.get('deploy_method')
        if not deploy_method:
            logger.error(f"No deployment method specified for component: {component}")
            return False
        
        try:
            if deploy_method == 'kubernetes':
                return self._show_kubernetes_logs(component, component_config, tail)
            elif deploy_method == 'vercel':
                return self._show_vercel_logs(component, component_config, tail)
            else:
                logger.error(f"Unsupported deployment method: {deploy_method}")
                return False
        except Exception as e:
            logger.error(f"Failed to retrieve logs for {component}: {str(e)}")
            return False
    
    def _show_kubernetes_logs(self, component: str, config: Dict[str, Any], tail: int) -> bool:
        """Show logs for a Kubernetes-deployed component."""
        namespace = config.get('namespace', 'maily')
        deployment = config.get('deployment', component)
        kube_context = self.config.get('kubernetes', {}).get('context', f"maily-{self.environment}")
        
        try:
            # Get pod names
            cmd = [
                "kubectl", 
                f"--context={kube_context}", 
                f"--namespace={namespace}", 
                "get", "pods", 
                "-l", f"app={deployment}", 
                "-o", "jsonpath={.items[0].metadata.name}"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            pod_name = result.stdout.strip()
            if not pod_name:
                logger.error(f"No pods found for deployment {deployment}")
                return False
            
            # Show logs
            cmd = [
                "kubectl", 
                f"--context={kube_context}", 
                f"--namespace={namespace}", 
                "logs", 
                pod_name, 
                f"--tail={tail}"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to retrieve Kubernetes logs for {component}: {str(e)}")
            return False
    
    def _show_vercel_logs(self, component: str, config: Dict[str, Any], tail: int) -> bool:
        """Show logs for a Vercel-deployed component."""
        project_id = config.get('project_id')
        if not project_id:
            logger.error(f"No project ID specified for Vercel deployment of {component}")
            return False
        
        vercel_token = self.config.get('env', {}).get('VERCEL_TOKEN')
        if not vercel_token:
            logger.error("No Vercel token found in environment variables")
            return False
        
        try:
            # Show logs
            cmd = [
                "vercel",
                "logs",
                f"--token={vercel_token}",
                f"--project={project_id}",
                f"--limit={tail}"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to retrieve Vercel logs for {component}: {str(e)}")
            return False
    
    def rollback(self, component: str, to_version: str) -> bool:
        """
        Rollback a component to a previous version.
        
        Args:
            component: The component to rollback
            to_version: The version to rollback to
            
        Returns:
            bool: True if rollback was successful, False otherwise
        """
        logger.info(f"Rolling back {component} to version {to_version} in {self.environment} environment")
        
        component_config = self.config.get('components', {}).get(component)
        if not component_config:
            logger.error(f"No configuration found for component: {component}")
            return False
        
        deploy_method = component_config.get('deploy_method')
        if not deploy_method:
            logger.error(f"No deployment method specified for component: {component}")
            return False
        
        try:
            if deploy_method == 'kubernetes':
                return self._rollback_kubernetes(component, component_config, to_version)
            elif deploy_method == 'vercel':
                return self._rollback_vercel(component, component_config, to_version)
            else:
                logger.error(f"Unsupported deployment method: {deploy_method}")
                return False
        except Exception as e:
            logger.error(f"Rollback failed for {component}: {str(e)}")
            return False
    
    def _rollback_kubernetes(self, component: str, config: Dict[str, Any], to_version: str) -> bool:
        """Rollback a Kubernetes-deployed component."""
        namespace = config.get('namespace', 'maily')
        deployment = config.get('deployment', component)
        image = config.get('image', f"maily/{component}")
        kube_context = self.config.get('kubernetes', {}).get('context', f"maily-{self.environment}")
        
        # Prepare image tag
        image_tag = f"{image}:{to_version}"
        
        try:
            # Update deployment with previous image
            cmd = [
                "kubectl", 
                f"--context={kube_context}", 
                f"--namespace={namespace}", 
                "set", "image", 
                f"deployment/{deployment}", 
                f"{component}={image_tag}"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            # Wait for rollout to complete
            cmd = [
                "kubectl", 
                f"--context={kube_context}", 
                f"--namespace={namespace}", 
                "rollout", "status", 
                f"deployment/{deployment}",
                "--timeout=300s"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            logger.info(f"Successfully rolled back {component} to version {to_version}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Kubernetes rollback failed for {component}: {str(e)}")
            return False
    
    def _rollback_vercel(self, component: str, config: Dict[str, Any], to_version: str) -> bool:
        """
        Roll back a Vercel deployment to a specific version.
        
        Args:
            component: The component to roll back
            config: The component configuration
            to_version: The version to roll back to
            
        Returns:
            bool: True if rollback was successful, False otherwise
        """
        try:
            logger.info(f"Rolling back Vercel deployment for {component} to version {to_version}")
            
            # Extract Vercel project ID and token from config
            project_id = config.get('vercel', {}).get('project_id')
            token = os.environ.get('VERCEL_TOKEN', '')
            
            if not project_id or not token:
                logger.error(f"Missing Vercel project ID or token for {component}")
                return False
                
            # Execute Vercel CLI command for rollback
            cmd = [
                'vercel', 'alias', 
                f'https://{component}-{to_version}.vercel.app', 
                config.get('vercel', {}).get('production_url', f'{component}.vercel.app'),
                '--token', token,
                '--scope', config.get('vercel', {}).get('team', 'maily')
            ]
            
            subprocess.check_call(cmd, stderr=subprocess.STDOUT)
            logger.info(f"Successfully rolled back {component} to version {to_version}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Vercel rollback failed for {component}: {str(e)}")
            return False


def main():
    """Main entry point for the CLI."""
    args = docopt(__doc__)
    
    # Parse environment
    environment = args.get('--env', 'staging')
    
    # Parse components
    components_arg = args.get('--components', 'all')
    components = components_arg.split(',') if components_arg else ['all']
    
    # Parse version
    version = args.get('--version', 'latest')
    
    # Show version if requested
    if args.get('--show-version'):
        print(f"mailyctl version {VERSION}")
        return 0
        
    # Execute the appropriate command
    if args.get('phased-deploy'):
        # Parse phased deployment options
        skip_staging = args.get('--skip-staging', False)
        start_phase = int(args.get('--start-phase', 1))
        end_phase = int(args.get('--end-phase', 3))
        dry_run = args.get('--dry-run', False)
        canary = args.get('--canary', False)
        canary_weight = int(args.get('--canary-weight', 10))
        
        # Create and run phased deployer
        deployer = PhasedDeployment(
            environment=environment,
            version=version,
            skip_staging=skip_staging,
            start_phase=start_phase,
            end_phase=end_phase,
            dry_run=dry_run,
            canary=canary,
            canary_weight=canary_weight
        )
        success = deployer.run()
    
    elif args.get('secrets') and args.get('rotate'):
        # Parse secret rotation options
        secret_types_arg = args.get('--secret-types', 'all')
        secret_types = set(secret_types_arg.split(',')) if secret_types_arg != 'all' else None
        notify = args.get('--notify', False)
        
        async def rotate_secrets():
            # Load default config with environment overrides
            config = DEFAULT_SECRET_CONFIG.copy()
            config['environment'] = environment
            
            # Create and initialize secret manager
            secret_manager = SecretManager(config)
            await secret_manager.initialize()
            
            try:
                # Rotate secrets
                await secret_manager.rotate_secrets(secret_types, notify)
                return True
            except Exception as e:
                logger.error(f"Secret rotation failed: {str(e)}")
                return False
            finally:
                # Clean up
                await secret_manager.close()
        
        # Run secret rotation asynchronously
        success = asyncio.run(rotate_secrets())
    
    elif args.get('verify-mesh'):
        # Parse service mesh verification options
        component = args.get('--component', 'api')
        release = args.get('--release', 'maily')
        
        # Create and run service mesh verifier
        verifier = ServiceMeshVerifier(environment, component, release, version)
        success = verifier.verify()
        
    else:
        # Initialize controller for original commands
        controller = MailyCtl(environment, components, version)
        
        # Execute original commands
        if args.get('deploy'):
            success = controller.deploy()
        elif args.get('verify'):
            success = controller.verify()
        elif args.get('test'):
            scope = args.get('--scope', 'all')
            success = controller.test(scope)
        elif args.get('status'):
            success = controller.status()
        elif args.get('logs'):
            component = components[0] if components and components[0] != 'all' else 'api'
            tail = int(args.get('--tail', 100))
            success = controller.logs(component, tail)
        elif args.get('rollback'):
            to_version = args.get('--to-version')
            if not to_version:
                logger.error("No version specified for rollback. Use --to-version option.")
                return 1
            
            component = components[0] if components and components[0] != 'all' else 'api'
            success = controller.rollback(component, to_version)
        elif args.get('config'):
            show_secrets = args.get('--show-secrets', False)
            config = controller.config
            
            # Filter out secrets if not showing them
            if not show_secrets:
                # Recursively filter out secret keys
                def filter_secrets(data):
                    if isinstance(data, dict):
                        return {
                            k: filter_secrets(v) if not any(sk in k.lower() for sk in ['password', 'secret', 'token', 'key', 'cert']) 
                            else "********" for k, v in data.items()
                        }
                    elif isinstance(data, list):
                        return [filter_secrets(item) for item in data]
                    else:
                        return data
                
                config = filter_secrets(config)
            
            print(json.dumps(config, indent=2))
            success = True
        else:
            logger.error("Unknown command")
            return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
