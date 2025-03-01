from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from typing import Dict, List, Any, Optional, Set
import json
import asyncio
import logging
from datetime import datetime
from ..middleware.auth0 import Auth0JWTBearer
from ..config.settings import get_settings
from ..cache.redis_pubsub import RedisPubSub
from pydantic import BaseModel
from loguru import logger
import httpx
from ..services.canvas_service import CanvasService
from ..models.canvas import CanvasOperation, OperationTransform

router = APIRouter()
settings = get_settings()

# Store active connections with room mapping
connections: Dict[str, Dict[str, WebSocket]] = {}
# Store active users for presence tracking
active_users: Dict[str, Set[str]] = {}

# Auth dependency for WebSockets
auth_handler = Auth0JWTBearer(auto_error=True)

# PubSub instance
pubsub = RedisPubSub()

# Canvas service for operation transformation and state management
canvas_service = CanvasService()

class WebSocketMessage(BaseModel):
    type: str
    roomId: str
    userId: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    operations: Optional[List[Dict[str, Any]]] = None
    baseVersion: Optional[int] = None
    version: Optional[int] = None

class Cursor(BaseModel):
    x: float
    y: float
    userId: str
    userName: Optional[str] = None
    color: Optional[str] = None

@router.websocket("/v1/canvas")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    room: str = Query(...)
):
    # Authenticate
    try:
        payload = await auth_handler(websocket)
        user_id = payload.get("sub")
        user_name = payload.get("name", "Anonymous")
        if not user_id:
            await websocket.close(code=4001, reason="Unauthorized")
            return
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # Accept connection
    await websocket.accept()

    # Setup connection in the room
    if room not in connections:
        connections[room] = {}
    connections[room][user_id] = websocket

    # Add user to active users
    if room not in active_users:
        active_users[room] = set()
    active_users[room].add(user_id)

    # Extract canvas ID from room
    canvas_id = room.replace('room_', '')

    # Create a callback for this websocket
    async def message_callback(data):
        try:
            # Don't send back to originating user
            if isinstance(data, dict) and data.get("userId") != user_id:
                await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error in message callback: {e}")

    # Subscribe to room channel
    channel = f"canvas:{room}"
    await pubsub.subscribe(channel, message_callback)

    # Get current canvas state and version
    try:
        current_state = await canvas_service.get_canvas_state(canvas_id)
        current_version = current_state.get("version", 0)
    except Exception as e:
        logger.error(f"Error fetching canvas state: {e}")
        current_version = 0

    # Send connection acknowledgment
    await websocket.send_json({
        "type": "connected",
        "roomId": room,
        "userId": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "version": current_version
    })

    # Send active users list to the new user
    active_users_list = [{
        "userId": uid,
        "status": "active",
        "lastActive": datetime.utcnow().isoformat()
    } for uid in active_users[room]]

    await websocket.send_json({
        "type": "presence_update",
        "roomId": room,
        "payload": {
            "activeUsers": active_users_list
        }
    })

    # Send current user presence to all users in the room
    presence_message = {
        "type": "presence",
        "roomId": room,
        "userId": user_id,
        "payload": {
            "userId": user_id,
            "userName": user_name,
            "status": "active",
            "lastActive": datetime.utcnow().isoformat()
        }
    }
    await broadcast(room, presence_message)

    # Set up cursor tracking
    cursor: Optional[Cursor] = None

    try:
        while True:
            # Receive message from WebSocket
            message_raw = await websocket.receive_text()
            message = json.loads(message_raw)

            # Add user ID and timestamp to all messages
            if "userId" not in message:
                message["userId"] = user_id
            message["timestamp"] = datetime.utcnow().isoformat()

            # Handle different message types
            if message["type"] == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            # Handle cursor movement
            if message["type"] == "cursor_move":
                if "payload" in message and "x" in message["payload"] and "y" in message["payload"]:
                    cursor = Cursor(
                        x=message["payload"]["x"],
                        y=message["payload"]["y"],
                        userId=user_id,
                        userName=user_name,
                        color=message["payload"].get("color", "#3B82F6")  # Default blue color
                    )

                    cursor_message = {
                        "type": "cursor_update",
                        "roomId": room,
                        "userId": user_id,
                        "payload": cursor.dict()
                    }

                    # Only broadcast to others, don't send back to self
                    await broadcast(room, cursor_message, exclude_user=user_id)
                continue

            # Handle sync request
            if message["type"] == "sync_request":
                from_version = message.get("payload", {}).get("fromVersion", 0)

                try:
                    # Get operations since requested version
                    operations = await canvas_service.get_operations_since(canvas_id, from_version)

                    # Send operations to the client
                    await websocket.send_json({
                        "type": "sync_response",
                        "roomId": room,
                        "operations": operations,
                        "baseVersion": from_version,
                        "currentVersion": current_version
                    })
                except Exception as e:
                    logger.error(f"Error handling sync request: {e}")

                    await websocket.send_json({
                        "type": "error",
                        "roomId": room,
                        "error": "Failed to sync canvas state"
                    })
                continue

            # Handle operations specially
            if message["type"] == "operations":
                await handle_operations(user_id, room, canvas_id, message)
                continue

            # For selection update, broadcast to all users
            if message["type"] == "selection_update":
                await broadcast(room, message)
                continue

            # For any other message, publish to Redis
            await pubsub.publish(channel, message)

    except WebSocketDisconnect:
        # Remove from connections
        if room in connections and user_id in connections[room]:
            del connections[room][user_id]
            if not connections[room]:
                del connections[room]

        # Remove from active users
        if room in active_users and user_id in active_users[room]:
            active_users[room].remove(user_id)
            if not active_users[room]:
                del active_users[room]

        # Broadcast disconnect
        disconnect_message = {
            "type": "presence",
            "roomId": room,
            "userId": user_id,
            "payload": {
                "userId": user_id,
                "status": "inactive",
                "lastActive": datetime.utcnow().isoformat()
            }
        }
        await broadcast(room, disconnect_message)

        # Unsubscribe from Redis
        await pubsub.unsubscribe(f"canvas:{room}", message_callback)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011)

async def handle_operations(user_id: str, room: str, canvas_id: str, message: Dict[str, Any]):
    """Handle canvas operations with operational transformation"""
    try:
        operations = message.get("operations", [])
        base_version = message.get("baseVersion", 0)

        if not operations:
            logger.warning(f"Received empty operations list from user {user_id}")
            return

        # Convert to CanvasOperation objects
        canvas_operations = [CanvasOperation(**op) for op in operations]

        # Apply operations to canvas state with OT
        result = await canvas_service.apply_operations(
            canvas_id=canvas_id,
            operations=canvas_operations,
            base_version=base_version,
            user_id=user_id
        )

        if not result:
            logger.error(f"Failed to apply operations for canvas {canvas_id}")

            # Send error to the client
            if room in connections and user_id in connections[room]:
                await connections[room][user_id].send_json({
                    "type": "operations_error",
                    "roomId": room,
                    "error": "Failed to apply operations",
                    "timestamp": datetime.utcnow().isoformat()
                })
            return

        # Broadcast operations to all users in the room
        ops_message = {
            "type": "operations_applied",
            "roomId": room,
            "userId": user_id,
            "operations": [op.dict() for op in result.operations],
            "baseVersion": base_version,
            "version": result.new_version,
            "timestamp": datetime.utcnow().isoformat()
        }

        await broadcast(room, ops_message)

        # Send transformed operations back to originating client
        if result.needs_transform and room in connections and user_id in connections[room]:
            transform_message = {
                "type": "operations_transformed",
                "roomId": room,
                "operations": [op.dict() for op in result.transformed_operations] if result.transformed_operations else [],
                "baseVersion": base_version,
                "version": result.new_version,
                "timestamp": datetime.utcnow().isoformat()
            }

            await connections[room][user_id].send_json(transform_message)

    except Exception as e:
        logger.error(f"Error handling operations: {e}")

        # Send error to the client
        if room in connections and user_id in connections[room]:
            await connections[room][user_id].send_json({
                "type": "operations_error",
                "roomId": room,
                "error": f"Error processing operations: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })

async def broadcast(room: str, message: Dict[str, Any], exclude_user: Optional[str] = None):
    """Broadcast message to all users in room"""
    if room not in connections:
        return

    # Publish to Redis instead of direct broadcast
    channel = f"canvas:{room}"
    if exclude_user:
        # Add metadata to indicate who to exclude
        message["_exclude_user"] = exclude_user

    await pubsub.publish(channel, message)

@router.on_event("startup")
async def startup_pubsub():
    """Initialize the PubSub system on startup"""
    logger.info("Initializing WebSocket PubSub system")
    # Ensure canvas service is initialized
    await canvas_service.initialize()

@router.on_event("shutdown")
async def shutdown_pubsub():
    """Close the PubSub system on shutdown"""
    logger.info("Closing WebSocket PubSub system")
    await pubsub.close()
    # Close canvas service
    await canvas_service.close()
