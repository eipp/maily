"""
WebSocket router for canvas real-time collaboration.
Handles visualization layer updates, canvas operations, and user presence.
"""

import json
import logging
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from starlette.websockets import WebSocketState
from pydantic import BaseModel, Field

from ..services.websocket_service import get_connection_manager, MessageType, WebSocketMessage
from ..services.visualization_service import get_visualization_service
from ..services.trust_verification_service import get_trust_verification_service
from ..services.performance_insights_service import get_performance_insights_service
from ..services.auth_service import get_current_user_from_token
from ..monitoring.metrics import record_metric
from ..utils.tracing import create_websocket_span, trace_function, setup_tracing

# Setup tracing and logging
tracer = setup_tracing("canvas_websocket_router")
logger = logging.getLogger("api.routers.canvas_websocket")

# Create router
router = APIRouter(prefix="/ws/canvas", tags=["websocket", "canvas"])

# Define message models
class UserPresence(BaseModel):
    """User presence information"""
    user_id: str
    name: str
    cursor: Optional[Dict[str, float]] = None
    color: str = "#1E88E5"
    is_active: bool = True
    last_active: datetime = Field(default_factory=datetime.utcnow)

class CursorPosition(BaseModel):
    """Cursor position update"""
    x: float
    y: float

class LayerUpdate(BaseModel):
    """Layer update information"""
    layer_id: str
    visible: bool = True
    opacity: float = 1.0
    layer_data: Optional[Dict[str, Any]] = None

class CanvasOperation(BaseModel):
    """Canvas operation information"""
    operation_id: str
    operation_type: str  # add, update, delete, transform
    target_id: Optional[str] = None
    data: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Active canvas rooms and users
canvas_users: Dict[str, Dict[str, UserPresence]] = {}  # canvas_id -> {user_id -> UserPresence}

@router.websocket("/{canvas_id}")
async def websocket_canvas_endpoint(
    websocket: WebSocket,
    canvas_id: str,
    token: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    user_name: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for canvas real-time collaboration.
    
    Args:
        websocket: WebSocket connection
        canvas_id: Canvas identifier
        token: Optional authentication token
        user_id: User identifier (required if token not provided)
        user_name: User name (required if token not provided)
    """
    connection_id = None
    connection_manager = get_connection_manager()
    room_id = f"room_{canvas_id}"
    
    # Authenticate user
    authenticated_user = None
    if token:
        try:
            authenticated_user = await get_current_user_from_token(token)
            user_id = authenticated_user.id
            user_name = authenticated_user.name
        except Exception as e:
            logger.warning(f"Invalid token for WebSocket connection: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    # Require user_id and user_name if not authenticated
    if not user_id or not user_name:
        logger.warning("Missing user_id or user_name for WebSocket connection")
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        return
    
    # Generate a random color for the user
    import random
    colors = [
        "#1E88E5",  # Blue
        "#43A047",  # Green
        "#E53935",  # Red
        "#FB8C00",  # Orange
        "#8E24AA",  # Purple
        "#00ACC1",  # Cyan
        "#FFB300",  # Amber
        "#5E35B1",  # Deep Purple
        "#1565C0",  # Blue
        "#00897B",  # Teal
    ]
    user_color = random.choice(colors)
    
    # Initialize user presence
    user_presence = UserPresence(
        user_id=user_id,
        name=user_name,
        color=user_color
    )
    
    try:
        # Accept WebSocket connection
        connection_metadata = {
            "user_id": user_id,
            "name": user_name,
            "color": user_color,
            "canvas_id": canvas_id,
            "authenticated": authenticated_user is not None
        }
        
        # Connect using the connection manager
        connection_id = await connection_manager.connect(
            websocket, 
            room_id, 
            user_id=user_id, 
            metadata=connection_metadata
        )
        
        # Track user presence for this canvas
        if canvas_id not in canvas_users:
            canvas_users[canvas_id] = {}
        
        canvas_users[canvas_id][user_id] = user_presence
        
        # Record connection metric
        record_metric(
            "websocket.canvas.connection.active", 
            len(canvas_users.get(canvas_id, {})),
            {"canvas_id": canvas_id}
        )
        
        # Send initial visualization layers
        visualization_service = get_visualization_service()
        if not getattr(visualization_service, "initialized", False):
            await visualization_service.initialize()
        
        layers = await visualization_service.get_visualization_layers(canvas_id)
        
        await connection_manager.send_to_connection(connection_id, {
            "type": "visualization_layers",
            "layers": layers,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send active users in this canvas
        active_users = list(canvas_users.get(canvas_id, {}).values())
        
        await connection_manager.broadcast(WebSocketMessage(
            type=MessageType.STATUS_UPDATE,
            data={
                "type": "active_users",
                "canvas_id": canvas_id,
                "users": [user.dict() for user in active_users],
                "timestamp": datetime.utcnow().isoformat()
            },
            sender="canvas_websocket"
        ), room_id)
        
        # Listen for client messages
        try:
            while True:
                # Wait for message
                data = await websocket.receive_text()
                
                # Parse message
                try:
                    message = json.loads(data)
                    await process_canvas_message(
                        canvas_id=canvas_id,
                        user_id=user_id,
                        message=message,
                        connection_manager=connection_manager,
                        connection_id=connection_id
                    )
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from client {connection_id}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        # Clean up
        if connection_id:
            await connection_manager.disconnect(connection_id)
        
        # Remove user from canvas
        if canvas_id in canvas_users and user_id in canvas_users[canvas_id]:
            del canvas_users[canvas_id][user_id]
            
            # Remove canvas if no users left
            if not canvas_users[canvas_id]:
                del canvas_users[canvas_id]
            
            # Notify other users about departure
            await connection_manager.broadcast(WebSocketMessage(
                type=MessageType.STATUS_UPDATE,
                data={
                    "type": "user_left",
                    "canvas_id": canvas_id,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                sender="canvas_websocket"
            ), room_id)
            
            # Record connection metric
            record_metric(
                "websocket.canvas.connection.active", 
                len(canvas_users.get(canvas_id, {})),
                {"canvas_id": canvas_id}
            )


@trace_function(tracer, "process_canvas_message")
async def process_canvas_message(
    canvas_id: str,
    user_id: str,
    message: Dict[str, Any],
    connection_manager,
    connection_id: str
):
    """
    Process incoming WebSocket message from canvas client.
    
    Args:
        canvas_id: Canvas identifier
        user_id: User identifier
        message: Message data
        connection_manager: WebSocket connection manager
        connection_id: Connection identifier
    """
    with create_websocket_span("process_message", 
                               room_id=f"room_{canvas_id}",
                               message_type=message.get("type"),
                               user_id=user_id):
        
        message_type = message.get("type")
        room_id = f"room_{canvas_id}"
        
        if message_type == "cursor_move" and "position" in message:
            # Update cursor position
            if canvas_id in canvas_users and user_id in canvas_users[canvas_id]:
                position = message["position"]
                canvas_users[canvas_id][user_id].cursor = position
                canvas_users[canvas_id][user_id].last_active = datetime.utcnow()
                
                # Broadcast cursor position to other users
                await connection_manager.broadcast(WebSocketMessage(
                    type=MessageType.STATUS_UPDATE,
                    data={
                        "type": "cursor_position",
                        "canvas_id": canvas_id,
                        "user_id": user_id,
                        "position": position,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    sender="canvas_websocket"
                ), room_id, exclude_connection=connection_id)
        
        elif message_type == "layer_update" and "layer" in message:
            # Process layer update
            layer_data = message["layer"]
            layer_id = layer_data.get("id")
            
            if not layer_id:
                return
            
            # Get visualization service
            visualization_service = get_visualization_service()
            if not getattr(visualization_service, "initialized", False):
                await visualization_service.initialize()
            
            # Update layer visibility
            if "visible" in layer_data or "opacity" in layer_data:
                await visualization_service.update_layer_visibility(
                    canvas_id=canvas_id,
                    layer_id=layer_id,
                    visible=layer_data.get("visible", True),
                    opacity=layer_data.get("opacity", 1.0)
                )
            
            # The _notify_layer_update method will broadcast to all clients
        
        elif message_type == "canvas_operation" and "operation" in message:
            # Process canvas operation
            operation = message["operation"]
            
            # Broadcast operation to all clients
            await connection_manager.broadcast(WebSocketMessage(
                type=MessageType.CANVAS_UPDATE,
                data={
                    "type": "canvas_operation",
                    "canvas_id": canvas_id,
                    "user_id": user_id,
                    "operation": operation,
                    "timestamp": datetime.utcnow().isoformat()
                },
                sender="canvas_websocket"
            ), room_id)
        
        elif message_type == "verify_content" and "content" in message:
            # Process verification request
            content = message["content"]
            
            # Get verification service
            verification_service = get_trust_verification_service()
            if not hasattr(verification_service, "redis") or verification_service.redis is None:
                await verification_service.initialize()
            
            # Verify content
            verification_data = await verification_service.verify_canvas_content(
                canvas_id=canvas_id,
                content=content,
                user_id=user_id
            )
            
            # Get visualization service
            visualization_service = get_visualization_service()
            if not getattr(visualization_service, "initialized", False):
                await visualization_service.initialize()
            
            # Update visualization layer
            await visualization_service.sync_visualization_with_verification(
                canvas_id=canvas_id
            )
            
            # Send verification result to requestor
            await connection_manager.send_to_connection(connection_id, {
                "type": "verification_result",
                "canvas_id": canvas_id,
                "status": verification_data.get("status", {}).get("status", "unverified"),
                "data": verification_data,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif message_type == "performance_request" and "metrics" in message:
            # Process performance metrics request
            metrics_request = message["metrics"]
            campaign_id = metrics_request.get("campaign_id")
            
            # Get performance service
            performance_service = get_performance_insights_service()
            
            # Get metrics
            metrics = await performance_service.get_email_performance_metrics(
                canvas_id=canvas_id,
                campaign_id=campaign_id
            )
            
            # Get visualization service
            visualization_service = get_visualization_service()
            if not getattr(visualization_service, "initialized", False):
                await visualization_service.initialize()
            
            # Update visualization layer
            await visualization_service.sync_visualization_with_performance(
                canvas_id=canvas_id,
                campaign_id=campaign_id
            )
            
            # Send metrics to requestor
            await connection_manager.send_to_connection(connection_id, {
                "type": "performance_metrics",
                "canvas_id": canvas_id,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif message_type == "ping":
            # Respond to ping
            await connection_manager.send_to_connection(connection_id, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        else:
            logger.warning(f"Unknown message type: {message_type}")


@router.get("/active/{canvas_id}")
async def get_active_canvas_users(canvas_id: str):
    """
    Get all active users in a canvas.
    
    Args:
        canvas_id: Canvas identifier
        
    Returns:
        List of active users
    """
    if canvas_id not in canvas_users:
        return {"users": []}
    
    users = list(canvas_users[canvas_id].values())
    return {"users": [user.dict() for user in users]}