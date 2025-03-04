import { useCallback, useEffect, useRef, useState } from 'react';
import { 
  ConnectionState, 
  MessageType, 
  WebSocketConnectionOptions, 
  WebSocketMessage 
} from '../../packages/models/src/shared/WebSocketMessage';

type MessageHandler = (message: WebSocketMessage) => void;

interface UseWebSocketReturn {
  connectionState: ConnectionState;
  sendMessage: (message: WebSocketMessage) => void;
  addMessageHandler: (type: MessageType, handler: MessageHandler) => void;
  removeMessageHandler: (type: MessageType, handler: MessageHandler) => void;
}

const DEFAULT_OPTIONS: WebSocketConnectionOptions = {
  heartbeatInterval: 30000,
  reconnectAttempts: 5,
  reconnectDelay: 2000,
  bufferMessages: true,
};

/**
 * React hook for WebSocket connections with automatic reconnection,
 * heartbeats, and typed message handling
 */
export function useWebSocket(
  url: string,
  options: WebSocketConnectionOptions = {}
): UseWebSocketReturn {
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    ConnectionState.DISCONNECTED
  );
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const messageBufferRef = useRef<WebSocketMessage[]>([]);
  const messageHandlersRef = useRef<Map<MessageType, Set<MessageHandler>>>(new Map());
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Merge default options with provided options
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options };
  
  // Function to establish WebSocket connection
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    try {
      setConnectionState(ConnectionState.CONNECTING);
      
      const authHeader = mergedOptions.authToken 
        ? { Authorization: `Bearer ${mergedOptions.authToken}` }
        : {};
      
      const ws = new WebSocket(url, [], { headers: authHeader });
      
      ws.onopen = () => {
        setConnectionState(ConnectionState.CONNECTED);
        reconnectAttemptsRef.current = 0;
        
        // Send any buffered messages
        if (mergedOptions.bufferMessages && messageBufferRef.current.length > 0) {
          messageBufferRef.current.forEach((msg) => {
            ws.send(JSON.stringify(msg));
          });
          messageBufferRef.current = [];
        }
        
        // Start heartbeat
        if (mergedOptions.heartbeatInterval && mergedOptions.heartbeatInterval > 0) {
          startHeartbeat();
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          
          // Handle PONG messages for heartbeat
          if (message.type === MessageType.PONG) {
            return;
          }
          
          // Dispatch message to registered handlers
          const handlers = messageHandlersRef.current.get(message.type);
          if (handlers) {
            handlers.forEach((handler) => {
              try {
                handler(message);
              } catch (error) {
                console.error('Error in message handler:', error);
              }
            });
          }
          
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onclose = () => {
        setConnectionState(ConnectionState.DISCONNECTED);
        
        // Stop heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }
        
        // Attempt to reconnect
        const maxAttempts = mergedOptions.reconnectAttempts || 0;
        if (maxAttempts === 0 || reconnectAttemptsRef.current < maxAttempts) {
          reconnectAttemptsRef.current += 1;
          setConnectionState(ConnectionState.RECONNECTING);
          
          setTimeout(() => {
            connect();
          }, mergedOptions.reconnectDelay);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionState(ConnectionState.ERROR);
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Error establishing WebSocket connection:', error);
      setConnectionState(ConnectionState.ERROR);
    }
  }, [url, mergedOptions]);
  
  // Start heartbeat interval
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        const pingMessage: WebSocketMessage = {
          type: MessageType.PING,
          data: { timestamp: new Date().toISOString() },
          sender: 'client',
        };
        wsRef.current.send(JSON.stringify(pingMessage));
      }
    }, mergedOptions.heartbeatInterval);
  }, [mergedOptions.heartbeatInterval]);
  
  // Send a message through the WebSocket
  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else if (mergedOptions.bufferMessages) {
      // Buffer the message for when the connection is established
      messageBufferRef.current.push(message);
    }
  }, [mergedOptions.bufferMessages]);
  
  // Add message handler
  const addMessageHandler = useCallback((type: MessageType, handler: MessageHandler) => {
    if (!messageHandlersRef.current.has(type)) {
      messageHandlersRef.current.set(type, new Set());
    }
    messageHandlersRef.current.get(type)!.add(handler);
  }, []);
  
  // Remove message handler
  const removeMessageHandler = useCallback((type: MessageType, handler: MessageHandler) => {
    const handlers = messageHandlersRef.current.get(type);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        messageHandlersRef.current.delete(type);
      }
    }
  }, []);
  
  // Connect on component mount
  useEffect(() => {
    connect();
    
    return () => {
      // Clean up on unmount
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }
    };
  }, [connect]);
  
  return {
    connectionState,
    sendMessage,
    addMessageHandler,
    removeMessageHandler,
  };
}