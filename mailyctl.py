#!/usr/bin/env python3

"""
Maily Control Tool (mailyctl)

A command-line tool for managing the Maily platform across different environments.
This tool provides functionality for deploying, verifying, and testing Maily components.

Usage:
  mailyctl.py deploy [--env=<environment>] [--version=<version>] [--components=<components>]
  mailyctl.py verify [--env=<environment>] [--version=<version>] [--components=<components>]
  mailyctl.py test [--env=<environment>] [--scope=<scope>]
  mailyctl.py status [--env=<environment>] [--components=<components>]
  mailyctl.py logs [--env=<environment>] [--components=<components>] [--tail=<lines>]
  mailyctl.py rollback [--env=<environment>] [--components=<components>] [--to-version=<version>]
  mailyctl.py config [--env=<environment>] [--show-secrets]
  mailyctl.py (-h | --help)
  mailyctl.py --version

Options:
  -h --help                 Show this help message and exit.
  --version                 Show version.
  --env=<environment>       Environment to target [default: staging].
  --components=<components> Comma-separated list of components to target [default: all].
  --version=<version>       Version to deploy [default: latest].
  --scope=<scope>           Test scope (unit, integration, e2e, post-deployment) [default: all].
  --tail=<lines>            Number of log lines to show [default: 100].
  --to-version=<version>    Version to rollback to.
  --show-secrets            Show secrets in config output.
"""

import os
import sys
import yaml
import json
import time
import logging
import subprocess
import concurrent.futures
from typing import List, Dict, Any, Optional, Union
from docopt import docopt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mailyctl')

# Constants
VERSION = '1.0.0'
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
SYSTEM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'system')
VALIDATORS_DIR = os.path.join(SYSTEM_DIR, 'validators')
VERIFIERS_DIR = os.path.join(SYSTEM_DIR, 'verifiers')

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
    'workers'
]

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
            'workers': None  # No validator for workers
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
            'workers': None  # No verifier for workers
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
