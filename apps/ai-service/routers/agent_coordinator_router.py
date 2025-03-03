"""
Router for AI Mesh Network Agent Coordinator

This module provides API endpoints for the AI Mesh Network Agent Coordinator.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, status
from pydantic import BaseModel, Field

from ..services.agent_coordinator import get_agent_coordinator, AgentCoordinator

logger = logging.getLogger("ai_service.routers.agent_coordinator_router")

router = APIRouter()

# Pydantic models for request/response validation
class AgentConfig(BaseModel):
    name: str = Field(..., description="Name of the agent")
    type: str = Field(..., description="Type of the agent (content, design, analytics, etc.)")
    model: str = Field(..., description="LLM model to use for the agent")
    description: Optional[str] = Field(None, description="Description of the agent")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters for the agent")
    capabilities: Optional[List[str]] = Field(None, description="Capabilities of the agent")

class CreateNetworkRequest(BaseModel):
    name: str = Field(..., description="Name of the network")
    description: Optional[str] = Field(None, description="Description of the network")
    agents: Optional[List[AgentConfig]] = Field(None, description="Agents to add to the network")
    shared_context: Optional[Dict[str, Any]] = Field(None, description="Shared context for the network")
    max_iterations: Optional[int] = Field(10, description="Maximum number of iterations for tasks")
    timeout_seconds: Optional[int] = Field(300, description="Timeout in seconds for tasks")

class CreateNetworkResponse(BaseModel):
    network_id: str = Field(..., description="ID of the created network")
    name: str = Field(..., description="Name of the network")
    description: str = Field(..., description="Description of the network")
    created_at: str = Field(..., description="Creation timestamp")
    status: str = Field(..., description="Status of the network")

class NetworkSummary(BaseModel):
    id: str = Field(..., description="Network ID")
    name: str = Field(..., description="Network name")
    description: str = Field(..., description="Network description")
    created_at: str = Field(..., description="Creation timestamp")
    status: str = Field(..., description="Network status")
    agent_count: int = Field(..., description="Number of agents in the network")
    task_count: int = Field(..., description="Number of tasks in the network")
    memory_count: int = Field(..., description="Number of memory items in the network")

class SubmitTaskRequest(BaseModel):
    task: str = Field(..., description="Task description")
    context: Optional[Dict[str, Any]] = Field(None, description="Task context")
    priority: Optional[int] = Field(1, description="Task priority (1-10)")
    deadline: Optional[datetime] = Field(None, description="Task deadline")

class SubmitTaskResponse(BaseModel):
    task_id: str = Field(..., description="ID of the submitted task")
    network_id: str = Field(..., description="ID of the network")
    status: str = Field(..., description="Status of the task")
    created_at: str = Field(..., description="Creation timestamp")

class AddAgentRequest(BaseModel):
    agent_config: AgentConfig = Field(..., description="Agent configuration")

class AddAgentResponse(BaseModel):
    agent_id: str = Field(..., description="ID of the added agent")
    network_id: str = Field(..., description="ID of the network")
    name: str = Field(..., description="Name of the agent")
    type: str = Field(..., description="Type of the agent")
    status: str = Field(..., description="Status of the agent")

class AddMemoryRequest(BaseModel):
    content: str = Field(..., description="Content of the memory item")
    memory_type: str = Field("fact", description="Type of memory (fact, context, decision, feedback)")
    confidence: float = Field(1.0, description="Confidence score (0.0-1.0)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class AddMemoryResponse(BaseModel):
    memory_id: str = Field(..., description="ID of the added memory item")
    network_id: str = Field(..., description="ID of the network")
    type: str = Field(..., description="Type of the memory item")
    created_at: str = Field(..., description="Creation timestamp")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")
    redis_connection: bool = Field(..., description="Redis connection status")
    llm_client: Dict[str, Any] = Field(..., description="LLM client status")
    active_networks_count: int = Field(..., description="Number of active networks")
    active_tasks_count: int = Field(..., description="Number of active tasks")
    timestamp: str = Field(..., description="Timestamp of the health check")

# Dependency to get the agent coordinator
async def get_coordinator() -> AgentCoordinator:
    return get_agent_coordinator()

# Routes
@router.post("/mesh/networks", response_model=CreateNetworkResponse, status_code=status.HTTP_201_CREATED, tags=["AI Mesh Network"])
async def create_network(
    request: CreateNetworkRequest,
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Create a new AI Mesh Network"""
    try:
        network_id = await coordinator.create_network(
            name=request.name,
            description=request.description,
            agents=[agent.dict() for agent in request.agents] if request.agents else None,
            shared_context=request.shared_context,
            max_iterations=request.max_iterations,
            timeout_seconds=request.timeout_seconds
        )
        
        # Get network details
        network = await coordinator.get_network(network_id)
        
        return {
            "network_id": network_id,
            "name": network["name"],
            "description": network["description"],
            "created_at": network["created_at"],
            "status": network["status"]
        }
    except Exception as e:
        logger.error(f"Failed to create network: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create network: {str(e)}"
        )

@router.get("/mesh/networks", response_model=List[NetworkSummary], tags=["AI Mesh Network"])
async def list_networks(
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """List all AI Mesh Networks"""
    try:
        networks = await coordinator.list_networks()
        return networks
    except Exception as e:
        logger.error(f"Failed to list networks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list networks: {str(e)}"
        )

@router.get("/mesh/networks/{network_id}", tags=["AI Mesh Network"])
async def get_network(
    network_id: str = Path(..., description="ID of the network"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Get details of an AI Mesh Network"""
    try:
        network = await coordinator.get_network(network_id)
        if not network:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Network {network_id} not found"
            )
        return network
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get network: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get network: {str(e)}"
        )

@router.delete("/mesh/networks/{network_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["AI Mesh Network"])
async def delete_network(
    network_id: str = Path(..., description="ID of the network"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Delete an AI Mesh Network"""
    try:
        success = await coordinator.delete_network(network_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Network {network_id} not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete network: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete network: {str(e)}"
        )

@router.post("/mesh/networks/{network_id}/tasks", response_model=SubmitTaskResponse, tags=["AI Mesh Network"])
async def submit_task(
    request: SubmitTaskRequest,
    network_id: str = Path(..., description="ID of the network"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Submit a task to an AI Mesh Network"""
    try:
        task_id = await coordinator.submit_task(
            network_id=network_id,
            task=request.task,
            context=request.context,
            priority=request.priority,
            deadline=request.deadline
        )
        
        # Get task details
        task = await coordinator.get_task(task_id)
        
        return {
            "task_id": task_id,
            "network_id": network_id,
            "status": task["status"],
            "created_at": task["created_at"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to submit task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit task: {str(e)}"
        )

@router.post("/mesh/networks/{network_id}/tasks/{task_id}/process", status_code=status.HTTP_202_ACCEPTED, tags=["AI Mesh Network"])
async def process_task(
    network_id: str = Path(..., description="ID of the network"),
    task_id: str = Path(..., description="ID of the task"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Process a task in the AI Mesh Network"""
    try:
        # Start task processing asynchronously
        # Note: This will run in the background
        await coordinator.process_task(network_id, task_id)
        
        return {"status": "processing", "task_id": task_id, "network_id": network_id}
    except Exception as e:
        logger.error(f"Failed to process task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process task: {str(e)}"
        )

@router.get("/mesh/networks/{network_id}/tasks/{task_id}", tags=["AI Mesh Network"])
async def get_task(
    network_id: str = Path(..., description="ID of the network"),
    task_id: str = Path(..., description="ID of the task"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Get details of a task"""
    try:
        task = await coordinator.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        # Check if task belongs to the specified network
        if task["network_id"] != network_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found in network {network_id}"
            )
        
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}"
        )

@router.get("/mesh/networks/{network_id}/tasks", tags=["AI Mesh Network"])
async def list_tasks(
    network_id: str = Path(..., description="ID of the network"),
    status: Optional[str] = Query(None, description="Filter by task status"),
    limit: int = Query(10, description="Maximum number of tasks to return"),
    offset: int = Query(0, description="Offset for pagination"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """List tasks for a network"""
    try:
        tasks = await coordinator.list_network_tasks(
            network_id=network_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return tasks
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}"
        )

@router.post("/mesh/networks/{network_id}/agents", response_model=AddAgentResponse, tags=["AI Mesh Network"])
async def add_agent(
    request: AddAgentRequest,
    network_id: str = Path(..., description="ID of the network"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Add an agent to a network"""
    try:
        agent_id = await coordinator.add_agent_to_network(
            network_id=network_id,
            agent_config=request.agent_config.dict()
        )
        
        # Get agent details
        agent = await coordinator._get_agent(agent_id)
        
        return {
            "agent_id": agent_id,
            "network_id": network_id,
            "name": agent["name"],
            "type": agent["type"],
            "status": agent["status"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to add agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add agent: {str(e)}"
        )

@router.delete("/mesh/networks/{network_id}/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["AI Mesh Network"])
async def remove_agent(
    network_id: str = Path(..., description="ID of the network"),
    agent_id: str = Path(..., description="ID of the agent"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Remove an agent from a network"""
    try:
        success = await coordinator.remove_agent_from_network(
            network_id=network_id,
            agent_id=agent_id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found in network {network_id}"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove agent: {str(e)}"
        )

@router.get("/mesh/networks/{network_id}/agents", tags=["AI Mesh Network"])
async def list_agents(
    network_id: str = Path(..., description="ID of the network"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """List agents for a network"""
    try:
        agents = await coordinator.get_network_agents(network_id)
        return agents
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )

@router.post("/mesh/networks/{network_id}/memory", response_model=AddMemoryResponse, tags=["AI Mesh Network"])
async def add_memory(
    request: AddMemoryRequest,
    network_id: str = Path(..., description="ID of the network"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Add a memory item to the shared memory"""
    try:
        memory_id = await coordinator.add_memory(
            network_id=network_id,
            content=request.content,
            memory_type=request.memory_type,
            confidence=request.confidence,
            metadata=request.metadata
        )
        
        # Get memory details
        memory = await coordinator._get_memory(memory_id)
        
        return {
            "memory_id": memory_id,
            "network_id": network_id,
            "type": memory["type"],
            "created_at": memory["created_at"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add memory: {str(e)}"
        )

@router.get("/mesh/networks/{network_id}/memory", tags=["AI Mesh Network"])
async def get_memory(
    network_id: str = Path(..., description="ID of the network"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    query: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(50, description="Maximum number of memory items to return"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Get shared memory for a network"""
    try:
        memories = await coordinator.get_network_memory(
            network_id=network_id,
            memory_type=memory_type,
            query=query,
            limit=limit
        )
        return memories
    except Exception as e:
        logger.error(f"Failed to get memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory: {str(e)}"
        )

@router.get("/mesh/health", response_model=HealthResponse, tags=["AI Mesh Network"])
async def check_health(
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Check health of the AI Mesh Network service"""
    try:
        health = await coordinator.check_health()
        return health
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )
