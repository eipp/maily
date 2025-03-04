"""
WebSocket Service for real-time communication across services.
This module provides shared functionality for WebSocket connections.
"""

import asyncio
import json
import logging
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from utils.resilience import backoff_retry
from utils.tracing import tracer

logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    """WebSocket message types for standardized communication."""
    CANVAS_UPDATE = "canvas_update"
    AI_RESPONSE = "ai_response"
    CHAT_MESSAGE = "chat_message"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    PREDICTION = "prediction"
    VERIFICATION = "verification"
    PING = "ping"
    PONG = "pong"

class WebSocketMessage(BaseModel):
    """Standard WebSocket message format."""
    type: MessageType
    data: Dict[str, Any]
    sender: str
    # Optional trace ID for distributed tracing
    trace_id: Optional[str] = None

class WebSocketConnectionManager:
    """
    Manages WebSocket connections with standardized messaging.
    Supports:
    - Connection management
    - Message broadcasting
    - Cross-service communication via Redis
    - Message buffering for reconnection
    - Heartbeat mechanism
    """
    
    def __init__(self, redis_client=None):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.connection_groups: Dict[str, Set[str]] = {}
        self.message_buffer: Dict[str, List[WebSocketMessage]] = {}
        self.buffer_size = 100  # Maximum number of messages to buffer per client
        self.redis_client = redis_client
        self.handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }

    async def connect(self, websocket: WebSocket, client_id: str, group: Optional[str] = None) -> None:
        """Accept a WebSocket connection and add it to the active connections."""
        await websocket.accept()
        
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        
        self.active_connections[client_id].append(websocket)
        
        if group:
            if group not in self.connection_groups:
                self.connection_groups[group] = set()
            self.connection_groups[group].add(client_id)
            
        # Send any buffered messages
        await self._send_buffered_messages(client_id, websocket)
            
        # Send a welcome message
        await self.send_personal_message(
            WebSocketMessage(
                type=MessageType.STATUS_UPDATE,
                data={"status": "connected", "message": "Connected to WebSocket server"},
                sender="system"
            ),
            client_id
        )
        
        logger.info(f"Client {client_id} connected to WebSocket. Active connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket, client_id: str, group: Optional[str] = None) -> None:
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            try:
                self.active_connections[client_id].remove(websocket)
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]
            except ValueError:
                logger.warning(f"WebSocket for client {client_id} not found in active connections")
        
        if group and group in self.connection_groups and client_id in self.connection_groups[group]:
            self.connection_groups[group].remove(client_id)
            if not self.connection_groups[group]:
                del self.connection_groups[group]
                
        logger.info(f"Client {client_id} disconnected from WebSocket. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: WebSocketMessage, client_id: str) -> None:
        """Send a message to a specific client."""
        if client_id not in self.active_connections:
            # Buffer the message for later delivery
            self._buffer_message(client_id, message)
            return
            
        with tracer.start_as_current_span("websocket.send_personal_message"):
            connections = self.active_connections[client_id]
            disconnected = []
            
            for connection in connections:
                try:
                    await connection.send_text(message.json())
                except RuntimeError:
                    disconnected.append(connection)
                    
            # Clean up any disconnected websockets
            for connection in disconnected:
                try:
                    self.active_connections[client_id].remove(connection)
                except ValueError:
                    pass
                    
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
                # Buffer the message since the client is disconnected
                self._buffer_message(client_id, message)

    async def broadcast(self, message: WebSocketMessage, group: Optional[str] = None) -> None:
        """Broadcast a message to all connected clients, or a specific group."""
        with tracer.start_as_current_span("websocket.broadcast_message"):
            clients = set()
            
            if group and group in self.connection_groups:
                clients = self.connection_groups[group]
            else:
                clients = set(self.active_connections.keys())
                
            tasks = [self.send_personal_message(message, client) for client in clients]
            await asyncio.gather(*tasks)
            
            # If Redis is available, publish to channel for cross-service communication
            if self.redis_client:
                channel = f"websocket:broadcast:{group}" if group else "websocket:broadcast"
                await self._publish_to_redis(channel, message)

    async def handle_message(self, message: WebSocketMessage) -> None:
        """Process incoming messages and trigger registered handlers."""
        with tracer.start_as_current_span("websocket.handle_message"):
            # Execute any registered handlers for this message type
            if message.type in self.handlers:
                for handler in self.handlers[message.type]:
                    try:
                        await handler(message)
                    except Exception as e:
                        logger.error(f"Error in websocket handler: {e}")
            
            # If Redis is available, publish to channel for cross-service communication
            if self.redis_client:
                await self._publish_to_redis("websocket:message", message)

    async def start_heartbeat(self, interval: int = 30) -> None:
        """Start sending heartbeat messages to keep connections alive."""
        while True:
            heartbeat_msg = WebSocketMessage(
                type=MessageType.PING,
                data={"timestamp": str(asyncio.get_event_loop().time())},
                sender="system"
            )
            
            await self.broadcast(heartbeat_msg)
            await asyncio.sleep(interval)

    @backoff_retry(exceptions=(Exception,), max_tries=3)
    async def _publish_to_redis(self, channel: str, message: WebSocketMessage) -> None:
        """Publish a message to a Redis channel."""
        if not self.redis_client:
            return
            
        try:
            await self.redis_client.publish(channel, message.json())
        except Exception as e:
            logger.error(f"Error publishing to Redis channel {channel}: {e}")
            raise

    async def subscribe_to_redis_channels(self, channels: List[str]) -> None:
        """Subscribe to Redis channels for cross-service communication."""
        if not self.redis_client:
            logger.warning("Redis client not available. Cross-service communication disabled.")
            return
            
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(*channels)
            
            # Start background task to process messages
            asyncio.create_task(self._process_redis_messages(pubsub))
        except Exception as e:
            logger.error(f"Error subscribing to Redis channels: {e}")

    async def _process_redis_messages(self, pubsub) -> None:
        """Process messages from Redis channels."""
        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    try:
                        data = json.loads(message["data"])
                        ws_message = WebSocketMessage(**data)
                        await self.handle_message(ws_message)
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
            except Exception as e:
                logger.error(f"Error getting message from Redis: {e}")
                
            await asyncio.sleep(0.01)

    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Register a handler for a specific message type."""
        if message_type not in self.handlers:
            self.handlers[message_type] = []
        self.handlers[message_type].append(handler)

    def _buffer_message(self, client_id: str, message: WebSocketMessage) -> None:
        """Buffer a message for a client that is not currently connected."""
        if client_id not in self.message_buffer:
            self.message_buffer[client_id] = []
            
        # Add message to buffer, respecting buffer size limit
        buffer = self.message_buffer[client_id]
        buffer.append(message)
        
        # If buffer exceeds limit, remove oldest messages
        if len(buffer) > self.buffer_size:
            self.message_buffer[client_id] = buffer[-self.buffer_size:]

    async def _send_buffered_messages(self, client_id: str, websocket: WebSocket) -> None:
        """Send any buffered messages to a newly connected client."""
        if client_id not in self.message_buffer:
            return
            
        # Send all buffered messages
        for message in self.message_buffer[client_id]:
            try:
                await websocket.send_text(message.json())
            except Exception as e:
                logger.error(f"Error sending buffered message: {e}")
                
        # Clear buffer after sending
        del self.message_buffer[client_id]

    async def listen(self, websocket: WebSocket, client_id: str) -> None:
        """Listen for messages from a WebSocket connection."""
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message_data = json.loads(data)
                    message = WebSocketMessage(**message_data)
                    
                    # Special handling for PING messages
                    if message.type == MessageType.PING:
                        await websocket.send_text(WebSocketMessage(
                            type=MessageType.PONG,
                            data={"timestamp": message.data.get("timestamp")},
                            sender="system"
                        ).json())
                    else:
                        await self.handle_message(message)
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    await websocket.send_text(WebSocketMessage(
                        type=MessageType.ERROR,
                        data={"error": str(e)},
                        sender="system"
                    ).json())
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for client {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error for client {client_id}: {e}")
        finally:
            # Ensure connection is removed on any error
            await self.disconnect(websocket, client_id)

# Global instance
connection_manager = None

async def get_connection_manager(redis_client=None):
    """Get or create a WebSocketConnectionManager instance."""
    global connection_manager
    if connection_manager is None:
        connection_manager = WebSocketConnectionManager(redis_client)
    return connection_manager