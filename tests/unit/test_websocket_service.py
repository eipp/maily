"""
Unit tests for WebSocket service implementation.
Tests the real-time communication capabilities for the canvas visualization service.
"""

import unittest
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from apps.api.services.websocket_service import (
    WebSocketConnectionManager, 
    WebSocketMessage, 
    MessageType
)

# Mock for WebSocket
class MockWebSocket:
    def __init__(self):
        self.sent_messages = []
        self.closed = False
        self.close_code = None
        
    async def accept(self):
        pass
        
    async def send_text(self, text):
        self.sent_messages.append(text)
        
    async def send_json(self, data):
        self.sent_messages.append(json.dumps(data))
        
    async def close(self, code=1000):
        self.closed = True
        self.close_code = code
        
    def get_sent_messages(self):
        return self.sent_messages


class TestWebSocketService(unittest.TestCase):
    """Tests for the WebSocket service."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a connection manager with mock Redis client
        self.redis_client = AsyncMock()
        self.connection_manager = WebSocketConnectionManager(self.redis_client)
        
        # Prepare test data
        self.client_id = "test_client"
        self.group = "test_group"
        self.websocket = MockWebSocket()
        
    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        """Test connecting and disconnecting a WebSocket."""
        # Connect
        await self.connection_manager.connect(self.websocket, self.client_id, self.group)
        
        # Verify connection was added
        self.assertIn(self.client_id, self.connection_manager.active_connections)
        self.assertIn(self.client_id, self.connection_manager.connection_groups[self.group])
        
        # Verify welcome message was sent
        self.assertEqual(len(self.websocket.sent_messages), 1)
        welcome_msg = json.loads(self.websocket.sent_messages[0])
        self.assertEqual(welcome_msg["type"], "STATUS_UPDATE")
        
        # Disconnect
        await self.connection_manager.disconnect(self.websocket, self.client_id, self.group)
        
        # Verify connection was removed
        self.assertNotIn(self.client_id, self.connection_manager.active_connections)
        self.assertNotIn(self.client_id, self.connection_manager.connection_groups.get(self.group, []))
        
    @pytest.mark.asyncio
    async def test_personal_message(self):
        """Test sending a personal message to a client."""
        # Connect
        await self.connection_manager.connect(self.websocket, self.client_id, self.group)
        
        # Clear messages from connection
        self.websocket.sent_messages = []
        
        # Create test message
        test_message = WebSocketMessage(
            type=MessageType.CANVAS_UPDATE,
            data={"test": "data"},
            sender="test_sender"
        )
        
        # Send message
        await self.connection_manager.send_personal_message(test_message, self.client_id)
        
        # Verify message was sent
        self.assertEqual(len(self.websocket.sent_messages), 1)
        sent_msg = json.loads(self.websocket.sent_messages[0])
        self.assertEqual(sent_msg["type"], "CANVAS_UPDATE")
        self.assertEqual(sent_msg["data"]["test"], "data")
        
    @pytest.mark.asyncio
    async def test_broadcast_to_group(self):
        """Test broadcasting a message to a group."""
        # Connect two clients to the same group
        websocket2 = MockWebSocket()
        client_id2 = "test_client2"
        
        await self.connection_manager.connect(self.websocket, self.client_id, self.group)
        await self.connection_manager.connect(websocket2, client_id2, self.group)
        
        # Clear connection messages
        self.websocket.sent_messages = []
        websocket2.sent_messages = []
        
        # Create test message
        test_message = WebSocketMessage(
            type=MessageType.CANVAS_UPDATE,
            data={"test": "broadcast"},
            sender="test_sender"
        )
        
        # Broadcast message
        await self.connection_manager.broadcast(test_message, self.group)
        
        # Verify both clients received the message
        self.assertEqual(len(self.websocket.sent_messages), 1)
        self.assertEqual(len(websocket2.sent_messages), 1)
        
        # Verify Redis publish was called for cross-service communication
        self.redis_client.publish.assert_called_once()
        
    @pytest.mark.asyncio  
    async def test_message_buffer(self):
        """Test buffering messages for disconnected clients."""
        # Create test message
        test_message = WebSocketMessage(
            type=MessageType.CANVAS_UPDATE,
            data={"test": "buffer"},
            sender="test_sender"
        )
        
        # Send message to non-existent client (should be buffered)
        await self.connection_manager.send_personal_message(test_message, "offline_client")
        
        # Verify message was buffered
        self.assertIn("offline_client", self.connection_manager.message_buffer)
        self.assertEqual(len(self.connection_manager.message_buffer["offline_client"]), 1)
        
        # Connect client and verify buffered message is sent
        offline_socket = MockWebSocket()
        await self.connection_manager.connect(offline_socket, "offline_client")
        
        # Verify buffered message was sent and buffer was cleared
        self.assertEqual(len(offline_socket.sent_messages), 2)  # Welcome + buffered
        self.assertNotIn("offline_client", self.connection_manager.message_buffer)
        
    @pytest.mark.asyncio
    async def test_heartbeat(self):
        """Test heartbeat mechanism."""
        # Mock asyncio.sleep to avoid actual waiting
        original_sleep = asyncio.sleep
        asyncio.sleep = AsyncMock()
        
        try:
            # Start heartbeat in background task
            heartbeat_task = asyncio.create_task(self.connection_manager.start_heartbeat(interval=1))
            
            # Connect client
            await self.connection_manager.connect(self.websocket, self.client_id)
            
            # Clear connection messages
            self.websocket.sent_messages = []
            
            # Manually trigger one heartbeat cycle
            await original_sleep(0.1)
            await self.connection_manager.broadcast(
                WebSocketMessage(
                    type=MessageType.PING,
                    data={"timestamp": str(asyncio.get_event_loop().time())},
                    sender="system"
                )
            )
            
            # Verify ping message was sent
            self.assertEqual(len(self.websocket.sent_messages), 1)
            ping_msg = json.loads(self.websocket.sent_messages[0])
            self.assertEqual(ping_msg["type"], "PING")
            
            # Cancel heartbeat task
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        finally:
            # Restore asyncio.sleep
            asyncio.sleep = original_sleep


@pytest.mark.asyncio
async def test_canvas_websocket_integration():
    """Integration test with canvas and WebSocket service."""
    # Import canvas services
    from apps.api.services.visualization_service import get_visualization_service
    from apps.api.services.websocket_service import get_connection_manager
    
    # Create mock WebSocket
    mock_websocket = MockWebSocket()
    
    # Get connection manager
    connection_manager = WebSocketConnectionManager()
    
    # Get visualization service
    visualization_service = get_visualization_service()
    
    # Initialize visualization service
    if not getattr(visualization_service, "initialized", False):
        await visualization_service.initialize()
    
    # Create test canvas ID and room
    canvas_id = "test_canvas_123"
    room_id = f"room_{canvas_id}"
    
    # Connect to WebSocket
    client_id = "test_user_456"
    
    try:
        # Connect client
        await connection_manager.connect(mock_websocket, client_id, room_id)
        
        # Get visualization layers
        layers = await visualization_service.get_visualization_layers(canvas_id)
        
        # Verify default layers were created
        assert "ai_reasoning" in layers
        assert "performance" in layers
        assert "trust_verification" in layers
        
        # Update a layer
        updated_layer = await visualization_service.update_ai_reasoning_layer(
            canvas_id=canvas_id,
            confidence_scores={"score1": 0.9, "score2": 0.8},
            reasoning_steps=[{"label": "Step 1", "content": "Test content"}],
            model_info={"model": "test_model"}
        )
        
        # Verify layer was updated
        assert updated_layer["confidence_scores"]["score1"] == 0.9
        
        # Check if message was sent via websocket
        messages = mock_websocket.get_sent_messages()
        assert len(messages) >= 1  # We should have at least the welcome message
        
        # Now test performance layer update
        updated_performance = await visualization_service.update_performance_layer(
            canvas_id=canvas_id,
            metrics={"open_rate": {"value": 0.25, "unit": "%"}},
            historical_data=[{"date": "2025-03-01", "open_rate": 0.22}, {"date": "2025-03-02", "open_rate": 0.25}],
            benchmarks={"industry": {"open_rate": 0.21}}
        )
        
        # Verify performance layer was updated
        assert updated_performance["metrics"]["open_rate"]["value"] == 0.25
        
        # Test layer visibility updates
        updated_visibility = await visualization_service.update_layer_visibility(
            canvas_id=canvas_id,
            layer_id="performance",
            visible=True,
            opacity=0.8
        )
        
        # Verify visibility was updated
        assert updated_visibility["visible"] is True
        assert updated_visibility["opacity"] == 0.8
        
    finally:
        # Cleanup
        await connection_manager.disconnect(mock_websocket, client_id, room_id)


if __name__ == "__main__":
    unittest.main()