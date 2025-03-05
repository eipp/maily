# WebSocket Infrastructure Documentation

This document provides a comprehensive overview of the WebSocket infrastructure implemented in the Maily platform. The WebSocket system enables real-time communication and collaboration features, particularly for the Cognitive Canvas component, AI Mesh Network, and other interactive features.

## Architecture

The WebSocket infrastructure follows a layered architecture that ensures scalability, reliability, and security:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Client        │     │  API Gateway    │     │ WebSocket       │
│   Applications  │────▶│  (Load Balancer)│────▶│ Service         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │ Redis PubSub    │
                                               │ (Message Broker)│
                                               └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Canvas Service │     │  AI Mesh        │     │  Other Service  │
│  (Visualization)│◀───▶│  Network        │◀───▶│  Integrations   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Key Components

1. **Client Applications**: Web and mobile applications that connect to the WebSocket service
2. **API Gateway**: Routes WebSocket connections and handles authentication
3. **WebSocket Service**: Manages connections, authentication, and message routing
4. **Redis PubSub**: Serves as the message broker for distributing messages across services
5. **Canvas Service**: Handles visualization operations for Cognitive Canvas
6. **AI Mesh Network**: Provides AI-driven collaboration and analysis
7. **Service Integrations**: Connects to other services like analytics, email, etc.

## Connection Workflow

Below is the standard connection workflow for WebSocket clients:

1. **Authentication & Connection**:
   ```
   ┌─────────┐                            ┌─────────────┐                  ┌──────────────┐
   │ Client  │                            │ API Gateway │                  │ WebSocket    │
   │         │                            │             │                  │ Service      │
   └────┬────┘                            └──────┬──────┘                  └───────┬──────┘
        │                                        │                                  │
        │  GET /api/v1/ws/connect?token=<JWT>    │                                  │
        │───────────────────────────────────────▶│                                  │
        │                                        │                                  │
        │                                        │    Authenticate & authorize      │
        │                                        │ ─────────────────────────────▶  │
        │                                        │                                  │
        │      Connection established            │                                  │
        │◀──────────────────────────────────────┤                                  │
        │                                        │                                  │
        │      Upgrade to WebSocket             │                                  │
        │◀──────────────────────────────────────┤                                  │
        │                                        │                                  │
   ```

2. **Session Initialization**:
   - After connection, the client receives a unique session ID
   - The server registers the client in its active connections registry
   - Initial state synchronization occurs
   - Subscription to relevant channels is established

## Message Protocol

### Message Format

All WebSocket messages follow a standardized JSON format:

```json
{
  "type": "message_type",
  "sessionId": "unique_session_id",
  "timestamp": "2023-05-20T15:30:00Z",
  "data": {
    // Message-specific payload
  },
  "traceId": "unique_trace_id_for_telemetry"
}
```

### Message Types

#### Client to Server

| Message Type | Description | Example Payload |
| ------------ | ----------- | --------------- |
| `connection_init` | Initialize connection | `{ "clientInfo": { "version": "1.0.0", "platform": "web" } }` |
| `subscribe` | Subscribe to a channel | `{ "channel": "canvas:123", "options": { "history": true } }` |
| `unsubscribe` | Unsubscribe from a channel | `{ "channel": "canvas:123" }` |
| `canvas_update` | Update canvas element | `{ "canvasId": "123", "action": "move", "elementId": "e1", "position": { "x": 100, "y": 200 } }` |
| `cursor_position` | Update cursor position | `{ "canvasId": "123", "position": { "x": 150, "y": 300 } }` |
| `ai_request` | Request AI assistance | `{ "canvasId": "123", "prompt": "Suggest improvements", "context": {} }` |
| `heartbeat` | Keep connection alive | `{ "timestamp": "2023-05-20T15:30:00Z" }` |

#### Server to Client

| Message Type | Description | Example Payload |
| ------------ | ----------- | --------------- |
| `connection_ack` | Connection acknowledged | `{ "sessionId": "sess_123456", "userId": "usr_789" }` |
| `subscribed` | Channel subscription confirmed | `{ "channel": "canvas:123", "participantCount": 5 }` |
| `unsubscribed` | Channel unsubscription confirmed | `{ "channel": "canvas:123" }` |
| `canvas_updated` | Canvas was updated | `{ "canvasId": "123", "action": "move", "elementId": "e1", "position": { "x": 100, "y": 200 }, "user": { "id": "usr_456", "name": "Jane" } }` |
| `cursor_moved` | Cursor position of another user | `{ "canvasId": "123", "position": { "x": 150, "y": 300 }, "user": { "id": "usr_456", "name": "Jane" } }` |
| `ai_response` | AI response to request | `{ "canvasId": "123", "suggestions": [{ "type": "color", "value": "#ff5500" }] }` |
| `error` | Error message | `{ "code": "AUTH_FAILED", "message": "Authentication failed", "original_message_id": "msg_123" }` |
| `heartbeat_ack` | Heartbeat acknowledged | `{ "timestamp": "2023-05-20T15:30:05Z" }` |

## Channel Structure

Channels in the WebSocket infrastructure follow a hierarchical pattern:

```
<resource_type>:<resource_id>[:<sub_resource>]
```

Common channel patterns:

- `canvas:123` - Updates for canvas with ID 123
- `canvas:123:ai` - AI-specific messages for canvas 123
- `canvas:123:cursor` - Cursor movement for canvas 123
- `user:456:notifications` - Notifications for user 456
- `ai_mesh:789` - AI Mesh Network with ID 789

## Security

### Authentication and Authorization

- All WebSocket connections require authentication via JWT tokens
- Tokens include user identity, permissions, and expiry time
- Authorization is verified for each subscription request
- Token refresh mechanism to handle long-lived connections

### Connection Limits

- Per-user connection limits prevent abuse
- Rate limiting on message frequency
- Maximum message size enforcement
- Automatic disconnection for idle connections (configurable timeout)

## Reliability Features

### Reconnection Handling

The system implements automatic reconnection handling with these features:

1. **Exponential Backoff**:
   - Initial retry after 100ms
   - Doubling delay with each retry up to max 30 seconds
   - Maximum 10 reconnection attempts

2. **Session Resumption**:
   - Server maintains active session state for 15 minutes
   - Client sends last message ID on reconnection
   - Server synchronizes missed messages

3. **State Synchronization**:
   - After resumption, client receives state updates
   - Conflict resolution with last-write-wins strategy
   - Version vectors for multi-user editing scenarios

### Error Handling

Error responses follow this format:

```json
{
  "type": "error",
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "timestamp": "2023-05-20T15:30:00Z",
  "original_message_id": "id_of_message_that_caused_error",
  "traceId": "trace_id_for_debugging"
}
```

Common error codes:

| Code | Description |
| ---- | ----------- |
| `AUTH_FAILED` | Authentication failure |
| `FORBIDDEN` | Authorization failure |
| `INVALID_MESSAGE` | Malformed message |
| `RATE_LIMITED` | Too many messages |
| `SUBSCRIPTION_FAILED` | Failed to subscribe to channel |
| `INTERNAL_ERROR` | Server-side error |

## Tracing and Monitoring

### Telemetry Integration

The WebSocket service implements comprehensive telemetry:

1. **Distributed Tracing**:
   - Each message has a unique `traceId`
   - Integration with OpenTelemetry
   - End-to-end tracing across services

2. **Metrics Collection**:
   - Active connections count
   - Message rate (in/out)
   - Error rate
   - WebSocket service latency
   - Channel subscription count

3. **Logging**:
   - Structured logs with correlation IDs
   - Connection lifecycle events
   - Error conditions with context
   - User authentication events

### Performance Monitoring

Key performance indicators tracked:

- WebSocket connection establishment time
- Message delivery latency
- Client reconnection frequency
- Subscription processing time
- Redis PubSub latency

## Implementation Details

### WebSocket Service Implementation

The WebSocket service is implemented in Python using FastAPI and WebSockets:

```python
# Example WebSocket router implementation
from fastapi import APIRouter, WebSocket, Depends, HTTPException
from typing import Dict, List, Any, Optional
import json
import asyncio
import logging
from utils.tracing import get_tracer, trace_websocket
from utils.redis_client import get_redis

router = APIRouter()
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = generate_session_id()
    active_connections[session_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Extract trace information
            trace_id = message.get("traceId", generate_trace_id())
            
            # Process message with tracing
            with trace_websocket(trace_id, message.get("type")):
                await process_message(session_id, message, websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}", exc_info=True)
    finally:
        if session_id in active_connections:
            del active_connections[session_id]
```

### Redis PubSub Integration

```python
async def subscribe_to_channel(session_id: str, channel: str, websocket: WebSocket):
    """Subscribe a client to a Redis PubSub channel."""
    redis = await get_redis()
    
    # Register subscription in session tracking
    await redis.sadd(f"sessions:{session_id}:channels", channel)
    await redis.sadd(f"channels:{channel}:sessions", session_id)
    
    # Setup Redis PubSub
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    
    # Start background task to listen for messages
    asyncio.create_task(channel_listener(channel, pubsub, session_id, websocket))
    
    # Notify client of successful subscription
    await websocket.send_json({
        "type": "subscribed",
        "sessionId": session_id,
        "channel": channel,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "participantCount": await redis.scard(f"channels:{channel}:sessions")
        }
    })

async def channel_listener(channel: str, pubsub, session_id: str, websocket: WebSocket):
    """Listen for messages on a Redis PubSub channel and forward to WebSocket."""
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                
                # Skip messages from the same session (avoid echo)
                if data.get("sessionId") == session_id:
                    continue
                    
                # Forward message to WebSocket client
                await websocket.send_json(data)
    except Exception as e:
        logging.error(f"Channel listener error: {str(e)}", exc_info=True)
    finally:
        # Clean up subscriptions
        await pubsub.unsubscribe(channel)
```

## Canvas-Specific Features

### Real-time Collaboration

The WebSocket infrastructure enables these collaboration features in the Cognitive Canvas:

1. **Multi-user Editing**:
   - Real-time updates of canvas elements
   - Conflict resolution with operational transforms
   - Element locking to prevent simultaneous edits

2. **Cursor Tracking**:
   - Real-time cursor position sharing
   - User identification and avatars
   - Activity indication (idle/active)

3. **Layer Control**:
   - Layer visibility synchronization
   - Layer locking and permissions
   - Layer-specific notifications

### AI Integration

The Canvas connects to the AI Mesh Network through WebSockets for:

1. **Real-time Analysis**:
   - Element placement suggestions
   - Design consistency checking
   - Accessibility recommendations

2. **Collaborative AI**:
   - AI agent participation in design process
   - Design critique and feedback
   - Smart element creation and positioning

3. **Trust Verification**:
   - Content safety verification
   - Design compliance checks
   - Real-time verification status updates

## Performance Optimization

### Message Batching

For high-frequency updates (like cursor movement), messages are batched:

```javascript
// Client-side batching example
class WebSocketManager {
  constructor() {
    this.cursorUpdateQueue = [];
    this.batchInterval = 50; // ms
    this.batchTimer = null;
  }
  
  queueCursorUpdate(position) {
    this.cursorUpdateQueue.push({
      x: position.x,
      y: position.y,
      timestamp: Date.now()
    });
    
    if (!this.batchTimer) {
      this.batchTimer = setTimeout(() => this.sendCursorBatch(), this.batchInterval);
    }
  }
  
  sendCursorBatch() {
    if (this.cursorUpdateQueue.length > 0) {
      this.send({
        type: "cursor_batch",
        positions: this.cursorUpdateQueue
      });
      this.cursorUpdateQueue = [];
    }
    this.batchTimer = null;
  }
}
```

### Binary Protocol

For performance-critical applications, binary message protocol is available:

1. **MessagePack Serialization**:
   - Reduced message size compared to JSON
   - Faster serialization/deserialization
   - Support for binary data

2. **Custom Binary Format**:
   - For high-frequency updates like cursor positions
   - Reduced overhead for telemetry data
   - Optimized for network bandwidth

## Usage Examples

### Client-Side Connection

Example using the WebSocket in a web application:

```typescript
// WebSocket client implementation
class MailyWebSocket {
  private socket: WebSocket | null = null;
  private sessionId: string | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: any = null;
  private messageHandlers: Map<string, Function[]> = new Map();
  
  constructor(private authToken: string) {}
  
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const url = `wss://api.maily.com/ws?token=${this.authToken}`;
        this.socket = new WebSocket(url);
        
        this.socket.onopen = () => {
          // Reset reconnection attempts on successful connection
          this.reconnectAttempts = 0;
          
          // Initialize connection
          this.send({
            type: "connection_init",
            timestamp: new Date().toISOString(),
            data: {
              clientInfo: {
                version: APP_VERSION,
                platform: 'web'
              }
            }
          });
          
          resolve();
        };
        
        this.socket.onclose = (event) => {
          // Handle reconnection
          if (!event.wasClean) {
            this.scheduleReconnect();
          }
        };
        
        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
        
        this.socket.onmessage = (event) => {
          const message = JSON.parse(event.data);
          
          // Handle connection acknowledgment
          if (message.type === 'connection_ack') {
            this.sessionId = message.sessionId;
          }
          
          // Dispatch message to registered handlers
          this.dispatchMessage(message);
        };
      } catch (error) {
        reject(error);
      }
    });
  }
  
  public subscribe(channel: string, options: any = {}): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }
    
    this.send({
      type: "subscribe",
      sessionId: this.sessionId,
      timestamp: new Date().toISOString(),
      data: {
        channel,
        options
      }
    });
  }
  
  public send(message: any): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }
    
    // Add trace ID and session ID if not provided
    if (!message.traceId) {
      message.traceId = generateTraceId();
    }
    
    if (this.sessionId && !message.sessionId) {
      message.sessionId = this.sessionId;
    }
    
    this.socket.send(JSON.stringify(message));
  }
  
  public on(messageType: string, handler: Function): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    
    this.messageHandlers.get(messageType)!.push(handler);
  }
  
  private dispatchMessage(message: any): void {
    if (this.messageHandlers.has(message.type)) {
      for (const handler of this.messageHandlers.get(message.type)!) {
        handler(message);
      }
    }
  }
  
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    
    // Exponential backoff with jitter
    const delay = Math.min(1000 * (2 ** this.reconnectAttempts) + Math.random() * 1000, 30000);
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect().catch(() => {
        // If reconnection fails, schedule another attempt
        if (this.reconnectAttempts < 10) {
          this.scheduleReconnect();
        }
      });
    }, delay);
  }
}
```

### Canvas Collaboration Example

```typescript
// Canvas collaboration implementation
class CollaborativeCanvas {
  private websocket: MailyWebSocket;
  private canvasId: string;
  private localUser: User;
  
  constructor(canvasId: string, authToken: string, user: User) {
    this.canvasId = canvasId;
    this.localUser = user;
    this.websocket = new MailyWebSocket(authToken);
    
    // Setup event handlers
    this.websocket.on('canvas_updated', this.handleCanvasUpdate.bind(this));
    this.websocket.on('cursor_moved', this.handleCursorMove.bind(this));
    this.websocket.on('ai_response', this.handleAIResponse.bind(this));
  }
  
  public async connect(): Promise<void> {
    await this.websocket.connect();
    
    // Subscribe to canvas channels
    this.websocket.subscribe(`canvas:${this.canvasId}`);
    this.websocket.subscribe(`canvas:${this.canvasId}:cursor`);
    this.websocket.subscribe(`canvas:${this.canvasId}:ai`);
    
    // Start cursor tracking
    this.startCursorTracking();
  }
  
  public updateElement(elementId: string, properties: any): void {
    this.websocket.send({
      type: "canvas_update",
      data: {
        canvasId: this.canvasId,
        action: "update",
        elementId,
        properties,
        user: {
          id: this.localUser.id,
          name: this.localUser.name
        }
      }
    });
  }
  
  public requestAIAssistance(prompt: string): void {
    this.websocket.send({
      type: "ai_request",
      data: {
        canvasId: this.canvasId,
        prompt,
        context: {
          selectedElements: this.getSelectedElementIds()
        }
      }
    });
  }
  
  private handleCanvasUpdate(message: any): void {
    const { action, elementId, properties, user } = message.data;
    
    // Skip updates from the local user
    if (user.id === this.localUser.id) {
      return;
    }
    
    // Apply the update to the canvas
    switch (action) {
      case 'add':
        this.addElement(elementId, properties);
        break;
      case 'update':
        this.updateElementLocal(elementId, properties);
        break;
      case 'delete':
        this.deleteElement(elementId);
        break;
    }
    
    // Show notification of change
    this.showUserActivity(user, action);
  }
  
  private handleCursorMove(message: any): void {
    const { position, user } = message.data;
    
    // Skip cursor updates from the local user
    if (user.id === this.localUser.id) {
      return;
    }
    
    // Update remote cursor position
    this.updateRemoteCursor(user.id, position, user);
  }
  
  private handleAIResponse(message: any): void {
    const { suggestions } = message.data;
    
    // Display AI suggestions to the user
    this.showAISuggestions(suggestions);
  }
  
  // Additional methods and implementation details...
}
```

## Scaling Considerations

### Horizontal Scaling

The WebSocket infrastructure is designed for horizontal scaling:

1. **Connection Balancing**:
   - Load balancer with sticky sessions
   - Redis-based session lookup for routing
   - Cross-node communication via Redis PubSub

2. **WebSocket Clustering**:
   - Multiple WebSocket server instances
   - Shared state through Redis
   - Connection migration on server failure

3. **Regional Distribution**:
   - Geographic distribution of WebSocket servers
   - Client routing to nearest region
   - Cross-region synchronization for global canvases

### Performance Limits

Current system performance limits:

- Maximum 100,000 concurrent WebSocket connections per cluster
- Maximum 1,000 concurrent users per canvas
- Message rate limit of 100 messages per second per user
- Maximum message size of 64KB
- Maximum 100 channels per client

## Troubleshooting

### Common Issues

1. **Connection Failures**:
   - Check authentication token validity
   - Verify network connectivity
   - Check WebSocket server status

2. **Message Delivery Issues**:
   - Verify subscription to correct channels
   - Check message format and structure
   - Look for rate-limiting errors

3. **Performance Problems**:
   - Reduce message frequency
   - Implement message batching
   - Minimize payload size

### Debugging Tools

For debugging WebSocket connections:

1. **Client-side Debugging**:
   - Browser DevTools Network tab (WS filter)
   - WebSocket frame inspector
   - Console logging with traceId

2. **Server-side Debugging**:
   - Structured logs with correlation IDs
   - OpenTelemetry tracing spans
   - Redis PubSub monitoring tools

## Conclusion

The WebSocket infrastructure provides a robust foundation for real-time collaboration and interactive features in the Maily platform. It enables seamless multi-user editing, AI-assisted creation, and real-time feedback for the Cognitive Canvas and other components.