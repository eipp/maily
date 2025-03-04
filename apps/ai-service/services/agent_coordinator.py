"""
Agent Coordinator Service for AI Mesh Network

This service coordinates a network of specialized AI agents with shared memory and dynamic task delegation.
It includes rate limiting, security features, and long-term memory persistence.
"""

import json
import logging
import uuid
import asyncio
import time
import functools
import traceback
import hashlib
import hmac
from typing import Dict, Any, List, Optional, Tuple, Union, Callable, TypeVar, Awaitable
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
import random
import os

from ..utils.redis_client import get_redis_client, get_rate_limiter
from ..utils.llm_client import get_llm_client, LLMClient
from ..implementations.memory.long_term_memory import get_tiered_memory_storage
# Import the broadcast functions - will be imported later after they're defined
# to avoid circular imports

logger = logging.getLogger("ai_service.services.agent_coordinator")

# Security and audit modules
audit_logger = logging.getLogger("ai_service.audit")
# Configure audit logger to write to a separate file
audit_handler = logging.FileHandler("logs/audit.log")
audit_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False  # Don't send audit logs to parent loggers

# Constants
NETWORK_KEY_PREFIX = "ai_mesh:network:"
AGENT_KEY_PREFIX = "ai_mesh:agent:"
TASK_KEY_PREFIX = "ai_mesh:task:"
MEMORY_KEY_PREFIX = "ai_mesh:memory:"
AUDIT_LOG_KEY_PREFIX = "ai_mesh:audit:"
TOKEN_KEY_PREFIX = "ai_mesh:token:"
AGENT_TYPES = ["content", "design", "analytics", "personalization", "coordinator", "research", "critic"]
MODEL_FALLBACK_CHAIN = ["claude-3-7-sonnet", "gpt-4o", "gemini-2.0"]

# Default data retention period in days
DEFAULT_DATA_RETENTION_DAYS = 90

# Authentication and security models
class AuthCredential(BaseModel):
    """Authentication credential model for AI Mesh operations"""
    api_key: str
    user_id: str
    role: str = "user"  # Possible values: "user", "admin", "service"
    scopes: List[str] = Field(default_factory=list)
    
    @validator("scopes", pre=True, always=True)
    def set_default_scopes(cls, scopes, values):
        """Set default scopes based on role if not provided"""
        if not scopes:
            role = values.get("role", "user")
            if role == "admin":
                return ["read", "write", "admin"]
            elif role == "service":
                return ["read", "write", "service"]
            else:
                return ["read", "write"]
        return scopes
    
    def can_access(self, resource_type: str, operation: str) -> bool:
        """Check if credential has access to perform operation on resource type"""
        # Admin can access everything
        if "admin" in self.scopes:
            return True
            
        # Service accounts can access service operations
        if "service" in self.scopes and operation in ["read", "write", "create", "delete"]:
            return True
            
        # Check specific permissions
        if operation == "read" and "read" in self.scopes:
            return True
            
        if operation == "write" and "write" in self.scopes:
            return True
            
        if operation == "create" and ("write" in self.scopes or "create" in self.scopes):
            return True
            
        if operation == "delete" and ("admin" in self.scopes or "delete" in self.scopes):
            return True
            
        return False

class AuditLogEntry(BaseModel):
    """Audit log entry for AI Mesh operations"""
    id: str
    timestamp: datetime
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    operation: str
    status: str
    details: Optional[Dict[str, Any]] = None
    client_ip: Optional[str] = None
    session_id: Optional[str] = None

class SecurityManager:
    """Security manager for AI Mesh operations"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        # Load API key from environment variable or use a placeholder in development
        self.api_secret = os.environ.get("AI_MESH_API_SECRET", "default-secret-change-in-production")
        
    async def verify_api_key(self, api_key: str) -> Optional[AuthCredential]:
        """Verify API key and return credentials if valid"""
        try:
            # Get credential from Redis
            token_key = f"{TOKEN_KEY_PREFIX}{api_key}"
            credential_data = await self.redis.get(token_key)
            
            if not credential_data:
                return None
                
            # Parse credential data
            credential_dict = json.loads(credential_data)
            return AuthCredential(**credential_dict)
            
        except Exception as e:
            logger.error(f"Failed to verify API key: {e}")
            return None
    
    def generate_api_key(self, user_id: str, role: str = "user", scopes: List[str] = None) -> str:
        """Generate a new API key for a user"""
        # Create a new API key using HMAC
        timestamp = str(int(time.time()))
        message = f"{user_id}:{timestamp}:{role}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Create API key format: first 8 chars of user_id + timestamp + first 8 chars of signature
        api_key = f"{user_id[:8]}.{timestamp}.{signature[:8]}"
        return api_key
    
    async def create_api_credential(self, user_id: str, role: str = "user", scopes: List[str] = None) -> Dict[str, Any]:
        """Create API credential for a user and store in Redis"""
        # Generate API key
        api_key = self.generate_api_key(user_id, role)
        
        # Create credential
        credential = AuthCredential(
            api_key=api_key,
            user_id=user_id,
            role=role,
            scopes=scopes or []
        )
        
        # Store in Redis with 90-day expiry by default
        token_key = f"{TOKEN_KEY_PREFIX}{api_key}"
        await self.redis.set(
            token_key, 
            json.dumps(credential.dict()),
            ex=60 * 60 * 24 * DEFAULT_DATA_RETENTION_DAYS  # 90 days expiry
        )
        
        return {
            "api_key": api_key,
            "user_id": user_id,
            "role": role,
            "scopes": credential.scopes,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=DEFAULT_DATA_RETENTION_DAYS)).isoformat()
        }
    
    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        try:
            # Delete from Redis
            token_key = f"{TOKEN_KEY_PREFIX}{api_key}"
            result = await self.redis.delete(token_key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            return False

class AuditManager:
    """Audit manager for AI Mesh operations"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        
    async def log_operation(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        operation: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        client_ip: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> None:
        """Log an operation to the audit log"""
        try:
            # Create audit log entry
            entry_id = f"audit_{uuid.uuid4().hex}"
            entry = AuditLogEntry(
                id=entry_id,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                operation=operation,
                status=status,
                details=details,
                client_ip=client_ip,
                session_id=session_id
            )
            
            # Store in Redis with TTL
            entry_key = f"{AUDIT_LOG_KEY_PREFIX}{entry_id}"
            await self.redis.set(
                entry_key, 
                json.dumps(entry.dict(), default=str),  # Use default=str to handle datetime serialization
                ex=60 * 60 * 24 * DEFAULT_DATA_RETENTION_DAYS  # 90 days retention
            )
            
            # Also log to audit logger for immediate visibility
            audit_logger.info(
                f"AUDIT: {user_id} - {action} - {resource_type}:{resource_id} - {operation} - {status}"
            )
            
        except Exception as e:
            logger.error(f"Failed to log audit entry: {e}")
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit logs with filtering"""
        try:
            # Get all audit log keys
            audit_keys = await self.redis.keys(f"{AUDIT_LOG_KEY_PREFIX}*")
            
            # Sort keys by timestamp (newer first)
            audit_entries = []
            
            # Create Redis pipeline for batch retrieval
            pipeline = self.redis.pipeline()
            
            # Add all gets to the pipeline
            for key in audit_keys:
                pipeline.get(key)
            
            # Execute pipeline
            results = await pipeline.execute()
            
            # Process results
            for data in results:
                if not data:
                    continue
                    
                entry = json.loads(data)
                
                # Convert timestamp string to datetime for comparison
                entry_time = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                
                # Apply filters
                if user_id and entry["user_id"] != user_id:
                    continue
                    
                if resource_type and entry["resource_type"] != resource_type:
                    continue
                    
                if action and entry["action"] != action:
                    continue
                    
                if start_time and entry_time < start_time:
                    continue
                    
                if end_time and entry_time > end_time:
                    continue
                
                audit_entries.append(entry)
            
            # Sort by timestamp (newer first)
            audit_entries.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # Apply pagination
            paginated_entries = audit_entries[offset:offset + limit]
            
            return paginated_entries
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []

class DataRetentionManager:
    """Data retention manager for AI Mesh operations"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.retention_period = DEFAULT_DATA_RETENTION_DAYS
    
    async def set_retention_policy(self, retention_days: int) -> None:
        """Set data retention policy in days"""
        self.retention_period = max(1, retention_days)  # Minimum 1 day
        
        # Store policy in Redis for persistence
        await self.redis.set("ai_mesh:config:retention_days", str(self.retention_period))
    
    async def get_retention_policy(self) -> int:
        """Get data retention policy in days"""
        policy = await self.redis.get("ai_mesh:config:retention_days")
        if policy:
            return int(policy)
        return self.retention_period
    
    async def cleanup_expired_data(self) -> Dict[str, int]:
        """
        Clean up expired data based on retention policy
        Returns count of deleted items by type
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_period)
            cutoff_timestamp = cutoff_date.isoformat()
            
            deleted_counts = {
                "networks": 0,
                "agents": 0,
                "tasks": 0,
                "memories": 0,
                "audit_logs": 0
            }
            
            # Get all network keys
            network_keys = await self.redis.keys(f"{NETWORK_KEY_PREFIX}*")
            
            # Process networks and their resources
            for network_key in network_keys:
                network_data = await self.redis.get(network_key)
                if not network_data:
                    continue
                
                network = json.loads(network_data)
                
                # Check if network is expired
                created_at = datetime.fromisoformat(network["created_at"].replace("Z", "+00:00"))
                if created_at < cutoff_date:
                    # Delete network and all associated resources
                    await self.delete_network_resources(network)
                    deleted_counts["networks"] += 1
            
            # Clean up audit logs
            audit_keys = await self.redis.keys(f"{AUDIT_LOG_KEY_PREFIX}*")
            for audit_key in audit_keys:
                audit_data = await self.redis.get(audit_key)
                if not audit_data:
                    continue
                
                audit = json.loads(audit_data)
                audit_time = datetime.fromisoformat(audit["timestamp"].replace("Z", "+00:00"))
                
                if audit_time < cutoff_date:
                    await self.redis.delete(audit_key)
                    deleted_counts["audit_logs"] += 1
            
            return deleted_counts
            
        except Exception as e:
            logger.error(f"Failed to clean up expired data: {e}")
            return {"error": str(e)}
    
    async def delete_network_resources(self, network: Dict[str, Any]) -> None:
        """Delete all resources associated with a network"""
        try:
            # Create a Redis pipeline for batch deletion
            pipeline = self.redis.pipeline()
            
            # Delete tasks
            for task_id in network.get("tasks", []):
                task_key = f"{TASK_KEY_PREFIX}{task_id}"
                pipeline.delete(task_key)
            
            # Delete agents
            for agent_id in network.get("agents", []):
                agent_key = f"{AGENT_KEY_PREFIX}{agent_id}"
                pipeline.delete(agent_key)
            
            # Delete memories
            for memory_id in network.get("memories", []):
                memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                pipeline.delete(memory_key)
            
            # Delete network itself
            network_key = f"{NETWORK_KEY_PREFIX}{network['id']}"
            pipeline.delete(network_key)
            
            # Execute all deletes in a batch
            await pipeline.execute()
            
        except Exception as e:
            logger.error(f"Failed to delete network resources: {e}")

class InputValidator:
    """Input validation for AI Mesh operations"""
    
    @staticmethod
    def validate_network_creation(name: str, description: Optional[str], agents: Optional[List[Dict[str, Any]]]) -> List[str]:
        """Validate network creation input"""
        errors = []
        
        # Validate name
        if not name or len(name) < 3:
            errors.append("Network name must be at least 3 characters")
        
        if name and len(name) > 100:
            errors.append("Network name must be less than 100 characters")
        
        # Validate description if provided
        if description and len(description) > 1000:
            errors.append("Description must be less than 1000 characters")
        
        # Validate agents if provided
        if agents:
            for i, agent in enumerate(agents):
                # Check required fields
                if "name" not in agent:
                    errors.append(f"Agent {i} is missing name")
                
                if "type" not in agent:
                    errors.append(f"Agent {i} is missing type")
                
                # Validate agent type
                if agent.get("type") not in AGENT_TYPES:
                    valid_types = ", ".join(AGENT_TYPES)
                    errors.append(f"Agent {i} has invalid type. Must be one of: {valid_types}")
                
                # Validate model if provided
                if "model" in agent and agent["model"] not in MODEL_FALLBACK_CHAIN:
                    valid_models = ", ".join(MODEL_FALLBACK_CHAIN)
                    errors.append(f"Agent {i} has invalid model. Must be one of: {valid_models}")
        
        return errors
    
    @staticmethod
    def validate_task_submission(task: str, context: Optional[Dict[str, Any]], priority: int) -> List[str]:
        """Validate task submission input"""
        errors = []
        
        # Validate task
        if not task or len(task) < 5:
            errors.append("Task description must be at least 5 characters")
        
        if task and len(task) > 5000:
            errors.append("Task description must be less than 5000 characters")
        
        # Validate priority
        if not 1 <= priority <= 10:
            errors.append("Priority must be between 1 and 10")
        
        # Validate context if provided
        if context:
            # Check for potentially dangerous content
            context_str = json.dumps(context)
            dangerous_patterns = [
                "exec(", "eval(", "os.system(", "subprocess", "import os",
                "__import__", "lambda", "base64", "decode", "encode"
            ]
            
            for pattern in dangerous_patterns:
                if pattern.lower() in context_str.lower():
                    errors.append(f"Context contains potentially dangerous content: {pattern}")
        
        return errors

class AgentCoordinator:
    """Service for coordinating AI agents in a mesh network"""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.llm_client = get_llm_client()
        self.active_networks = {}  # network_id -> network_info
        self.active_tasks = {}  # task_id -> task_info
        
        # Cache of agent instances with max size and TTL
        self.agent_instances = {}  # agent_id -> (agent_instance, timestamp)
        self.agent_cache_max_size = 100  # Maximum number of agents to keep in cache
        self.agent_cache_ttl = 300  # Time-to-live in seconds (5 minutes)
        
        # Initialize security components
        self.security_manager = SecurityManager(self.redis)
        self.audit_manager = AuditManager(self.redis)
        self.data_retention_manager = DataRetentionManager(self.redis)
        self.input_validator = InputValidator()
        
        # Start background tasks
        asyncio.create_task(self._cache_cleanup_task())
        asyncio.create_task(self._data_retention_task())
        
    async def create_network(
        self,
        name: str,
        description: Optional[str] = None,
        agents: Optional[List[Dict[str, Any]]] = None,
        shared_context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10,
        timeout_seconds: int = 300,
        user_id: str = "anonymous",
        api_key: Optional[str] = None,
        client_ip: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new AI Mesh Network
        
        Args:
            name: Name of the network
            description: Description of the network
            agents: List of agent configurations
            shared_context: Shared context for the network
            max_iterations: Maximum iterations for tasks
            timeout_seconds: Timeout for tasks in seconds
            user_id: ID of the user creating the network
            api_key: API key for authentication
            client_ip: Client IP address for audit logging
            session_id: Session ID for audit logging
            
        Returns:
            Dictionary with network ID and status
        
        Raises:
            ValueError: If validation fails
            PermissionError: If authentication fails
            Exception: For other errors
        """
        try:
            # Validate input
            validation_errors = self.input_validator.validate_network_creation(name, description, agents)
            if validation_errors:
                # Log validation failure to audit log
                await self.audit_manager.log_operation(
                    user_id=user_id,
                    action="create_network",
                    resource_type="network",
                    resource_id="validation_failed",
                    operation="create",
                    status="failed",
                    details={"errors": validation_errors},
                    client_ip=client_ip,
                    session_id=session_id
                )
                raise ValueError(f"Validation failed: {', '.join(validation_errors)}")
            
            # Authenticate user if API key provided
            if api_key:
                credential = await self.security_manager.verify_api_key(api_key)
                if not credential:
                    # Log authentication failure to audit log
                    await self.audit_manager.log_operation(
                        user_id=user_id,
                        action="create_network",
                        resource_type="network",
                        resource_id="auth_failed",
                        operation="create",
                        status="failed",
                        details={"error": "Invalid API key"},
                        client_ip=client_ip,
                        session_id=session_id
                    )
                    raise PermissionError("Authentication failed: Invalid API key")
                
                # Check authorization
                if not credential.can_access("network", "create"):
                    # Log authorization failure to audit log
                    await self.audit_manager.log_operation(
                        user_id=credential.user_id,
                        action="create_network",
                        resource_type="network",
                        resource_id="auth_failed",
                        operation="create",
                        status="failed",
                        details={"error": "Insufficient permissions"},
                        client_ip=client_ip,
                        session_id=session_id
                    )
                    raise PermissionError("Authorization failed: Insufficient permissions")
                
                # Use authenticated user ID
                user_id = credential.user_id
            
            # Generate network ID
            network_id = f"network_{uuid.uuid4().hex[:8]}"
            
            # Log start of network creation to audit log
            await self.audit_manager.log_operation(
                user_id=user_id,
                action="create_network",
                resource_type="network",
                resource_id=network_id,
                operation="create",
                status="in_progress",
                details={
                    "name": name,
                    "description": description,
                    "agent_count": len(agents) if agents else 0
                },
                client_ip=client_ip,
                session_id=session_id
            )
            
            # Create network object with additional security metadata
            network = {
                "id": network_id,
                "name": name,
                "description": description or f"AI Mesh Network: {name}",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "status": "active",
                "max_iterations": max_iterations,
                "timeout_seconds": timeout_seconds,
                "shared_context": shared_context or {},
                "agents": [],
                "tasks": [],
                "memories": [],
                "created_by": user_id,
                "retention_days": DEFAULT_DATA_RETENTION_DAYS,
                "metadata": {
                    "client_ip": client_ip,
                    "session_id": session_id,
                    "creation_timestamp": int(time.time())
                }
            }
            
            # Add agents if provided
            if agents:
                for agent_config in agents:
                    agent_id = await self._create_agent(network_id, agent_config)
                    network["agents"].append(agent_id)
            else:
                # Create default agents if none provided
                await self._create_default_agents(network_id, network)
            
            # Store network in Redis with TTL based on retention policy
            network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
            await self.redis.set(
                network_key, 
                json.dumps(network),
                ex=60 * 60 * 24 * DEFAULT_DATA_RETENTION_DAYS  # TTL based on retention policy
            )
            
            # Add to active networks
            self.active_networks[network_id] = network
            
            # Log successful network creation to audit log
            await self.audit_manager.log_operation(
                user_id=user_id,
                action="create_network",
                resource_type="network",
                resource_id=network_id,
                operation="create",
                status="success",
                details={
                    "name": name,
                    "agent_count": len(network["agents"]),
                    "network_id": network_id
                },
                client_ip=client_ip,
                session_id=session_id
            )
            
            return {
                "network_id": network_id,
                "status": "created",
                "agent_count": len(network["agents"]),
                "name": name,
                "created_at": network["created_at"],
                "created_by": user_id,
                "retention_days": DEFAULT_DATA_RETENTION_DAYS
            }
            
        except (ValueError, PermissionError) as e:
            # These exceptions are already logged and should be passed through
            raise
            
        except Exception as e:
            logger.error(f"Failed to create network: {e}")
            traceback.print_exc()
            
            # Log unexpected error to audit log
            await self.audit_manager.log_operation(
                user_id=user_id,
                action="create_network",
                resource_type="network",
                resource_id="error",
                operation="create",
                status="failed",
                details={"error": str(e)},
                client_ip=client_ip,
                session_id=session_id
            )
            
            raise Exception(f"Failed to create network: {str(e)}")
    
    async def _create_default_agents(self, network_id: str, network: Dict[str, Any]):
        """Create default agents for a network"""
        # Create coordinator agent
        coordinator_config = {
            "name": "Coordinator",
            "type": "coordinator",
            "model": "claude-3-7-sonnet",
            "description": "Coordinates tasks and delegates to specialized agents",
            "parameters": {
                "temperature": 0.2,
                "max_tokens": 4000
            },
            "capabilities": ["task_delegation", "task_coordination", "task_synthesis"]
        }
        coordinator_id = await self._create_agent(network_id, coordinator_config)
        network["agents"].append(coordinator_id)
        
        # Create content agent
        content_config = {
            "name": "Content Specialist",
            "type": "content",
            "model": "claude-3-7-sonnet",
            "description": "Specializes in generating and refining content",
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "capabilities": ["content_generation", "content_editing", "content_analysis"]
        }
        content_id = await self._create_agent(network_id, content_config)
        network["agents"].append(content_id)
        
        # Create design agent
        design_config = {
            "name": "Design Specialist",
            "type": "design",
            "model": "claude-3-7-sonnet",
            "description": "Specializes in design and layout considerations",
            "parameters": {
                "temperature": 0.6,
                "max_tokens": 4000
            },
            "capabilities": ["design_suggestions", "layout_analysis", "visual_planning"]
        }
        design_id = await self._create_agent(network_id, design_config)
        network["agents"].append(design_id)
        
        # Create analytics agent
        analytics_config = {
            "name": "Analytics Specialist",
            "type": "analytics",
            "model": "claude-3-7-sonnet",
            "description": "Specializes in data analysis and performance insights",
            "parameters": {
                "temperature": 0.2,
                "max_tokens": 4000
            },
            "capabilities": ["data_analysis", "performance_prediction", "trend_identification"]
        }
        analytics_id = await self._create_agent(network_id, analytics_config)
        network["agents"].append(analytics_id)
        
        # Create personalization agent
        personalization_config = {
            "name": "Personalization Specialist",
            "type": "personalization",
            "model": "claude-3-7-sonnet",
            "description": "Specializes in audience targeting and personalization",
            "parameters": {
                "temperature": 0.5,
                "max_tokens": 4000
            },
            "capabilities": ["audience_analysis", "personalization", "segmentation"]
        }
        personalization_id = await self._create_agent(network_id, personalization_config)
        network["agents"].append(personalization_id)
    
    async def _cache_cleanup_task(self):
        """Background task to clean up agent cache periodically"""
        try:
            while True:
                # Wait for cleanup interval (1 minute)
                await asyncio.sleep(60)
                
                # Get current time
                current_time = time.time()
                
                # Remove expired entries from cache
                expired_keys = []
                for agent_id, (agent, timestamp) in self.agent_instances.items():
                    if current_time - timestamp > self.agent_cache_ttl:
                        expired_keys.append(agent_id)
                
                # Remove expired entries
                for agent_id in expired_keys:
                    del self.agent_instances[agent_id]
                
                if expired_keys:
                    logger.info(f"Removed {len(expired_keys)} expired agents from cache")
                    
                # If cache still too large, remove oldest entries
                if len(self.agent_instances) > self.agent_cache_max_size:
                    # Sort by timestamp (oldest first)
                    sorted_items = sorted(
                        self.agent_instances.items(), 
                        key=lambda x: x[1][1]  # x = (agent_id, (agent, timestamp))
                    )
                    
                    # Calculate number of items to remove
                    remove_count = len(self.agent_instances) - self.agent_cache_max_size
                    
                    # Remove oldest items
                    for i in range(remove_count):
                        agent_id, _ = sorted_items[i]
                        del self.agent_instances[agent_id]
                    
                    logger.info(f"Removed {remove_count} oldest agents from cache due to size limit")
                
        except Exception as e:
            logger.error(f"Error in cache cleanup task: {e}")
            # Restart the task
            asyncio.create_task(self._cache_cleanup_task())
            
    async def _data_retention_task(self):
        """Background task to clean up expired data based on retention policy"""
        try:
            while True:
                # Run data retention cleanup once per day
                await asyncio.sleep(24 * 60 * 60)  # 24 hours
                
                try:
                    # Get current retention policy
                    retention_days = await self.data_retention_manager.get_retention_policy()
                    logger.info(f"Running data retention cleanup with {retention_days} days policy")
                    
                    # Run cleanup
                    deleted_counts = await self.data_retention_manager.cleanup_expired_data()
                    
                    # Log results
                    total_deleted = sum(deleted_counts.values()) if isinstance(deleted_counts, dict) else 0
                    logger.info(f"Data retention cleanup completed: {total_deleted} items deleted")
                    
                    # Log detailed counts
                    if isinstance(deleted_counts, dict) and not "error" in deleted_counts:
                        for key, count in deleted_counts.items():
                            if count > 0:
                                logger.info(f"Data retention cleanup: {count} {key} deleted")
                    
                    # Log to audit log
                    await self.audit_manager.log_operation(
                        user_id="system",
                        action="data_retention_cleanup",
                        resource_type="system",
                        resource_id="data_retention",
                        operation="cleanup",
                        status="success",
                        details=deleted_counts if isinstance(deleted_counts, dict) else {"error": str(deleted_counts)}
                    )
                    
                except Exception as inner_e:
                    logger.error(f"Error in data retention cleanup: {inner_e}")
                    traceback.print_exc()
                    # Log to audit log
                    await self.audit_manager.log_operation(
                        user_id="system",
                        action="data_retention_cleanup",
                        resource_type="system",
                        resource_id="data_retention",
                        operation="cleanup",
                        status="failed",
                        details={"error": str(inner_e)}
                    )
                
        except Exception as e:
            logger.error(f"Error in data retention task: {e}")
            # Restart the task
            asyncio.create_task(self._data_retention_task())
    
    async def _create_agent(self, network_id: str, agent_config: Dict[str, Any]) -> str:
        """Create an agent for a network"""
        # Generate agent ID
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        # Create agent object
        agent = {
            "id": agent_id,
            "network_id": network_id,
            "name": agent_config["name"],
            "type": agent_config["type"],
            "model": agent_config["model"],
            "description": agent_config.get("description", f"{agent_config['type'].capitalize()} Agent"),
            "parameters": agent_config.get("parameters", {}),
            "capabilities": agent_config.get("capabilities", []),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "status": "idle",
            "confidence": 1.0,
            "last_action": None,
            "assigned_tasks": [],
            "connections": []
        }
        
        # Store agent in Redis
        agent_key = f"{AGENT_KEY_PREFIX}{agent_id}"
        await self.redis.set(agent_key, json.dumps(agent))
        
        # Store in cache with timestamp
        self.agent_instances[agent_id] = (agent, time.time())
        
        return agent_id
    
    async def list_networks(self) -> List[Dict[str, Any]]:
        """List all AI Mesh Networks"""
        try:
            # Get all network keys
            network_keys = await self.redis.keys(f"{NETWORK_KEY_PREFIX}*")
            
            networks = []
            for key in network_keys:
                network_data = await self.redis.get(key)
                if network_data:
                    network = json.loads(network_data)
                    # Add summary data only
                    networks.append({
                        "id": network["id"],
                        "name": network["name"],
                        "description": network["description"],
                        "created_at": network["created_at"],
                        "status": network["status"],
                        "agent_count": len(network["agents"]),
                        "task_count": len(network["tasks"]),
                        "memory_count": len(network["memories"])
                    })
            
            return networks
            
        except Exception as e:
            logger.error(f"Failed to list networks: {e}")
            return []
    
    async def get_network(self, network_id: str) -> Optional[Dict[str, Any]]:
        """Get details of an AI Mesh Network using concurrent fetching and functional patterns"""
        try:
            # Import utilities for concurrent processing
            from ..utils.concurrent import process_concurrently
            
            # Get network from Redis
            network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
            network_data = await self.redis.get(network_key)
            
            if not network_data:
                logger.warning(f"Network {network_id} not found in Redis")
                return None
            
            # Parse network data
            network = json.loads(network_data)
            
            # Define processor functions for each entity type
            async def fetch_agent(agent_id):
                return await self._get_agent(agent_id)
                
            async def fetch_task(task_id):
                return await self.get_task(task_id)
                
            async def fetch_memory(memory_id):
                return await self._get_memory(memory_id)
            
            # Prepare concurrent fetching for all entity types
            fetch_tasks = []
            
            # Only fetch if there are entities to fetch
            if network["agents"]:
                fetch_tasks.append(('agents', process_concurrently(network["agents"], fetch_agent)))
                
            if network["tasks"]:
                fetch_tasks.append(('tasks', process_concurrently(network["tasks"], fetch_task)))
                
            if network["memories"]:
                fetch_tasks.append(('memories', process_concurrently(network["memories"], fetch_memory)))
            
            # Execute all fetch operations concurrently
            entity_results = {}
            if fetch_tasks:
                entity_types, fetch_awaitables = zip(*fetch_tasks)
                fetch_results = await asyncio.gather(*fetch_awaitables)
                
                # Store results by entity type
                for entity_type, result in zip(entity_types, fetch_results):
                    # Filter out None values from results
                    entity_results[entity_type] = [item for item in result if item is not None]
            
            # Construct network response with immutable data patterns
            network_response = {
                **{k: network[k] for k in [
                    "id", "name", "description", "created_at", 
                    "updated_at", "status", "max_iterations", "timeout_seconds"
                ]},
                "agents": entity_results.get("agents", []),
                "tasks": entity_results.get("tasks", []),
                "memories": entity_results.get("memories", [])
            }
            
            return network_response
            
        except Exception as e:
            logger.error(f"Failed to get network: {e}")
            traceback.print_exc()
            return None
    
    async def delete_network(self, network_id: str) -> bool:
        """Delete an AI Mesh Network"""
        try:
            # Get network from Redis
            network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
            network_data = await self.redis.get(network_key)
            
            if not network_data:
                return False
            
            network = json.loads(network_data)
            
            # Create a Redis pipeline for batch deletion
            pipeline = self.redis.pipeline()
            
            # Add all delete operations to the pipeline
            
            # Delete agents
            for agent_id in network["agents"]:
                # Remove from cache if present
                if agent_id in self.agent_instances:
                    del self.agent_instances[agent_id]
                # Add to pipeline
                agent_key = f"{AGENT_KEY_PREFIX}{agent_id}"
                pipeline.delete(agent_key)
            
            # Delete tasks
            for task_id in network["tasks"]:
                task_key = f"{TASK_KEY_PREFIX}{task_id}"
                pipeline.delete(task_key)
            
            # Delete memories
            for memory_id in network["memories"]:
                memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                pipeline.delete(memory_key)
            
            # Delete network
            pipeline.delete(network_key)
            
            # Execute all delete operations in a single batch
            await pipeline.execute()
            
            # Remove from active networks
            if network_id in self.active_networks:
                del self.active_networks[network_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete network: {e}")
            traceback.print_exc()
            return False
    
    async def submit_task(
        self,
        network_id: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        priority: int = 1,
        deadline: Optional[datetime] = None,
        user_id: str = "anonymous",
        api_key: Optional[str] = None,
        client_ip: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit a task to an AI Mesh Network
        
        Args:
            network_id: ID of the network to submit task to
            task: Task description
            context: Additional context for the task
            priority: Task priority (1-10)
            deadline: Optional deadline for task completion
            user_id: ID of the user submitting the task
            api_key: API key for authentication
            client_ip: Client IP address for audit logging
            session_id: Session ID for audit logging
            
        Returns:
            Dictionary with task ID and status
            
        Raises:
            ValueError: If validation fails or network not found
            PermissionError: If authentication fails
            Exception: For other errors
        """
        try:
            # Validate input
            validation_errors = self.input_validator.validate_task_submission(task, context, priority)
            if validation_errors:
                # Log validation failure
                await self.audit_manager.log_operation(
                    user_id=user_id,
                    action="submit_task",
                    resource_type="task",
                    resource_id="validation_failed",
                    operation="create",
                    status="failed",
                    details={"errors": validation_errors, "network_id": network_id},
                    client_ip=client_ip,
                    session_id=session_id
                )
                raise ValueError(f"Validation failed: {', '.join(validation_errors)}")
            
            # Authenticate user if API key provided
            if api_key:
                credential = await self.security_manager.verify_api_key(api_key)
                if not credential:
                    # Log authentication failure
                    await self.audit_manager.log_operation(
                        user_id=user_id,
                        action="submit_task",
                        resource_type="task",
                        resource_id="auth_failed",
                        operation="create",
                        status="failed",
                        details={"error": "Invalid API key", "network_id": network_id},
                        client_ip=client_ip,
                        session_id=session_id
                    )
                    raise PermissionError("Authentication failed: Invalid API key")
                
                # Check authorization
                if not credential.can_access("task", "create"):
                    # Log authorization failure
                    await self.audit_manager.log_operation(
                        user_id=credential.user_id,
                        action="submit_task",
                        resource_type="task",
                        resource_id="auth_failed",
                        operation="create",
                        status="failed",
                        details={"error": "Insufficient permissions", "network_id": network_id},
                        client_ip=client_ip,
                        session_id=session_id
                    )
                    raise PermissionError("Authorization failed: Insufficient permissions")
                
                # Use authenticated user ID
                user_id = credential.user_id
                
            # Apply rate limiting for task submission
            rate_limiter = await get_rate_limiter()
            
            # Rate limit based on user ID and network ID
            rate_limit_key = f"task_submission:{user_id}:{network_id}"
            
            # Check rate limit - allow up to 10 task submissions per minute, with burst of 20
            allowed, info = await rate_limiter.check_rate_limit(
                rate_limit_key,
                tokens=1,  # Each submission consumes 1 token
                capacity=20,  # Maximum 20 tokens in bucket (burst capacity)
                refill_rate=10,  # Refill 10 tokens per minute
                refill_interval_seconds=60  # Interval is 1 minute
            )
            
            if not allowed:
                # Rate limited
                await self.audit_manager.log_operation(
                    user_id=user_id,
                    action="submit_task",
                    resource_type="task",
                    resource_id="rate_limited",
                    operation="create",
                    status="failed",
                    details={
                        "error": "Rate limit exceeded",
                        "wait_time_seconds": info.get("wait_time_seconds", 60),
                        "network_id": network_id
                    },
                    client_ip=client_ip,
                    session_id=session_id
                )
                raise ValueError(
                    f"Rate limit exceeded. Please try again in {info.get('wait_time_seconds', 60)} seconds. "
                    f"Current limit: 10 submissions per minute."
                )
            
            # Check if network exists
            network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
            network_data = await self.redis.get(network_key)
            
            if not network_data:
                # Log network not found error
                await self.audit_manager.log_operation(
                    user_id=user_id,
                    action="submit_task",
                    resource_type="task",
                    resource_id="network_not_found",
                    operation="create",
                    status="failed",
                    details={"error": f"Network {network_id} not found"},
                    client_ip=client_ip,
                    session_id=session_id
                )
                raise ValueError(f"Network {network_id} not found")
            
            network = json.loads(network_data)
            
            # Additional authorization check: verify user has access to this network
            if api_key and user_id != network.get("created_by") and "admin" not in credential.scopes:
                # Only network creator or admin can submit tasks
                # Log authorization failure
                await self.audit_manager.log_operation(
                    user_id=user_id,
                    action="submit_task",
                    resource_type="task",
                    resource_id="network_access_denied",
                    operation="create",
                    status="failed",
                    details={"error": "Not authorized to submit tasks to this network", "network_id": network_id},
                    client_ip=client_ip,
                    session_id=session_id
                )
                raise PermissionError("Not authorized to submit tasks to this network")
            
            # Log task submission start
            await self.audit_manager.log_operation(
                user_id=user_id,
                action="submit_task",
                resource_type="task",
                resource_id="task_submission",
                operation="create",
                status="in_progress",
                details={
                    "network_id": network_id,
                    "task_description": task[:100] + ("..." if len(task) > 100 else ""),
                    "priority": priority
                },
                client_ip=client_ip,
                session_id=session_id
            )
            
            # Generate task ID
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            
            # Create task object with security metadata
            task_obj = {
                "id": task_id,
                "network_id": network_id,
                "description": task,
                "context": context or {},
                "priority": priority,
                "deadline": deadline.isoformat() if deadline else None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "status": "pending",
                "assigned_to": None,
                "iterations": 0,
                "max_iterations": network["max_iterations"],
                "result": None,
                "subtasks": [],
                "dependencies": [],
                "history": [],
                "created_by": user_id,
                "metadata": {
                    "client_ip": client_ip,
                    "session_id": session_id,
                    "creation_timestamp": int(time.time())
                }
            }
            
            # Sanitize task input for security if needed
            # This would be custom filtering for potentially harmful content
            if context:
                # Sanitize context to prevent injection
                sanitized_context = self._sanitize_task_context(context)
                task_obj["context"] = sanitized_context
            
            # Store task in Redis with TTL based on retention policy
            task_key = f"{TASK_KEY_PREFIX}{task_id}"
            await self.redis.set(
                task_key, 
                json.dumps(task_obj),
                ex=60 * 60 * 24 * network.get("retention_days", DEFAULT_DATA_RETENTION_DAYS)
            )
            
            # Update network tasks
            network["tasks"].append(task_id)
            network["updated_at"] = datetime.utcnow().isoformat()
            await self.redis.set(network_key, json.dumps(network))
            
            # Add to active tasks
            self.active_tasks[task_id] = task_obj
            
            # Log successful task submission
            await self.audit_manager.log_operation(
                user_id=user_id,
                action="submit_task",
                resource_type="task",
                resource_id=task_id,
                operation="create",
                status="success",
                details={
                    "network_id": network_id,
                    "task_id": task_id,
                    "priority": priority
                },
                client_ip=client_ip,
                session_id=session_id
            )
            
            return {
                "task_id": task_id,
                "status": "submitted",
                "network_id": network_id,
                "priority": priority,
                "created_at": task_obj["created_at"],
                "created_by": user_id
            }
            
        except (ValueError, PermissionError) as e:
            # These exceptions are already logged and should be passed through
            raise
            
        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            traceback.print_exc()
            
            # Log unexpected error
            await self.audit_manager.log_operation(
                user_id=user_id,
                action="submit_task",
                resource_type="task",
                resource_id="error",
                operation="create",
                status="failed",
                details={"error": str(e), "network_id": network_id},
                client_ip=client_ip,
                session_id=session_id
            )
            
            raise Exception(f"Failed to submit task: {str(e)}")
            
    def _sanitize_task_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize task context to prevent injection attacks
        
        This is a basic implementation. In a production system, this would be more comprehensive.
        """
        # Create a copy to avoid modifying the original
        sanitized = {}
        
        # Process each key-value pair
        for key, value in context.items():
            # Sanitize keys - only allow alphanumeric and underscore
            safe_key = "".join(c for c in key if c.isalnum() or c == '_')
            
            # Sanitize values based on type
            if isinstance(value, str):
                # Remove potentially dangerous patterns
                dangerous_patterns = [
                    "exec(", "eval(", "os.system(", "subprocess", 
                    "__import__", "import os", "lambda", "base64.decode"
                ]
                
                safe_value = value
                for pattern in dangerous_patterns:
                    safe_value = safe_value.replace(pattern, "[FILTERED]")
                    
                sanitized[safe_key] = safe_value
                
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[safe_key] = self._sanitize_task_context(value)
                
            elif isinstance(value, list):
                # Sanitize list items
                sanitized[safe_key] = [
                    self._sanitize_task_context({0: item})[0] 
                    if isinstance(item, dict) else item
                    for item in value
                ]
                
            else:
                # For other types (numbers, booleans, None), keep as is
                sanitized[safe_key] = value
                
        return sanitized
    
    async def _validate_task_and_network(
        self, 
        network_id: str, 
        task_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Validate task and network exist and are valid"""
        task = await self.get_task(task_id)
        
        if not task:
            logger.error(f"Task {task_id} not found")
            return None, None
        
        network = await self.get_network(network_id)
        
        if not network:
            logger.error(f"Network {network_id} not found")
            return task, None
            
        return task, network
        
    async def _update_task_assignment(
        self, 
        task: Dict[str, Any], 
        coordinator_agent: Dict[str, Any]
    ) -> None:
        """Update task and agent assignment atomically"""
        # Create updated task
        updated_task = {
            **task,
            "status": "in_progress",
            "assigned_to": coordinator_agent["id"],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Create updated agent
        updated_agent = {
            **coordinator_agent,
            "assigned_tasks": [*coordinator_agent["assigned_tasks"], task["id"]],
            "status": "working",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Save both updates
        await asyncio.gather(
            self._save_task(updated_task),
            self._save_agent(updated_agent)
        )
        
    async def _complete_task(
        self, 
        task: Dict[str, Any], 
        coordinator_agent: Dict[str, Any], 
        result: Dict[str, Any]
    ) -> None:
        """Mark task as completed and update agent status"""
        # Create updated task
        updated_task = {
            **task,
            "result": result,
            "status": "completed",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Create updated agent
        updated_agent = {
            **coordinator_agent,
            "assigned_tasks": [t for t in coordinator_agent["assigned_tasks"] if t != task["id"]],
            "status": "idle",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Save both updates
        await asyncio.gather(
            self._save_task(updated_task),
            self._save_agent(updated_agent)
        )
        
    async def _mark_task_failed(
        self, 
        task_id: str, 
        coordinator_agent: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark task as failed and update agent if available"""
        try:
            # Update task status to failed
            task = await self.get_task(task_id)
            if not task:
                return
                
            updated_task = {
                **task,
                "status": "failed",
                "updated_at": datetime.utcnow().isoformat(),
                "error": "Task processing failed"
            }
            
            updates = [self._save_task(updated_task)]
            
            # Update agent if provided
            if coordinator_agent:
                updated_agent = {
                    **coordinator_agent,
                    "assigned_tasks": [t for t in coordinator_agent["assigned_tasks"] if t != task_id],
                    "status": "idle",
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                updates.append(self._save_agent(updated_agent))
            
            # Execute all updates
            await asyncio.gather(*updates)
                
        except Exception as e:
            logger.error(f"Failed to mark task as failed: {e}")
        
    async def process_task(
        self,
        network_id: str,
        task_id: str,
        user_id: str = "system",
        api_key: Optional[str] = None,
        client_ip: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a task in the AI Mesh Network
        
        Args:
            network_id: ID of the network
            task_id: ID of the task to process
            user_id: ID of the user initiating processing
            api_key: API key for authentication
            client_ip: Client IP address for audit logging
            session_id: Session ID for audit logging
            
        Returns:
            Dictionary with processing status and results
        """
        # Import broadcast functions here to avoid circular imports
        from ..routers.websocket_router import broadcast_task_update, broadcast_network_update
        
        coordinator_agent = None
        task_creator = None
        process_start_time = time.time()
        
        try:
            # Authenticate user if API key provided
            if api_key:
                credential = await self.security_manager.verify_api_key(api_key)
                if not credential:
                    # Log authentication failure
                    await self.audit_manager.log_operation(
                        user_id=user_id,
                        action="process_task",
                        resource_type="task",
                        resource_id=task_id,
                        operation="process",
                        status="failed",
                        details={"error": "Invalid API key", "network_id": network_id},
                        client_ip=client_ip,
                        session_id=session_id
                    )
                    raise PermissionError("Authentication failed: Invalid API key")
                
                # Check authorization
                if not credential.can_access("task", "process"):
                    # Log authorization failure
                    await self.audit_manager.log_operation(
                        user_id=credential.user_id,
                        action="process_task",
                        resource_type="task",
                        resource_id=task_id,
                        operation="process",
                        status="failed",
                        details={"error": "Insufficient permissions", "network_id": network_id},
                        client_ip=client_ip,
                        session_id=session_id
                    )
                    raise PermissionError("Authorization failed: Insufficient permissions")
                
                # Use authenticated user ID
                user_id = credential.user_id
            
            # Log task processing start
            await self.audit_manager.log_operation(
                user_id=user_id,
                action="process_task",
                resource_type="task",
                resource_id=task_id,
                operation="process",
                status="in_progress",
                details={"network_id": network_id},
                client_ip=client_ip,
                session_id=session_id
            )
            
            # Validate task and network
            task, network = await self._validate_task_and_network(network_id, task_id)
            if not task or not network:
                # Log validation failure
                await self.audit_manager.log_operation(
                    user_id=user_id,
                    action="process_task",
                    resource_type="task",
                    resource_id=task_id,
                    operation="process",
                    status="failed",
                    details={
                        "error": f"Task or network not found",
                        "network_id": network_id,
                        "task_exists": task is not None,
                        "network_exists": network is not None
                    },
                    client_ip=client_ip,
                    session_id=session_id
                )
                return {
                    "status": "failed",
                    "error": "Task or network not found",
                    "task_id": task_id,
                    "network_id": network_id
                }
            
            # Track task creator for authorization check
            task_creator = task.get("created_by", "anonymous")
            
            # Additional authorization check: only admin, task creator, or network creator can process task
            if (api_key and 
                user_id != task_creator and 
                user_id != network.get("created_by") and 
                "admin" not in credential.scopes):
                
                # Log authorization failure
                await self.audit_manager.log_operation(
                    user_id=user_id,
                    action="process_task",
                    resource_type="task",
                    resource_id=task_id,
                    operation="process",
                    status="failed",
                    details={
                        "error": "Not authorized to process this task",
                        "network_id": network_id,
                        "task_creator": task_creator,
                        "network_creator": network.get("created_by")
                    },
                    client_ip=client_ip,
                    session_id=session_id
                )
                raise PermissionError("Not authorized to process this task")
            
            # Find coordinator agent with functional approach
            coordinator_agent = next(
                (agent for agent in network["agents"] if agent["type"] == "coordinator"), 
                None
            )
            
            if not coordinator_agent:
                logger.error(f"No coordinator agent found in network {network_id}")
                await self._mark_task_failed(task_id)
                
                # Log coordinator agent not found
                await self.audit_manager.log_operation(
                    user_id=user_id,
                    action="process_task",
                    resource_type="task",
                    resource_id=task_id,
                    operation="process",
                    status="failed",
                    details={"error": "No coordinator agent found in network", "network_id": network_id},
                    client_ip=client_ip,
                    session_id=session_id
                )
                
                # Send failure notification via WebSocket
                await broadcast_task_update(
                    task_id=task_id,
                    update_type="task_failed",
                    data={"error": "No coordinator agent found in network"}
                )
                return {
                    "status": "failed",
                    "error": "No coordinator agent found in network",
                    "task_id": task_id,
                    "network_id": network_id
                }
            
            # Update task and agent states atomically
            await self._update_task_assignment(task, coordinator_agent)
            
            # Send task started notification via WebSocket
            await broadcast_task_update(
                task_id=task_id,
                update_type="task_started",
                data={
                    "task_id": task_id,
                    "network_id": network_id,
                    "coordinator_agent_id": coordinator_agent["id"]
                }
            )
            
            # Send network update
            await broadcast_network_update(
                network_id=network_id,
                update_type="task_processing",
                data={
                    "task_id": task_id,
                    "status": "in_progress",
                    "coordinator_agent_id": coordinator_agent["id"]
                }
            )
            
            # Log processing with coordinator start
            await self.audit_manager.log_operation(
                user_id=user_id,
                action="process_task",
                resource_type="task",
                resource_id=task_id,
                operation="process_with_coordinator",
                status="in_progress",
                details={
                    "network_id": network_id,
                    "coordinator_agent_id": coordinator_agent["id"]
                },
                client_ip=client_ip,
                session_id=session_id
            )
            
            # Process task with coordinator agent
            result = await self._process_with_coordinator(network, coordinator_agent, task)
            
            # Complete task
            await self._complete_task(task, coordinator_agent, result)
            
            # Calculate processing duration
            process_duration = time.time() - process_start_time
            
            # Log successful task processing
            await self.audit_manager.log_operation(
                user_id=user_id,
                action="process_task",
                resource_type="task",
                resource_id=task_id,
                operation="process",
                status="success",
                details={
                    "network_id": network_id,
                    "coordinator_agent_id": coordinator_agent["id"],
                    "duration_seconds": round(process_duration, 2),
                    "content_length": len(json.dumps(result)),
                    "confidence": result.get("confidence", 0)
                },
                client_ip=client_ip,
                session_id=session_id
            )
            
            # Send task completed notification via WebSocket
            await broadcast_task_update(
                task_id=task_id,
                update_type="task_completed",
                data={
                    "task_id": task_id,
                    "network_id": network_id,
                    "result": result
                }
            )
            
            # Send network update
            await broadcast_network_update(
                network_id=network_id,
                update_type="task_completed",
                data={
                    "task_id": task_id,
                    "status": "completed"
                }
            )
            
            return {
                "status": "completed",
                "task_id": task_id,
                "network_id": network_id,
                "result": result,
                "duration_seconds": round(process_duration, 2),
                "confidence": result.get("confidence", 0),
                "processed_by": coordinator_agent["id"],
                "completion_time": datetime.utcnow().isoformat()
            }
            
        except PermissionError as e:
            # These exceptions are already logged
            raise
            
        except Exception as e:
            logger.error(f"Failed to process task: {e}")
            traceback.print_exc()
            
            # Calculate processing duration for failed task
            process_duration = time.time() - process_start_time
            
            # Mark task as failed with coordinator agent information if available
            await self._mark_task_failed(task_id, coordinator_agent)
            
            # Log task processing failure
            await self.audit_manager.log_operation(
                user_id=user_id,
                action="process_task",
                resource_type="task",
                resource_id=task_id,
                operation="process",
                status="failed",
                details={
                    "error": str(e),
                    "network_id": network_id,
                    "coordinator_agent_id": coordinator_agent["id"] if coordinator_agent else None,
                    "duration_seconds": round(process_duration, 2),
                    "stack_trace": traceback.format_exc()[:500]  # Include partial stack trace
                },
                client_ip=client_ip,
                session_id=session_id
            )
            
            # Send failure notification via WebSocket
            await broadcast_task_update(
                task_id=task_id,
                update_type="task_failed",
                data={"error": str(e)}
            )
            
            # Send network update
            await broadcast_network_update(
                network_id=network_id,
                update_type="task_failed",
                data={
                    "task_id": task_id,
                    "error": str(e)
                }
            )
            
            return {
                "status": "failed",
                "task_id": task_id,
                "network_id": network_id,
                "error": str(e),
                "duration_seconds": round(process_duration, 2)
            }
    
    async def _process_with_coordinator(
        self,
        network: Dict[str, Any],
        coordinator_agent: Dict[str, Any],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a task with the coordinator agent"""
        try:
            # Initialize task processing
            iteration = 0
            max_iterations = task["max_iterations"]
            task_complete = False
            result = None
            
            # Get shared memory
            memories = await self.get_network_memory(network["id"])
            
            # Create initial context
            context = {
                "task": task["description"],
                "task_context": task["context"],
                "network_name": network["name"],
                "network_description": network["description"],
                "available_agents": [
                    {
                        "id": agent["id"],
                        "name": agent["name"],
                        "type": agent["type"],
                        "capabilities": agent["capabilities"],
                        "status": agent["status"]
                    }
                    for agent in network["agents"] if agent["id"] != coordinator_agent["id"]
                ],
                "shared_memory": [
                    {
                        "id": memory["id"],
                        "type": memory["type"],
                        "content": memory["content"],
                        "confidence": memory["confidence"]
                    }
                    for memory in memories
                ],
                "iteration": iteration,
                "max_iterations": max_iterations
            }
            
            # Process task iteratively
            while not task_complete and iteration < max_iterations:
                iteration += 1
                
                # Update context
                context["iteration"] = iteration
                
                # Generate coordinator prompt
                prompt = self._generate_coordinator_prompt(coordinator_agent, context)
                
                # Get response from LLM
                response = await self.llm_client.generate_text(
                    prompt=prompt,
                    model=coordinator_agent["model"],
                    temperature=coordinator_agent["parameters"].get("temperature", 0.2),
                    max_tokens=coordinator_agent["parameters"].get("max_tokens", 4000)
                )
                
                # Parse coordinator response
                coordinator_response = self._parse_coordinator_response(response["content"])
                
                # Update task history
                task["history"].append({
                    "iteration": iteration,
                    "agent": coordinator_agent["id"],
                    "action": "coordinate",
                    "timestamp": datetime.utcnow().isoformat(),
                    "input": prompt,
                    "output": response["content"]
                })
                
                # Process coordinator decisions
                if coordinator_response.get("task_complete", False):
                    task_complete = True
                    result = coordinator_response.get("result", {})
                else:
                    # Import concurrent processing utility here to avoid circular imports
                    from ..utils.concurrent import process_concurrently
                    
                    # Process subtasks with specialized agents concurrently
                    subtasks = coordinator_response.get("subtasks", [])
                    
                    # Define processor function for each subtask
                    async def process_single_subtask(subtask_data):
                        subtask_result = await self._process_subtask(
                            network,
                            subtask_data["agent_id"],
                            subtask_data["description"],
                            context
                        )
                        
                        return {
                            "agent_id": subtask_data["agent_id"],
                            "description": subtask_data["description"],
                            "result": subtask_result
                        }
                    
                    # Calculate optimal concurrency based on number of subtasks
                    max_concurrency = min(len(subtasks), 5)  # Limit concurrency to 5
                    
                    # Process all subtasks concurrently
                    logger.info(f"Processing {len(subtasks)} subtasks concurrently with max_concurrency={max_concurrency}")
                    subtask_results = await process_concurrently(
                        subtasks,
                        process_single_subtask,
                        max_concurrency=max_concurrency
                    )
                    
                    # Initialize subtask_results in context if not present
                    context["subtask_results"] = context.get("subtask_results", [])
                    
                    # Add all subtask results to context
                    context["subtask_results"].extend(subtask_results)
                    
                    # Process memories concurrently
                    new_memories = coordinator_response.get("new_memories", [])
                    
                    # Define processor function for memory creation
                    async def create_and_process_memory(memory_item):
                        memory_id = await self.add_memory(
                            network_id=network["id"],
                            content=memory_item["content"],
                            memory_type=memory_item["type"],
                            confidence=memory_item.get("confidence", 1.0),
                            metadata={"created_by": coordinator_agent["id"]}
                        )
                        
                        # Fetch the created memory
                        memory = await self._get_memory(memory_id)
                        
                        if memory:
                            return {
                                "id": memory["id"],
                                "type": memory["type"],
                                "content": memory["content"],
                                "confidence": memory["confidence"]
                            }
                        return None
                    
                    # Process memories concurrently if there are any
                    if new_memories:
                        memory_results = await process_concurrently(
                            new_memories,
                            create_and_process_memory,
                            max_concurrency=5
                        )
                        
                        # Add valid memories to shared context
                        valid_memories = [m for m in memory_results if m is not None]
                        if valid_memories:
                            context["shared_memory"] = context.get("shared_memory", [])
                            context["shared_memory"].extend(valid_memories)
                
                # Save task
                await self._save_task(task)
            
            # If max iterations reached without completion
            if not task_complete:
                # Generate final result
                prompt = self._generate_final_result_prompt(coordinator_agent, context)
                
                # Get response from LLM
                response = await self.llm_client.generate_text(
                    prompt=prompt,
                    model=coordinator_agent["model"],
                    temperature=coordinator_agent["parameters"].get("temperature", 0.2),
                    max_tokens=coordinator_agent["parameters"].get("max_tokens", 4000)
                )
                
                # Parse final result
                result = self._parse_final_result(response["content"])
                
                # Update task history
                task["history"].append({
                    "iteration": iteration + 1,
                    "agent": coordinator_agent["id"],
                    "action": "finalize",
                    "timestamp": datetime.utcnow().isoformat(),
                    "input": prompt,
                    "output": response["content"]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process with coordinator: {e}")
            traceback.print_exc()
            return {"error": str(e), "status": "failed"}
    
    async def _process_subtask(
        self,
        network: Dict[str, Any],
        agent_id: str,
        description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a subtask with a specialized agent using functional programming patterns"""
        # Import broadcast function here to avoid circular imports
        from ..routers.websocket_router import broadcast_task_update
        from ..utils.concurrent import CircuitBreaker, with_retry
        
        # Create or get circuit breaker for this agent
        circuit_breaker_name = f"agent_{agent_id}"
        if not hasattr(self, 'circuit_breakers'):
            self.circuit_breakers = {}
        
        if circuit_breaker_name not in self.circuit_breakers:
            self.circuit_breakers[circuit_breaker_name] = CircuitBreaker(
                name=circuit_breaker_name,
                failure_threshold=3,
                recovery_timeout=60.0
            )
        
        circuit_breaker = self.circuit_breakers[circuit_breaker_name]
        
        async def get_agent_safely():
            # Get agent with validation
            agent = await self._get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            return agent
        
        async def update_agent_status(agent, status, action=None):
            # Create new agent state with functional update pattern
            updated_agent = {
                **agent,
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Add last_action if provided
            if action:
                updated_agent["last_action"] = action
                
            # Save updated agent
            await self._save_agent(updated_agent)
            
            # Send real-time update for any tasks this agent is assigned to
            for task_id in updated_agent.get("assigned_tasks", []):
                await broadcast_task_update(
                    task_id=task_id,
                    update_type="agent_status_change",
                    data={
                        "agent_id": agent["id"],
                        "agent_type": agent["type"],
                        "status": status,
                        "action": action
                    }
                )
                
            return updated_agent
        
        async def generate_and_parse_response(agent, prompt):
            # Generate response with retry and circuit breaker
            async def generate_with_protection():
                return await self._generate_with_fallback(prompt=prompt, agent=agent)
            
            # Create fallback function for circuit breaker
            async def fallback_generation():
                logger.warning(f"Using fallback generation for agent {agent_id}")
                return {
                    "content": json.dumps({
                        "reasoning": "Failed to generate response due to service issues",
                        "result": f"Error: Agent {agent_id} is currently unavailable",
                        "confidence": 0.1,
                        "suggested_memories": []
                    })
                }
            
            # Execute with protection
            response = await circuit_breaker.execute(
                with_retry, 
                generate_with_protection,
                retry_count=2,
                fallback=fallback_generation
            )
            
            # Parse response
            return self._parse_agent_response(response["content"])
        
        # Find the task_id from context
        task_id = context.get("task_context", {}).get("task_id")
        
        # Main execution flow with proper error handling
        try:
            # Get agent
            agent = await get_agent_safely()
            
            # Update agent status to working
            agent = await update_agent_status(
                agent,
                "working",
                f"Processing subtask: {description[:50]}..."
            )
            
            # Send real-time subtask start notification
            if task_id:
                await broadcast_task_update(
                    task_id=task_id,
                    update_type="subtask_started",
                    data={
                        "subtask_description": description,
                        "agent_id": agent_id,
                        "agent_name": agent["name"],
                        "agent_type": agent["type"]
                    }
                )
            
            # Generate prompt
            prompt = self._generate_agent_prompt(agent, description, context)
            
            # Generate and parse response
            agent_response = await generate_and_parse_response(agent, prompt)
            
            # Update agent status to idle
            await update_agent_status(agent, "idle")
            
            # Send real-time subtask completion notification
            if task_id:
                await broadcast_task_update(
                    task_id=task_id,
                    update_type="subtask_completed",
                    data={
                        "subtask_description": description,
                        "agent_id": agent_id,
                        "agent_name": agent["name"],
                        "agent_type": agent["type"],
                        "result": agent_response
                    }
                )
            
            # Return successful response
            return agent_response
            
        except Exception as e:
            logger.error(f"Failed to process subtask: {e}")
            
            # Try to update agent status to error
            try:
                agent = await self._get_agent(agent_id)
                if agent:
                    await update_agent_status(agent, "error")
            except Exception as inner_e:
                logger.error(f"Failed to update agent status: {inner_e}")
            
            # Send subtask failure notification
            if task_id:
                await broadcast_task_update(
                    task_id=task_id,
                    update_type="subtask_failed",
                    data={
                        "subtask_description": description,
                        "agent_id": agent_id,
                        "error": str(e)
                    }
                )
            
            # Return error response
            return {
                "error": str(e),
                "status": "failed",
                "confidence": 0.0,
                "result": f"Error processing task: {str(e)}"
            }
    
    async def _generate_with_fallback(
        self,
        prompt: str,
        agent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate text with model fallback using functional programming patterns and retry mechanisms"""
        from ..utils.concurrent import with_retry
        import functools
        
        # Get parameters with defaults
        temperature = agent["parameters"].get("temperature", 0.7)
        max_tokens = agent["parameters"].get("max_tokens", 4000)
        
        # Create model chain starting with configured model
        model = agent["model"]
        model_chain = [model] + [m for m in MODEL_FALLBACK_CHAIN if m != model]
        
        # Create generation function for a specific model
        async def generate_with_model(model_name):
            start_time = time.time()
            try:
                response = await self.llm_client.generate_text(
                    prompt=prompt,
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                duration = time.time() - start_time
                logger.info(f"Generated response with {model_name} in {duration:.2f}s")
                
                # Add model metadata to response
                response["model_used"] = model_name
                response["generation_time"] = duration
                
                return response
            except Exception as e:
                duration = time.time() - start_time
                logger.warning(f"Failed to generate with {model_name} after {duration:.2f}s: {str(e)}")
                raise
        
        # Try each model in the chain with retry
        errors = []
        for model_name in model_chain:
            try:
                # Create retry function for this model
                retry_generate = functools.partial(
                    with_retry,
                    generate_with_model,
                    model_name,
                    retry_count=1,  # Only retry once per model before moving to next
                    initial_backoff=1.0,
                    jitter=True
                )
                
                # Attempt generation with this model
                return await retry_generate()
                
            except Exception as e:
                # Record error and continue to next model
                errors.append(f"{model_name}: {str(e)}")
                continue
        
        # If we get here, all models failed
        error_details = "\n".join(errors)
        logger.error(f"All models failed for agent {agent['id']}:\n{error_details}")
        
        # Return a minimal fallback response
        fallback_response = {
            "content": json.dumps({
                "reasoning": "All model attempts failed",
                "result": "Error: Unable to generate content",
                "confidence": 0.0
            }),
            "model_used": "fallback",
            "generation_time": 0,
            "error": error_details
        }
        
        # Decide whether to raise an exception or return the fallback
        # We'll return the fallback for graceful degradation
        return fallback_response
    
    def _generate_coordinator_prompt(self, agent: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate prompt for coordinator agent"""
        prompt = f"""
You are {agent['name']}, a coordinator agent in the AI Mesh Network "{context['network_name']}".
Your role is to coordinate a network of specialized AI agents to solve complex tasks.

# CURRENT TASK
{context['task']}

# TASK CONTEXT
{json.dumps(context['task_context'], indent=2)}

# AVAILABLE AGENTS
{json.dumps(context['available_agents'], indent=2)}

# SHARED MEMORY
{json.dumps(context['shared_memory'], indent=2)}

# ITERATION INFORMATION
Current iteration: {context['iteration']} of {context['max_iterations']}

{
    "subtask_results" in context and 
    f"# PREVIOUS SUBTASK RESULTS\n{json.dumps(context['subtask_results'], indent=2)}" or 
    "# PREVIOUS SUBTASK RESULTS\nNone yet."
}

# INSTRUCTIONS
1. Analyze the current task and its context.
2. Decide if the task is complete based on the work done so far.
3. If the task is not complete:
   - Break down the task into subtasks for specialized agents.
   - Assign each subtask to the most appropriate agent based on their capabilities.
   - Add any important information to shared memory.
4. If the task is complete:
   - Provide the final result.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "task_complete": boolean,
  "reasoning": "Your step-by-step reasoning about the current state and decisions",
  "subtasks": [
    {{
      "agent_id": "ID of the agent to assign the subtask to",
      "description": "Detailed description of the subtask"
    }}
  ],
  "new_memories": [
    {{
      "type": "fact|context|decision|feedback",
      "content": "Content of the memory item",
      "confidence": float between 0 and 1
    }}
  ],
  "result": {{
    // Only include if task_complete is true
    "content": "Final result content",
    "confidence": float between 0 and 1,
    "explanation": "Explanation of the result"
  }}
}}
```

Respond only with the JSON object, no additional text.
"""
        return prompt
    
    def _generate_agent_prompt(
        self,
        agent: Dict[str, Any],
        subtask: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate prompt for specialized agent"""
        prompt = f"""
You are {agent['name']}, a specialized {agent['type']} agent in the AI Mesh Network "{context['network_name']}".
{agent['description']}

# YOUR CAPABILITIES
{json.dumps(agent['capabilities'], indent=2)}

# SUBTASK
{subtask}

# MAIN TASK CONTEXT
{context['task']}
{json.dumps(context['task_context'], indent=2)}

# SHARED MEMORY
{json.dumps(context['shared_memory'], indent=2)}

# INSTRUCTIONS
1. Analyze the subtask in the context of the main task.
2. Use your specialized capabilities to complete the subtask.
3. Provide a detailed response that addresses the subtask requirements.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your step-by-step reasoning about the subtask",
  "result": "Your detailed response to the subtask",
  "confidence": float between 0 and 1,
  "suggested_memories": [
    {{
      "type": "fact|context|decision|feedback",
      "content": "Content of the suggested memory item",
      "confidence": float between 0 and 1
    }}
  ]
}}
```

Respond only with the JSON object, no additional text.
"""
        return prompt
    
    def _generate_final_result_prompt(self, agent: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate prompt for final result"""
        prompt = f"""
You are {agent['name']}, a coordinator agent in the AI Mesh Network "{context['network_name']}".
Your role is to synthesize the results of multiple subtasks into a final result.

# ORIGINAL TASK
{context['task']}

# TASK CONTEXT
{json.dumps(context['task_context'], indent=2)}

# SUBTASK RESULTS
{json.dumps(context['subtask_results'], indent=2)}

# SHARED MEMORY
{json.dumps(context['shared_memory'], indent=2)}

# INSTRUCTIONS
1. Analyze all the subtask results and shared memory.
2. Synthesize a comprehensive final result that addresses the original task.
3. Provide a confidence score for the final result.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "content": "Comprehensive final result that addresses the original task",
  "confidence": float between 0 and 1,
  "explanation": "Explanation of how the final result was synthesized from the subtask results"
}}
```

Respond only with the JSON object, no additional text.
"""
        return prompt
    
    def _parse_coordinator_response(self, response: str) -> Dict[str, Any]:
        """Parse response from coordinator agent"""
        try:
            # Extract JSON from response
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str.split("```json")[1]
            if json_str.endswith("```"):
                json_str = json_str.split("```")[0]
            
            # Parse JSON
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Failed to parse coordinator response: {e}")
            logger.error(f"Response: {response}")
            
            # Return default response
            return {
                "task_complete": False,
                "reasoning": "Failed to parse response",
                "subtasks": [],
                "new_memories": []
            }
    
    def _parse_agent_response(self, response: str) -> Dict[str, Any]:
        """Parse response from specialized agent"""
        try:
            # Extract JSON from response
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str.split("```json")[1]
            if json_str.endswith("```"):
                json_str = json_str.split("```")[0]
            
            # Parse JSON
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Failed to parse agent response: {e}")
            logger.error(f"Response: {response}")
            
            # Return default response
            return {
                "reasoning": "Failed to parse response",
                "result": "Error: Failed to parse agent response",
                "confidence": 0.0,
                "suggested_memories": []
            }
    
    def _parse_final_result(self, response: str) -> Dict[str, Any]:
        """Parse final result from coordinator agent"""
        try:
            # Extract JSON from response
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str.split("```json")[1]
            if json_str.endswith("```"):
                json_str = json_str.split("```")[0]
            
            # Parse JSON
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Failed to parse final result: {e}")
            logger.error(f"Response: {response}")
            
            # Return default response
            return {
                "content": "Error: Failed to generate final result",
                "confidence": 0.0,
                "explanation": "Failed to parse response"
            }
    
    async def _get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent details from Redis"""
        try:
            # Check if agent is in memory
            if agent_id in self.agent_instances:
                return self.agent_instances[agent_id]
            
            # Get agent from Redis
            agent_key = f"{AGENT_KEY_PREFIX}{agent_id}"
            agent_data = await self.redis.get(agent_key)
            
            if not agent_data:
                return None
            
            agent = json.loads(agent_data)
            
            # Cache agent
            self.agent_instances[agent_id] = agent
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to get agent: {e}")
            return None
    
    async def _save_agent(self, agent: Dict[str, Any]) -> bool:
        """Save agent to Redis"""
        try:
            # Update agent in Redis
            agent_key = f"{AGENT_KEY_PREFIX}{agent['id']}"
            await self.redis.set(agent_key, json.dumps(agent))
            
            # Update agent in memory
            self.agent_instances[agent['id']] = agent
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save agent: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task details"""
        try:
            # Check if task is in memory
            if task_id in self.active_tasks:
                return self.active_tasks[task_id]
            
            # Get task from Redis
            task_key = f"{TASK_KEY_PREFIX}{task_id}"
            task_data = await self.redis.get(task_key)
            
            if not task_data:
                return None
            
            task = json.loads(task_data)
            
            # Cache task
            self.active_tasks[task_id] = task
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to get task: {e}")
            return None
    
    async def _save_task(self, task: Dict[str, Any]) -> bool:
        """Save task to Redis"""
        try:
            # Update task in Redis
            task_key = f"{TASK_KEY_PREFIX}{task['id']}"
            await self.redis.set(task_key, json.dumps(task))
            
            # Update task in memory
            self.active_tasks[task['id']] = task
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save task: {e}")
            return False
    
    async def _get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get memory item from Redis"""
        try:
            # Get memory from Redis
            memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
            memory_data = await self.redis.get(memory_key)
            
            if not memory_data:
                return None
            
            return json.loads(memory_data)
            
        except Exception as e:
            logger.error(f"Failed to get memory: {e}")
            return None
    
    async def add_memory(
        self,
        network_id: str,
        content: str,
        memory_type: str = "fact",
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        use_vector_embedding: bool = True
    ) -> str:
        """
        Add a memory item to the shared memory
        
        Args:
            network_id: ID of the network
            content: Memory content
            memory_type: Type of memory (fact, context, decision, feedback)
            confidence: Confidence score (0.0 to 1.0)
            metadata: Additional metadata for the memory
            use_vector_embedding: Whether to generate vector embedding for semantic search
        
        Returns:
            Memory ID if successful
        
        Raises:
            ValueError: If network not found
            Exception: For other errors
        """
        try:
            # Check if network exists
            network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
            network_data = await self.redis.get(network_key)
            
            if not network_data:
                raise ValueError(f"Network {network_id} not found")
            
            network = json.loads(network_data)
            
            # Generate memory ID
            memory_id = f"memory_{uuid.uuid4().hex[:8]}"
            
            # Get vector embedding if enabled
            vector_embedding = None
            if use_vector_embedding:
                try:
                    # Import vector embedding service here to avoid circular imports
                    from ..implementations.memory.vector_embeddings import get_vector_embedding_service
                    vector_service = get_vector_embedding_service()
                    
                    # Generate embedding
                    embedding_result = await vector_service.get_embedding(content)
                    vector_embedding = embedding_result.get("embedding")
                except Exception as ve:
                    logger.error(f"Error generating vector embedding: {ve}")
                    # Continue even if vector embedding fails
            
            # Use tiered memory storage
            tiered_memory = await get_tiered_memory_storage()
            
            # Store memory in tiered storage
            store_result = await tiered_memory.store_memory(
                memory_id=memory_id,
                network_id=network_id,
                content=content,
                memory_type=memory_type,
                confidence=confidence,
                metadata=metadata or {},
                vector_embedding=vector_embedding
            )
            
            if not store_result:
                raise Exception("Failed to store memory in tiered storage")
            
            # Update network memories reference list
            network["memories"].append(memory_id)
            network["updated_at"] = datetime.utcnow().isoformat()
            await self.redis.set(network_key, json.dumps(network))
            
            # Add to memory indexing system for keyword-based search
            try:
                # Import memory indexing system here to avoid circular imports
                from ..implementations.memory.memory_indexing import get_memory_indexing_system
                memory_indexing = get_memory_indexing_system()
                
                # Index memory for keyword-based retrieval
                await memory_indexing.add_memory_to_index(
                    network_id=network_id,
                    memory_id=memory_id,
                    memory_type=memory_type,
                    content=content,
                    metadata=metadata or {}
                )
            except Exception as indexing_error:
                logger.error(f"Error indexing memory: {indexing_error}")
                # Continue even if indexing fails
            
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise
    
    async def get_network_memory(
        self,
        network_id: str,
        memory_type: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 50,
        search_mode: str = "semantic"  # Options: semantic, keyword, hybrid
    ) -> List[Dict[str, Any]]:
        """
        Get shared memory for a network with enhanced search capabilities
        
        Args:
            network_id: ID of the network
            memory_type: Optional filter by memory type
            query: Search query for filtering memories
            limit: Maximum number of results
            search_mode: Search method (semantic, keyword, or hybrid)
            
        Returns:
            List of memory items matching the criteria
        """
        try:
            # Get tiered memory storage
            tiered_memory = await get_tiered_memory_storage()
            
            # If no query, just get all memories by network
            if not query:
                return await tiered_memory.get_network_memories(
                    network_id=network_id,
                    memory_type=memory_type,
                    limit=limit
                )
            
            # Apply rate limiting for search operations
            rate_limiter = await get_rate_limiter()
            # Define rate limit key based on network ID and search mode
            rate_limit_key = f"memory_search:{network_id}:{search_mode}"
            
            # Check rate limit with appropriate parameters for different search modes
            if search_mode == "semantic":
                # Semantic search is more expensive - stricter limits
                allowed, info = await rate_limiter.check_rate_limit(
                    rate_limit_key, 
                    tokens=3,  # Each semantic search consumes 3 tokens 
                    capacity=30,  # Maximum 30 tokens in bucket
                    refill_rate=5,  # Refill 5 tokens per interval
                    refill_interval_seconds=60  # Interval is 1 minute
                )
            else:
                # Keyword search is less expensive
                allowed, info = await rate_limiter.check_rate_limit(
                    rate_limit_key,
                    tokens=1,  # Each keyword search consumes 1 token
                    capacity=60,  # Maximum 60 tokens in bucket
                    refill_rate=10,  # Refill 10 tokens per interval
                    refill_interval_seconds=60  # Interval is 1 minute
                )
            
            # If rate limited and wait time is short, wait automatically
            if not allowed and info.get("wait_time_seconds", 0) < 3:
                # Small wait time, just wait automatically
                await asyncio.sleep(info.get("wait_time_seconds", 1))
                allowed = True
            elif not allowed:
                # Too many requests
                logger.warning(f"Rate limit exceeded for memory search: {info}")
                return [
                    {
                        "id": "rate_limited",
                        "network_id": network_id,
                        "type": "system",
                        "content": f"Rate limit exceeded. Please try again in {info.get('wait_time_seconds', 60)} seconds.",
                        "confidence": 1.0,
                        "created_at": datetime.utcnow().isoformat(),
                        "is_rate_limited": True
                    }
                ]
            
            # For search with query, we need vector embedding for semantic search
            vector_embedding = None
            if search_mode in ["semantic", "hybrid"]:
                try:
                    from ..implementations.memory.vector_embeddings import get_vector_embedding_service
                    vector_service = get_vector_embedding_service()
                    embedding_result = await vector_service.get_embedding(query)
                    vector_embedding = embedding_result.get("embedding")
                except Exception as e:
                    logger.error(f"Failed to generate vector embedding: {e}")
                    # Continue without vector embedding
            
            # Search memories using tiered storage
            return await tiered_memory.search_memories(
                network_id=network_id,
                query=query,
                memory_type=memory_type,
                vector_embedding=vector_embedding,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Failed to get network memory: {e}")
            traceback.print_exc()
            return []
    
    async def get_network_agents(self, network_id: str) -> List[Dict[str, Any]]:
        """Get agents for a network using pipelined Redis operations"""
        try:
            # Get network
            network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
            network_data = await self.redis.get(network_key)
            
            if not network_data:
                return []
            
            network = json.loads(network_data)
            
            # If no agents, return empty list
            if not network["agents"]:
                return []
                
            # Check cache first for each agent
            agents = []
            missing_agent_ids = []
            
            for agent_id in network["agents"]:
                if agent_id in self.agent_instances:
                    # Get from cache
                    agent, _ = self.agent_instances[agent_id]
                    agents.append(agent)
                else:
                    # Need to fetch from Redis
                    missing_agent_ids.append(agent_id)
            
            # If all agents were in cache, return them
            if not missing_agent_ids:
                return agents
                
            # Create Redis pipeline for missing agents
            pipeline = self.redis.pipeline()
            
            # Add all agent gets to the pipeline
            agent_keys = []
            for agent_id in missing_agent_ids:
                agent_key = f"{AGENT_KEY_PREFIX}{agent_id}"
                agent_keys.append((agent_id, agent_key))
                pipeline.get(agent_key)
            
            # Execute pipeline to get all agents in a single Redis operation
            agent_values = await pipeline.execute()
            
            # Process the results
            current_time = time.time()
            for i, data in enumerate(agent_values):
                if not data:
                    continue
                    
                agent = json.loads(data)
                agent_id = missing_agent_ids[i]
                
                # Add to results
                agents.append(agent)
                
                # Update cache
                self.agent_instances[agent_id] = (agent, current_time)
            
            return agents
            
        except Exception as e:
            logger.error(f"Failed to get network agents: {e}")
            traceback.print_exc()
            return []
    
    async def list_network_tasks(
        self,
        network_id: str,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List tasks for a network using pipelined Redis operations"""
        try:
            # Get network
            network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
            network_data = await self.redis.get(network_key)
            
            if not network_data:
                return []
            
            network = json.loads(network_data)
            
            # If no tasks, return empty list
            if not network["tasks"]:
                return []
                
            # Create Redis pipeline
            pipeline = self.redis.pipeline()
            
            # Add all task gets to the pipeline
            task_keys = []
            for task_id in network["tasks"]:
                task_key = f"{TASK_KEY_PREFIX}{task_id}"
                task_keys.append((task_id, task_key))
                pipeline.get(task_key)
            
            # Execute pipeline to get all tasks in a single Redis operation
            task_values = await pipeline.execute()
            
            # Process the results
            tasks = []
            for i, data in enumerate(task_values):
                if not data:
                    continue
                    
                task = json.loads(data)
                
                # Filter by status if specified
                if status and task["status"] != status:
                    continue
                
                tasks.append(task)
            
            # Sort by creation time (newest first)
            tasks.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Apply pagination
            return tasks[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to list network tasks: {e}")
            traceback.print_exc()
            return []
    
    async def add_agent_to_network(
        self,
        network_id: str,
        agent_config: Dict[str, Any]
    ) -> str:
        """Add an agent to a network"""
        try:
            # Check if network exists
            network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
            network_data = await self.redis.get(network_key)
            
            if not network_data:
                raise ValueError(f"Network {network_id} not found")
            
            network = json.loads(network_data)
            
            # Create agent
            agent_id = await self._create_agent(network_id, agent_config)
            
            # Update network agents
            network["agents"].append(agent_id)
            network["updated_at"] = datetime.utcnow().isoformat()
            await self.redis.set(network_key, json.dumps(network))
            
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to add agent to network: {e}")
            raise
    
    async def remove_agent_from_network(
        self,
        network_id: str,
        agent_id: str
    ) -> bool:
        """Remove an agent from a network"""
        try:
            # Check if network exists
            network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
            network_data = await self.redis.get(network_key)
            
            if not network_data:
                return False
            
            network = json.loads(network_data)
            
            # Check if agent exists in network
            if agent_id not in network["agents"]:
                return False
            
            # Remove agent from network
            network["agents"].remove(agent_id)
            network["updated_at"] = datetime.utcnow().isoformat()
            await self.redis.set(network_key, json.dumps(network))
            
            # Delete agent
            agent_key = f"{AGENT_KEY_PREFIX}{agent_id}"
            await self.redis.delete(agent_key)
            
            # Remove from memory
            if agent_id in self.agent_instances:
                del self.agent_instances[agent_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove agent from network: {e}")
            return False
    
    # Security API Key Management Methods
    async def create_api_key(
        self,
        user_id: str,
        role: str = "user",
        scopes: Optional[List[str]] = None,
        admin_user_id: Optional[str] = None,
        admin_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an API key for a user
        
        Args:
            user_id: User ID to create API key for
            role: Role for the API key (user, admin, service)
            scopes: List of permission scopes
            admin_user_id: Admin user ID making the request
            admin_api_key: Admin API key for authorization
            
        Returns:
            Dictionary with API key information
            
        Raises:
            PermissionError: If admin authentication fails
        """
        # If admin key provided, verify admin has permission
        if admin_api_key:
            credential = await self.security_manager.verify_api_key(admin_api_key)
            if not credential:
                await self.audit_manager.log_operation(
                    user_id=admin_user_id or "unknown",
                    action="create_api_key",
                    resource_type="api_key",
                    resource_id=user_id,
                    operation="create",
                    status="failed",
                    details={"error": "Invalid admin API key"}
                )
                raise PermissionError("Invalid admin API key")
            
            # Verify admin has permission to create API keys
            if "admin" not in credential.scopes:
                await self.audit_manager.log_operation(
                    user_id=credential.user_id,
                    action="create_api_key",
                    resource_type="api_key",
                    resource_id=user_id,
                    operation="create",
                    status="failed",
                    details={"error": "Insufficient permissions"}
                )
                raise PermissionError("Admin permission required to create API keys")
            
            # Use authenticated admin ID
            admin_user_id = credential.user_id
        
        # Create the API key
        api_key_info = await self.security_manager.create_api_credential(
            user_id=user_id,
            role=role,
            scopes=scopes
        )
        
        # Log API key creation
        await self.audit_manager.log_operation(
            user_id=admin_user_id or "system",
            action="create_api_key",
            resource_type="api_key",
            resource_id=user_id,
            operation="create",
            status="success",
            details={
                "user_id": user_id,
                "role": role,
                "scopes": scopes or [],
                "api_key_prefix": api_key_info["api_key"][:12] + "..." if api_key_info else "unknown"
            }
        )
        
        return api_key_info
    
    async def revoke_api_key(
        self,
        api_key: str,
        admin_user_id: Optional[str] = None,
        admin_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Revoke an API key
        
        Args:
            api_key: API key to revoke
            admin_user_id: Admin user ID making the request
            admin_api_key: Admin API key for authorization
            
        Returns:
            Dictionary with revocation status
            
        Raises:
            PermissionError: If admin authentication fails
        """
        # If admin key provided, verify admin has permission
        if admin_api_key:
            credential = await self.security_manager.verify_api_key(admin_api_key)
            if not credential:
                await self.audit_manager.log_operation(
                    user_id=admin_user_id or "unknown",
                    action="revoke_api_key",
                    resource_type="api_key",
                    resource_id=api_key[:12] + "...",
                    operation="revoke",
                    status="failed",
                    details={"error": "Invalid admin API key"}
                )
                raise PermissionError("Invalid admin API key")
            
            # Verify admin has permission to revoke API keys
            if "admin" not in credential.scopes:
                await self.audit_manager.log_operation(
                    user_id=credential.user_id,
                    action="revoke_api_key",
                    resource_type="api_key",
                    resource_id=api_key[:12] + "...",
                    operation="revoke",
                    status="failed",
                    details={"error": "Insufficient permissions"}
                )
                raise PermissionError("Admin permission required to revoke API keys")
            
            # Use authenticated admin ID
            admin_user_id = credential.user_id
        
        # Get target API key information before revocation
        target_credential = await self.security_manager.verify_api_key(api_key)
        target_user_id = target_credential.user_id if target_credential else "unknown"
        
        # Revoke the API key
        success = await self.security_manager.revoke_api_key(api_key)
        
        # Log API key revocation
        status = "success" if success else "failed"
        await self.audit_manager.log_operation(
            user_id=admin_user_id or "system",
            action="revoke_api_key",
            resource_type="api_key",
            resource_id=api_key[:12] + "...",
            operation="revoke",
            status=status,
            details={
                "target_user_id": target_user_id,
                "success": success
            }
        )
        
        return {
            "status": status,
            "revoked": success,
            "target_user_id": target_user_id,
            "revoked_at": datetime.utcnow().isoformat()
        }
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        admin_user_id: Optional[str] = None,
        admin_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get audit logs with filtering
        
        Args:
            user_id: Filter by user ID
            resource_type: Filter by resource type
            action: Filter by action
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            offset: Offset for pagination
            admin_user_id: Admin user ID making the request
            admin_api_key: Admin API key for authorization
            
        Returns:
            Dictionary with audit logs and metadata
            
        Raises:
            PermissionError: If admin authentication fails
        """
        # If admin key provided, verify admin has permission
        if admin_api_key:
            credential = await self.security_manager.verify_api_key(admin_api_key)
            if not credential:
                await self.audit_manager.log_operation(
                    user_id=admin_user_id or "unknown",
                    action="get_audit_logs",
                    resource_type="audit_logs",
                    resource_id="query",
                    operation="read",
                    status="failed",
                    details={"error": "Invalid admin API key"}
                )
                raise PermissionError("Invalid admin API key")
            
            # Verify admin has permission to view audit logs
            if "admin" not in credential.scopes:
                await self.audit_manager.log_operation(
                    user_id=credential.user_id,
                    action="get_audit_logs",
                    resource_type="audit_logs",
                    resource_id="query",
                    operation="read",
                    status="failed",
                    details={"error": "Insufficient permissions"}
                )
                raise PermissionError("Admin permission required to view audit logs")
            
            # Use authenticated admin ID
            admin_user_id = credential.user_id
        
        # Get audit logs
        logs = await self.audit_manager.get_audit_logs(
            user_id=user_id,
            resource_type=resource_type,
            action=action,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        
        # Log audit log query
        await self.audit_manager.log_operation(
            user_id=admin_user_id or "system",
            action="get_audit_logs",
            resource_type="audit_logs",
            resource_id="query",
            operation="read",
            status="success",
            details={
                "user_id_filter": user_id,
                "resource_type_filter": resource_type,
                "action_filter": action,
                "limit": limit,
                "offset": offset,
                "result_count": len(logs)
            }
        )
        
        return {
            "logs": logs,
            "count": len(logs),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def set_data_retention_policy(
        self,
        retention_days: int,
        admin_user_id: Optional[str] = None,
        admin_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set data retention policy
        
        Args:
            retention_days: Retention period in days
            admin_user_id: Admin user ID making the request
            admin_api_key: Admin API key for authorization
            
        Returns:
            Dictionary with retention policy information
            
        Raises:
            PermissionError: If admin authentication fails
            ValueError: If retention days is invalid
        """
        # Validate retention days
        if retention_days < 1 or retention_days > 365 * 2:  # Max 2 years
            raise ValueError("Retention days must be between 1 and 730")
        
        # If admin key provided, verify admin has permission
        if admin_api_key:
            credential = await self.security_manager.verify_api_key(admin_api_key)
            if not credential:
                await self.audit_manager.log_operation(
                    user_id=admin_user_id or "unknown",
                    action="set_retention_policy",
                    resource_type="system",
                    resource_id="retention_policy",
                    operation="update",
                    status="failed",
                    details={"error": "Invalid admin API key"}
                )
                raise PermissionError("Invalid admin API key")
            
            # Verify admin has permission to set retention policy
            if "admin" not in credential.scopes:
                await self.audit_manager.log_operation(
                    user_id=credential.user_id,
                    action="set_retention_policy",
                    resource_type="system",
                    resource_id="retention_policy",
                    operation="update",
                    status="failed",
                    details={"error": "Insufficient permissions"}
                )
                raise PermissionError("Admin permission required to set retention policy")
            
            # Use authenticated admin ID
            admin_user_id = credential.user_id
        
        # Get old policy for auditing
        old_policy = await self.data_retention_manager.get_retention_policy()
        
        # Set retention policy
        await self.data_retention_manager.set_retention_policy(retention_days)
        
        # Log retention policy update
        await self.audit_manager.log_operation(
            user_id=admin_user_id or "system",
            action="set_retention_policy",
            resource_type="system",
            resource_id="retention_policy",
            operation="update",
            status="success",
            details={
                "old_retention_days": old_policy,
                "new_retention_days": retention_days
            }
        )
        
        return {
            "status": "success",
            "old_retention_days": old_policy,
            "new_retention_days": retention_days,
            "updated_at": datetime.utcnow().isoformat()
        }

    async def check_health(self) -> Dict[str, Any]:
        """Check health of the AI Mesh Network service with detailed diagnostics"""
        try:
            health_start_time = time.time()
            results = {}
            errors = []
            
            # Check Redis connection with timeout
            try:
                redis_start = time.time()
                redis_ping = await asyncio.wait_for(self.redis.ping(), timeout=2.0)
                redis_latency = time.time() - redis_start
                results["redis"] = {
                    "status": "healthy" if redis_ping else "degraded",
                    "latency_ms": int(redis_latency * 1000)
                }
            except Exception as e:
                errors.append(f"Redis error: {str(e)}")
                results["redis"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # Check LLM client
            try:
                llm_start = time.time()
                llm_health = await asyncio.wait_for(self.llm_client.check_health(), timeout=5.0)
                llm_latency = time.time() - llm_start
                results["llm_client"] = {
                    "status": "healthy",
                    "latency_ms": int(llm_latency * 1000),
                    **llm_health
                }
            except Exception as e:
                errors.append(f"LLM client error: {str(e)}")
                results["llm_client"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # Check security components
            try:
                # Check security manager
                security_test_key = await self.security_manager.generate_api_key("health_check_user")
                results["security_manager"] = {
                    "status": "healthy",
                    "test_key_generated": security_test_key is not None
                }
            except Exception as e:
                errors.append(f"Security manager error: {str(e)}")
                results["security_manager"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # Check circuit breakers if available
            if hasattr(self, 'circuit_breakers'):
                circuit_breaker_stats = {
                    name: breaker.get_stats() 
                    for name, breaker in self.circuit_breakers.items()
                }
                results["circuit_breakers"] = circuit_breaker_stats
            
            # Use a more efficient approach with a single pipeline instead of multiple keys commands
            try:
                # Create a pipeline for all Redis operations
                pipeline = self.redis.pipeline()
                
                # Add key counting operations to pipeline
                prefixes = [
                    NETWORK_KEY_PREFIX, TASK_KEY_PREFIX, AGENT_KEY_PREFIX, 
                    MEMORY_KEY_PREFIX, AUDIT_LOG_KEY_PREFIX, TOKEN_KEY_PREFIX
                ]
                for prefix in prefixes:
                    pipeline.keys(f"{prefix}*")
                
                # Also add memory info to the same pipeline
                pipeline.info("memory")
                
                # Execute all commands in a single round-trip with timeout
                all_results = await asyncio.wait_for(pipeline.execute(), timeout=3.0)
                
                # Extract entity counts (all but last result)
                count_results = [len(keys) for keys in all_results[:-1]]
                
                # Extract memory info (last result)
                memory_info = all_results[-1]
                
                # Map count results to named operations
                count_ops_names = ['networks', 'tasks', 'agents', 'memories', 'audit_logs', 'tokens']
                
            except Exception as e:
                logger.error(f"Failed to execute Redis pipeline: {e}")
                errors.append(f"Redis pipeline error: {str(e)}")
                count_results = [-1] * len(prefixes)
                memory_info = {}
                count_ops_names = ['networks', 'tasks', 'agents', 'memories', 'audit_logs', 'tokens']
            
            # Process counts
            entity_counts = {}
            for i, name in enumerate(count_ops_names):
                result = count_results[i] if i < len(count_results) else -1
                if result == -1:
                    entity_counts[name] = {
                        "status": "error",
                        "error": "Failed to retrieve count"
                    }
                else:
                    entity_counts[name] = {
                        "count": result,
                        "status": "ok"
                    }
            
            results["entity_counts"] = entity_counts
            
            # Process memory usage information (already retrieved in the pipeline)
            if memory_info:
                results["memory_usage"] = {
                    "used_memory_human": memory_info.get("used_memory_human", "unknown"),
                    "used_memory_peak_human": memory_info.get("used_memory_peak_human", "unknown"),
                    "total_system_memory_human": memory_info.get("total_system_memory_human", "unknown")
                }
            else:
                errors.append("Failed to get memory info")
            
            # Calculate overall health status
            overall_status = "healthy"
            
            if results.get("redis", {}).get("status") != "healthy":
                overall_status = "unhealthy"  # Redis is critical
            elif results.get("llm_client", {}).get("status") != "healthy":
                overall_status = "degraded"   # LLM issues are degraded not unhealthy
            elif results.get("security_manager", {}).get("status") != "healthy":
                overall_status = "degraded"   # Security manager issues are degraded
            elif errors:
                overall_status = "degraded"   # Non-critical errors mean degraded
            
            # Calculate health check duration
            health_duration = time.time() - health_start_time
            
            # Final health check response
            health_response = {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": int(health_duration * 1000),
                "services": results,
                "errors": errors if errors else None,
                "instance_id": id(self),  # For debugging load balancing
                "version": "2.0.0"  # Add version information
            }
            
            # Log health check to audit log
            await self.audit_manager.log_operation(
                user_id="system",
                action="health_check",
                resource_type="system",
                resource_id="health",
                operation="read",
                status=overall_status,
                details={
                    "duration_ms": int(health_duration * 1000),
                    "status": overall_status,
                    "error_count": len(errors) if errors else 0
                }
            )
            
            return health_response
            
        except Exception as e:
            logger.error(f"Health check failed with critical error: {e}")
            traceback.print_exc()
            
            # Try to log to audit log even in error case
            try:
                await self.audit_manager.log_operation(
                    user_id="system",
                    action="health_check",
                    resource_type="system",
                    resource_id="health",
                    operation="read",
                    status="critical",
                    details={"error": str(e)}
                )
            except:
                pass  # Ignore errors in error handler
                
            return {
                "status": "critical",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Singleton instance
_agent_coordinator_instance = None

def get_agent_coordinator() -> AgentCoordinator:
    """Get the singleton instance of AgentCoordinator"""
    global _agent_coordinator_instance
    if _agent_coordinator_instance is None:
        _agent_coordinator_instance = AgentCoordinator()
    return _agent_coordinator_instance
