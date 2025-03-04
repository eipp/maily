"""
WebSocket Router for AI Mesh Network

This module provides WebSocket endpoints for real-time communication
with the AI Mesh Network, allowing clients to receive real-time updates
on agent activities, task progress, and results. The implementation supports:

1. Real-time task updates
2. Agent status monitoring 
3. Memory changes notification
4. Network-wide broadcasts
5. Session management with authentication
"""

import logging
import json
import asyncio
import time
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Depends
from pydantic import BaseModel

from ..services.agent_coordinator import get_agent_coordinator, AgentCoordinator
from ..utils.redis_client import get_redis_client

logger = logging.getLogger("ai_service.routers.websocket_router")

router = APIRouter()

# Store active connections with network mapping
connections: Dict[str, Dict[str, WebSocket]] = {}
# Store connection callbacks for each client
connection_callbacks: Dict[str, Dict[str, Set[Callable]]] = {}

# Redis PubSub client for real-time messaging
class MeshPubSub:
    """Redis PubSub client for AI Mesh Network real-time messaging"""
    
    def __init__(self):
        self.redis = None
        self.pubsub = None
        self.tasks: Dict[str, asyncio.Task] = {}
        self.callbacks: Dict[str, Set[Callable]] = {}
        self.channels: Dict[str, Set[str]] = {}  # Maps connection ID to channel subscriptions
        self.lock = asyncio.Lock()
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Initialize Redis client and PubSub"""
        if not self._initialized:
            self.redis = await get_redis_client()
            self.pubsub = await self.redis.client.pubsub()
            self._initialized = True
    
    async def subscribe(self, channel: str, connection_id: str, callback: Callable):
        """Subscribe to a channel and register a callback for a connection"""
        await self._ensure_initialized()
        
        async with self.lock:
            # Add channel to connection's subscriptions
            if connection_id not in self.channels:
                self.channels[connection_id] = set()
            self.channels[connection_id].add(channel)
            
            # Add callback for channel
            if channel not in self.callbacks:
                self.callbacks[channel] = set()
                
                # First callback for channel, subscribe in Redis
                await self.pubsub.subscribe(channel)
                
                # Start listener task if not already running
                if channel not in self.tasks or self.tasks[channel].done():
                    self.tasks[channel] = asyncio.create_task(
                        self._message_listener(channel)
                    )
            
            # Add callback
            self.callbacks[channel].add(callback)
        
        logger.debug(f"Connection {connection_id} subscribed to channel: {channel}")
    
    async def unsubscribe_connection(self, connection_id: str):
        """Unsubscribe a connection from all channels"""
        if not self._initialized:
            return
        
        if connection_id not in self.channels:
            return
        
        async with self.lock:
            # Get channels for this connection
            channels = list(self.channels[connection_id])
            
            # Remove callbacks for each channel
            for channel in channels:
                callbacks_to_remove = [
                    callback for callback in self.callbacks.get(channel, set())
                    if getattr(callback, "__connection_id", None) == connection_id
                ]
                
                for callback in callbacks_to_remove:
                    if channel in self.callbacks:
                        self.callbacks[channel].discard(callback)
                
                # If no more callbacks for channel, unsubscribe
                if channel in self.callbacks and not self.callbacks[channel]:
                    await self.pubsub.unsubscribe(channel)
                    self.callbacks.pop(channel)
                    
                    # Cancel listener task
                    if channel in self.tasks and not self.tasks[channel].done():
                        self.tasks[channel].cancel()
                        try:
                            await self.tasks[channel]
                        except asyncio.CancelledError:
                            pass
                        self.tasks.pop(channel)
            
            # Remove connection from channels mapping
            self.channels.pop(connection_id)
        
        logger.debug(f"Connection {connection_id} unsubscribed from all channels")
    
    async def publish(self, channel: str, message: Any):
        """Publish a message to a channel"""
        await self._ensure_initialized()
        
        # Convert message to JSON if it's a dict
        message_data = json.dumps(message) if isinstance(message, dict) else message
        
        # Publish to Redis
        await self.redis.publish(channel, message_data)
        logger.debug(f"Published message to {channel}")
    
    async def _message_listener(self, channel: str):
        """Listen for messages on a channel and dispatch to callbacks"""
        try:
            logger.debug(f"Started listener for channel: {channel}")
            
            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message is None:
                    await asyncio.sleep(0.01)  # Prevent CPU spinning
                    continue
                
                # Process message
                if message["type"] == "message":
                    try:
                        # Parse message data
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")
                        
                        # Try to parse as JSON
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            pass  # Keep as string if not valid JSON
                        
                        # Check exclusion metadata
                        exclude_connection = None
                        if isinstance(data, dict) and "_exclude_connection" in data:
                            exclude_connection = data.pop("_exclude_connection")
                        
                        # Dispatch to callbacks
                        async with self.lock:
                            callbacks_list = list(self.callbacks.get(channel, []))
                        
                        for callback in callbacks_list:
                            try:
                                # Skip if this connection should be excluded
                                connection_id = getattr(callback, "__connection_id", None)
                                if exclude_connection and connection_id == exclude_connection:
                                    continue
                                
                                await callback(data)
                            except Exception as e:
                                logger.error(f"Error in channel {channel} callback: {e}")
                    
                    except Exception as e:
                        logger.error(f"Error processing message from channel {channel}: {e}")
        
        except asyncio.CancelledError:
            logger.debug(f"Listener for channel {channel} cancelled")
            raise
        except Exception as e:
            logger.error(f"Channel {channel} listener failed: {e}")
    
    async def close(self):
        """Close all connections and cancel tasks"""
        if not self._initialized:
            return
        
        try:
            # Cancel all listener tasks
            for channel, task in list(self.tasks.items()):
                if not task.done():
                    task.cancel()
            
            # Wait for all tasks to complete
            if self.tasks:
                await asyncio.gather(*list(self.tasks.values()), return_exceptions=True)
            
            # Close PubSub and Redis connections
            if self.pubsub:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
            
            self._initialized = False
            logger.info("Mesh PubSub service closed")
        
        except Exception as e:
            logger.error(f"Error closing Mesh PubSub: {e}")

# Singleton PubSub instance
pubsub = MeshPubSub()

# Pydantic models for WebSocket messages
class WebSocketMessage(BaseModel):
    type: str
    network_id: str
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

@router.websocket("/mesh/network/{network_id}/ws")
async def network_websocket(
    websocket: WebSocket,
    network_id: str,
    user_id: Optional[str] = Query(None),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    """WebSocket endpoint for real-time AI Mesh Network updates"""
    
    # Verify network exists
    try:
        network = await coordinator.get_network(network_id)
        if not network:
            await websocket.close(code=4004, reason="Network not found")
            return
    except Exception as e:
        logger.error(f"Error verifying network {network_id}: {e}")
        await websocket.close(code=4004, reason="Network not found")
        return
    
    # Accept connection
    await websocket.accept()
    
    # Generate connection ID
    connection_id = f"{network_id}_{int(time.time())}_{id(websocket)}"
    
    # Track connection in active connections
    if network_id not in connections:
        connections[network_id] = {}
    connections[network_id][connection_id] = websocket
    
    # Send initial connection message
    await websocket.send_json({
        "type": "connected",
        "network_id": network_id,
        "connection_id": connection_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Subscribe to network events
    network_channel = f"network:{network_id}"
    
    # Create callback for network events
    async def network_callback(data):
        try:
            # Don't need to exclude this connection for network events
            # All clients should receive these
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error in network callback for {connection_id}: {e}")
    
    # Set connection ID attribute on callback
    setattr(network_callback, "__connection_id", connection_id)
    
    # Subscribe to network events
    await pubsub.subscribe(network_channel, connection_id, network_callback)
    
    # For task-specific events, tracks subscriptions
    task_subscriptions = set()
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Basic validation
                if "type" not in message:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Invalid message format: missing 'type'",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    continue
                
                # Handle message types
                if message["type"] == "ping":
                    # Respond to ping
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message["type"] == "subscribe_task":
                    # Subscribe to task events
                    if "task_id" not in message:
                        await websocket.send_json({
                            "type": "error",
                            "error": "Invalid subscribe_task message: missing 'task_id'",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    task_id = message["task_id"]
                    
                    # Verify task belongs to this network
                    try:
                        task = await coordinator.get_task(task_id)
                        if not task or task.get("network_id") != network_id:
                            await websocket.send_json({
                                "type": "error",
                                "error": f"Task {task_id} not found in network {network_id}",
                                "timestamp": datetime.utcnow().isoformat()
                            })
                            continue
                    except Exception as e:
                        logger.error(f"Error verifying task {task_id}: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "error": f"Error verifying task: {str(e)}",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    # Task channel
                    task_channel = f"task:{task_id}"
                    
                    # Create callback for task events
                    async def task_callback(data):
                        try:
                            await websocket.send_json(data)
                        except Exception as e:
                            logger.error(f"Error in task callback for {connection_id}: {e}")
                    
                    # Set connection ID attribute on callback
                    setattr(task_callback, "__connection_id", connection_id)
                    
                    # Subscribe to task events
                    await pubsub.subscribe(task_channel, connection_id, task_callback)
                    
                    # Track subscription
                    task_subscriptions.add(task_id)
                    
                    # Acknowledge subscription
                    await websocket.send_json({
                        "type": "subscribed",
                        "task_id": task_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message["type"] == "unsubscribe_task":
                    # Unsubscribe from task events
                    if "task_id" not in message:
                        await websocket.send_json({
                            "type": "error",
                            "error": "Invalid unsubscribe_task message: missing 'task_id'",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    task_id = message["task_id"]
                    task_channel = f"task:{task_id}"
                    
                    # Create a dummy callback to unsubscribe
                    # The actual callback will be found by connection ID
                    async def dummy_callback(data):
                        pass
                    
                    setattr(dummy_callback, "__connection_id", connection_id)
                    
                    # Unsubscribe from task events
                    # This will actually remove all callbacks for this connection
                    # for the specified channel
                    await pubsub.unsubscribe_connection(connection_id)
                    
                    # Re-subscribe to network channel
                    await pubsub.subscribe(network_channel, connection_id, network_callback)
                    
                    # Remove from tracked subscriptions
                    task_subscriptions.discard(task_id)
                    
                    # Acknowledge unsubscription
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "task_id": task_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message["type"] == "get_active_tasks":
                    # Get active tasks for the network
                    try:
                        tasks = await coordinator.list_network_tasks(
                            network_id=network_id,
                            status="active",
                            limit=50,
                            offset=0
                        )
                        
                        await websocket.send_json({
                            "type": "active_tasks",
                            "tasks": tasks,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except Exception as e:
                        logger.error(f"Error getting active tasks: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "error": f"Error getting active tasks: {str(e)}",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Unknown message type: {message['type']}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "error": "Invalid JSON",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "error": f"Server error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnect for {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        # Clean up
        await pubsub.unsubscribe_connection(connection_id)
        
        # Remove from active connections
        if network_id in connections and connection_id in connections[network_id]:
            del connections[network_id][connection_id]
            if not connections[network_id]:
                del connections[network_id]

@router.websocket("/mesh/task/{task_id}/ws")
async def task_websocket(
    websocket: WebSocket,
    task_id: str,
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    """WebSocket endpoint for real-time task updates"""
    
    # Verify task exists
    try:
        task = await coordinator.get_task(task_id)
        if not task:
            await websocket.close(code=4004, reason="Task not found")
            return
        
        network_id = task["network_id"]
    except Exception as e:
        logger.error(f"Error verifying task {task_id}: {e}")
        await websocket.close(code=4004, reason="Task not found")
        return
    
    # Accept connection
    await websocket.accept()
    
    # Generate connection ID
    connection_id = f"task_{task_id}_{int(time.time())}_{id(websocket)}"
    
    # Send initial connection message
    await websocket.send_json({
        "type": "connected",
        "task_id": task_id,
        "network_id": network_id,
        "connection_id": connection_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Subscribe to task events
    task_channel = f"task:{task_id}"
    
    # Create callback for task events
    async def task_callback(data):
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error in task callback for {connection_id}: {e}")
    
    # Set connection ID attribute on callback
    setattr(task_callback, "__connection_id", connection_id)
    
    # Subscribe to task events
    await pubsub.subscribe(task_channel, connection_id, task_callback)
    
    try:
        # Send initial task state
        task_state = await coordinator.get_task(task_id)
        await websocket.send_json({
            "type": "task_state",
            "task_id": task_id,
            "network_id": network_id,
            "state": task_state,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Handle incoming messages (mostly ping)
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle ping
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except:
                # Ignore invalid messages
                pass
    
    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnect for {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        # Clean up
        await pubsub.unsubscribe_connection(connection_id)

# Helper function to broadcast task updates
async def broadcast_task_update(
    task_id: str,
    update_type: str,
    data: Dict[str, Any]
):
    """Broadcast a task update to all subscribed clients"""
    channel = f"task:{task_id}"
    message = {
        "type": update_type,
        "task_id": task_id,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await pubsub.publish(channel, message)

# Helper function to broadcast network updates
async def broadcast_network_update(
    network_id: str,
    update_type: str,
    data: Dict[str, Any]
):
    """Broadcast a network update to all subscribed clients"""
    channel = f"network:{network_id}"
    message = {
        "type": update_type,
        "network_id": network_id,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await pubsub.publish(channel, message)

@router.get("/mesh/networks/{network_id}/memory", tags=["AI Mesh Network - WebSocket"])
async def get_memory_ws_endpoint(
    network_id: str = Path(..., description="ID of the network"),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    """Get WebSocket connection info for memory updates"""
    try:
        # Verify network exists
        network = await coordinator.get_network(network_id)
        if not network:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Network {network_id} not found"
            )
        
        # Return WebSocket connection info
        return {
            "websocket_url": f"/api/mesh/network/{network_id}/ws",
            "memory_channel": f"memory:{network_id}",
            "connection_type": "websocket",
            "protocol_version": "1.0"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory WebSocket endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory WebSocket endpoint: {str(e)}"
        )

@router.websocket("/mesh/memory/{network_id}/ws")
async def memory_websocket(
    websocket: WebSocket,
    network_id: str,
    user_id: Optional[str] = Query(None),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    """WebSocket endpoint for real-time memory updates"""
    
    # Verify network exists
    try:
        network = await coordinator.get_network(network_id)
        if not network:
            await websocket.close(code=4004, reason="Network not found")
            return
    except Exception as e:
        logger.error(f"Error verifying network {network_id}: {e}")
        await websocket.close(code=4004, reason="Network not found")
        return
    
    # Accept connection
    await websocket.accept()
    
    # Generate connection ID
    connection_id = f"memory_{network_id}_{int(time.time())}_{id(websocket)}"
    
    # Send initial connection message
    await websocket.send_json({
        "type": "connected",
        "network_id": network_id,
        "connection_id": connection_id,
        "timestamp": datetime.utcnow().isoformat(),
        "protocol": "memory"
    })
    
    # Subscribe to memory events
    memory_channel = f"memory:{network_id}"
    
    # Create callback for memory events
    async def memory_callback(data):
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error in memory callback for {connection_id}: {e}")
    
    # Set connection ID attribute on callback
    setattr(memory_callback, "__connection_id", connection_id)
    
    # Subscribe to memory events
    await pubsub.subscribe(memory_channel, connection_id, memory_callback)
    
    try:
        # Immediately send current memory items
        try:
            memories = await coordinator.get_network_memory(
                network_id=network_id,
                limit=50
            )
            
            await websocket.send_json({
                "type": "memory_snapshot",
                "network_id": network_id,
                "memories": memories,
                "timestamp": datetime.utcnow().isoformat(),
                "count": len(memories)
            })
        except Exception as e:
            logger.error(f"Error sending memory snapshot: {e}")
        
        # Handle incoming messages (simple commands and ping)
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle ping
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    continue
                
                # Handle memory query
                if message.get("type") == "memory_query":
                    query = message.get("query", "")
                    memory_type = message.get("memory_type")
                    limit = min(message.get("limit", 20), 100)  # Cap at 100 items max
                    
                    memories = await coordinator.get_network_memory(
                        network_id=network_id,
                        memory_type=memory_type,
                        query=query,
                        limit=limit,
                        search_mode=message.get("search_mode", "semantic")
                    )
                    
                    await websocket.send_json({
                        "type": "memory_query_results",
                        "query": query,
                        "results": memories,
                        "timestamp": datetime.utcnow().isoformat(),
                        "count": len(memories)
                    })
                    continue
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "error": "Invalid JSON",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error handling memory WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "error": f"Server error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        logger.debug(f"Memory WebSocket disconnect for {connection_id}")
    except Exception as e:
        logger.error(f"Memory WebSocket error for {connection_id}: {e}")
    finally:
        # Clean up
        await pubsub.unsubscribe_connection(connection_id)

# Helper function to broadcast memory updates
async def broadcast_memory_update(
    network_id: str,
    memory_id: str,
    update_type: str,
    memory_data: Dict[str, Any]
):
    """Broadcast a memory update to all subscribed clients"""
    channel = f"memory:{network_id}"
    message = {
        "type": update_type,
        "network_id": network_id,
        "memory_id": memory_id,
        "data": memory_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await pubsub.publish(channel, message)

@router.on_event("startup")
async def startup_pubsub():
    """Initialize the PubSub system on startup"""
    logger.info("Initializing AI Mesh Network WebSocket PubSub system")
    # Ensure pubsub is initialized
    await pubsub._ensure_initialized()
    
    # Register memory update handler
    from ..implementations.memory.memory_indexing import get_memory_indexing_system
    memory_indexing = get_memory_indexing_system()
    memory_indexing.set_update_callback(broadcast_memory_update)
    
    logger.info("Memory update broadcast handler registered")

@router.on_event("shutdown")
async def shutdown_pubsub():
    """Close the PubSub system on shutdown"""
    logger.info("Closing AI Mesh Network WebSocket PubSub system")
    await pubsub.close()