"""
Agent Coordinator Service for AI Mesh Network

This service coordinates a network of specialized AI agents with shared memory and dynamic task delegation.
"""

import json
import logging
import uuid
import asyncio
import time
import functools
import traceback
from typing import Dict, Any, List, Optional, Tuple, Union, Callable, TypeVar, Awaitable
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import random

from ..utils.redis_client import get_redis_client
from ..utils.llm_client import get_llm_client, LLMClient
# Import the broadcast functions - will be imported later after they're defined
# to avoid circular imports

logger = logging.getLogger("ai_service.services.agent_coordinator")

# Constants
NETWORK_KEY_PREFIX = "ai_mesh:network:"
AGENT_KEY_PREFIX = "ai_mesh:agent:"
TASK_KEY_PREFIX = "ai_mesh:task:"
MEMORY_KEY_PREFIX = "ai_mesh:memory:"
AGENT_TYPES = ["content", "design", "analytics", "personalization", "coordinator", "research", "critic"]
MODEL_FALLBACK_CHAIN = ["claude-3-7-sonnet", "gpt-4o", "gemini-2.0"]

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
        
        # Start background task for cache cleanup
        asyncio.create_task(self._cache_cleanup_task())
        
    async def create_network(
        self,
        name: str,
        description: Optional[str] = None,
        agents: Optional[List[Dict[str, Any]]] = None,
        shared_context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10,
        timeout_seconds: int = 300
    ) -> str:
        """Create a new AI Mesh Network"""
        try:
            # Generate network ID
            network_id = f"network_{uuid.uuid4().hex[:8]}"
            
            # Create network object
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
                "memories": []
            }
            
            # Add agents if provided
            if agents:
                for agent_config in agents:
                    agent_id = await self._create_agent(network_id, agent_config)
                    network["agents"].append(agent_id)
            else:
                # Create default agents if none provided
                await self._create_default_agents(network_id, network)
            
            # Store network in Redis
            network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
            await self.redis.set(network_key, json.dumps(network))
            
            # Add to active networks
            self.active_networks[network_id] = network
            
            return network_id
            
        except Exception as e:
            logger.error(f"Failed to create network: {e}")
            traceback.print_exc()
            raise
    
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
        deadline: Optional[datetime] = None
    ) -> str:
        """Submit a task to an AI Mesh Network"""
        try:
            # Check if network exists
            network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
            network_data = await self.redis.get(network_key)
            
            if not network_data:
                raise ValueError(f"Network {network_id} not found")
            
            network = json.loads(network_data)
            
            # Generate task ID
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            
            # Create task object
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
                "history": []
            }
            
            # Store task in Redis
            task_key = f"{TASK_KEY_PREFIX}{task_id}"
            await self.redis.set(task_key, json.dumps(task_obj))
            
            # Update network tasks
            network["tasks"].append(task_id)
            network["updated_at"] = datetime.utcnow().isoformat()
            await self.redis.set(network_key, json.dumps(network))
            
            # Add to active tasks
            self.active_tasks[task_id] = task_obj
            
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise
    
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
        
    async def process_task(self, network_id: str, task_id: str):
        """Process a task in the AI Mesh Network using functional programming patterns"""
        # Import broadcast functions here to avoid circular imports
        from ..routers.websocket_router import broadcast_task_update, broadcast_network_update
        
        coordinator_agent = None
        
        try:
            # Validate task and network
            task, network = await self._validate_task_and_network(network_id, task_id)
            if not task or not network:
                return
            
            # Find coordinator agent with functional approach
            coordinator_agent = next(
                (agent for agent in network["agents"] if agent["type"] == "coordinator"), 
                None
            )
            
            if not coordinator_agent:
                logger.error(f"No coordinator agent found in network {network_id}")
                await self._mark_task_failed(task_id)
                
                # Send failure notification via WebSocket
                await broadcast_task_update(
                    task_id=task_id,
                    update_type="task_failed",
                    data={"error": "No coordinator agent found in network"}
                )
                return
            
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
            
            # Process task with coordinator agent
            result = await self._process_with_coordinator(network, coordinator_agent, task)
            
            # Complete task
            await self._complete_task(task, coordinator_agent, result)
            
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
            
        except Exception as e:
            logger.error(f"Failed to process task: {e}")
            traceback.print_exc()
            
            # Mark task as failed with coordinator agent information if available
            await self._mark_task_failed(task_id, coordinator_agent)
            
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
            
            # Create memory object
            memory = {
                "id": memory_id,
                "network_id": network_id,
                "type": memory_type,
                "content": content,
                "confidence": confidence,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store memory in Redis
            memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
            await self.redis.set(memory_key, json.dumps(memory))
            
            # Update network memories
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
            
            # Generate and store vector embedding if enabled
            if use_vector_embedding:
                try:
                    # Import vector embedding service here to avoid circular imports
                    from ..implementations.memory.vector_embeddings import get_vector_embedding_service
                    vector_service = get_vector_embedding_service()
                    
                    # Index the memory with vector embedding
                    await vector_service.index_memory_item(
                        network_id=network_id,
                        memory_id=memory_id,
                        content=content,
                        metadata=metadata
                    )
                except Exception as ve:
                    logger.error(f"Error generating vector embedding: {ve}")
                    # Continue even if vector embedding fails
            
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
            # If no query, just get all memories sorted by recency
            if not query:
                # Get network
                network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
                network_data = await self.redis.get(network_key)
                
                if not network_data:
                    return []
                
                network = json.loads(network_data)
                
                # If no memories, return empty list
                if not network["memories"]:
                    return []
                
                # Create Redis pipeline
                pipeline = self.redis.pipeline()
                
                # Add all memory gets to the pipeline with their IDs for tracking
                memory_keys = []
                for memory_id in network["memories"]:
                    memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                    memory_keys.append((memory_id, memory_key))
                    pipeline.get(memory_key)
                
                # Execute pipeline to get all memories in a single Redis operation
                memory_values = await pipeline.execute()
                
                # Process the results
                memories = []
                for i, data in enumerate(memory_values):
                    if not data:
                        continue
                        
                    memory = json.loads(data)
                    
                    # Filter by type if specified
                    if memory_type and memory["type"] != memory_type:
                        continue
                        
                    memories.append(memory)
                
                # Sort by creation time (newest first)
                memories.sort(key=lambda x: x["created_at"], reverse=True)
                
                # Limit results
                return memories[:limit]
            
            # When a query is provided, use the appropriate search strategy
            semantic_results = []  # Will store semantic search results if applicable
            keyword_results = []   # Will store keyword search results if applicable
            
            # For semantic or hybrid search modes, use vector embeddings
            if search_mode in ["semantic", "hybrid"]:
                try:
                    # Import vector embedding service
                    from ..implementations.memory.vector_embeddings import get_vector_embedding_service
                    vector_service = get_vector_embedding_service()
                    
                    # Perform semantic search
                    similar_memories = await vector_service.search_by_vector_similarity(
                        network_id=network_id,
                        query=query,
                        limit=limit * 2  # Get more than needed to allow for filtering
                    )
                    
                    # Get full memory objects for similar memories
                    if similar_memories:
                        pipeline = self.redis.pipeline()
                        
                        for item in similar_memories:
                            memory_id = item["memory_id"]
                            memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                            pipeline.get(memory_key)
                        
                        memory_data_list = await pipeline.execute()
                        
                        # Process memory items and add similarity scores
                        for i, memory_data in enumerate(memory_data_list):
                            if memory_data:
                                memory = json.loads(memory_data)
                                
                                # Filter by type if specified
                                if memory_type and memory["type"] != memory_type:
                                    continue
                                
                                # Add similarity score to memory
                                memory["similarity_score"] = similar_memories[i]["similarity"]
                                
                                semantic_results.append(memory)
                                
                        # If semantic mode and we got results, return them
                        if search_mode == "semantic" and semantic_results:
                            # Limit results
                            return semantic_results[:limit]
                        
                except Exception as e:
                    logger.error(f"Semantic search failed: {e}")
                    # If semantic search fails and mode is semantic, fall back to keyword
                    if search_mode == "semantic":
                        search_mode = "keyword"
            
            # For keyword or hybrid search modes, or if semantic search failed
            if search_mode in ["keyword", "hybrid"] or (search_mode == "semantic" and not semantic_results):
                try:
                    # Try using memory indexing system first
                    from ..implementations.memory.memory_indexing import get_memory_indexing_system
                    memory_indexing = get_memory_indexing_system()
                    
                    # Search memories using indexing system
                    memory_ids = await memory_indexing.search_memories(
                        network_id=network_id,
                        query=query,
                        memory_type=memory_type,
                        limit=limit * 2,  # Get extra to allow for filtering
                        sort_by="relevance",
                        use_vector_search=False  # Use keyword search
                    )
                    
                    # Get memory objects for matching IDs
                    if memory_ids:
                        pipeline = self.redis.pipeline()
                        
                        for memory_id in memory_ids:
                            memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                            pipeline.get(memory_key)
                        
                        memory_data_list = await pipeline.execute()
                        
                        # Process memory items
                        for i, memory_data in enumerate(memory_data_list):
                            if memory_data:
                                memory = json.loads(memory_data)
                                
                                # Filter by type (if not already filtered by indexing system)
                                if memory_type and memory["type"] != memory_type:
                                    continue
                                
                                keyword_results.append(memory)
                        
                        # If keyword mode or semantic failed/empty, return keyword results
                        if search_mode == "keyword" or not semantic_results:
                            # Limit results
                            return keyword_results[:limit]
                
                except Exception as e:
                    logger.error(f"Keyword search failed: {e}")
                    # Fall back to basic search if both methods have failed
                    if not semantic_results:
                        search_mode = "fallback"
            
            # For hybrid mode, merge and deduplicate results
            if search_mode == "hybrid" and (semantic_results or keyword_results):
                # Start with semantic results, if any
                merged_results = semantic_results.copy()
                
                # Track existing memory IDs to avoid duplicates
                existing_ids = {memory.get("id") for memory in merged_results}
                
                # Add keyword results that aren't already included
                for memory in keyword_results:
                    if memory.get("id") not in existing_ids:
                        merged_results.append(memory)
                
                # Sort by similarity score if available, otherwise by creation time
                merged_results.sort(
                    key=lambda x: x.get("similarity_score", 0) if "similarity_score" in x else 0, 
                    reverse=True
                )
                
                # Limit results
                return merged_results[:limit]
            
            # Fallback to basic filtering (used if all else fails)
            if search_mode == "fallback" or (not semantic_results and not keyword_results):
                # Get network
                network_key = f"{NETWORK_KEY_PREFIX}{network_id}"
                network_data = await self.redis.get(network_key)
                
                if not network_data:
                    return []
                
                network = json.loads(network_data)
                
                # If no memories, return empty list
                if not network["memories"]:
                    return []
                
                # Create Redis pipeline
                pipeline = self.redis.pipeline()
                
                # Add all memory gets to the pipeline
                for memory_id in network["memories"]:
                    memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                    pipeline.get(memory_key)
                
                # Execute pipeline
                memory_values = await pipeline.execute()
                
                # Process the results
                memories = []
                for data in memory_values:
                    if not data:
                        continue
                        
                    memory = json.loads(data)
                    
                    # Filter by type if specified
                    if memory_type and memory["type"] != memory_type:
                        continue
                        
                    # Basic keyword filtering
                    if query and query.lower() not in memory["content"].lower():
                        continue
                        
                    memories.append(memory)
                
                # Sort by creation time (newest first)
                memories.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Apply limit
            return memories[:limit]
            
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
                prefixes = [NETWORK_KEY_PREFIX, TASK_KEY_PREFIX, AGENT_KEY_PREFIX, MEMORY_KEY_PREFIX]
                for prefix in prefixes:
                    pipeline.keys(f"{prefix}*")
                
                # Also add memory info to the same pipeline
                pipeline.info("memory")
                
                # Execute all commands in a single round-trip with timeout
                all_results = await asyncio.wait_for(pipeline.execute(), timeout=3.0)
                
                # Extract entity counts (first 4 results)
                count_results = [len(keys) for keys in all_results[:4]]
                
                # Extract memory info (last result)
                memory_info = all_results[4]
                
                # Map count results to named operations
                count_ops_names = ['networks', 'tasks', 'agents', 'memories']
                
            except Exception as e:
                logger.error(f"Failed to execute Redis pipeline: {e}")
                errors.append(f"Redis pipeline error: {str(e)}")
                count_results = [-1, -1, -1, -1] 
                memory_info = {}
                count_ops_names = ['networks', 'tasks', 'agents', 'memories']
            
            # Process counts
            entity_counts = {}
            for i, name in enumerate(count_ops_names):
                result = count_results[i]
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
            elif errors:
                overall_status = "degraded"   # Non-critical errors mean degraded
            
            # Calculate health check duration
            health_duration = time.time() - health_start_time
            
            # Final health check response
            return {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": int(health_duration * 1000),
                "services": results,
                "errors": errors if errors else None,
                "instance_id": id(self)  # For debugging load balancing
            }
            
        except Exception as e:
            logger.error(f"Health check failed with critical error: {e}")
            traceback.print_exc()
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
