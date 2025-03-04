/**
 * Shared WebSocket message types and interfaces for cross-service communication
 */

/**
 * Standardized WebSocket message types
 */
export enum MessageType {
  CANVAS_UPDATE = 'canvas_update',
  AI_RESPONSE = 'ai_response',
  CHAT_MESSAGE = 'chat_message',
  STATUS_UPDATE = 'status_update',
  ERROR = 'error', 
  PREDICTION = 'prediction',
  VERIFICATION = 'verification',
  PING = 'ping',
  PONG = 'pong'
}

/**
 * Standard WebSocket message format
 */
export interface WebSocketMessage {
  type: MessageType;
  data: Record<string, any>;
  sender: string;
  trace_id?: string; // Optional trace ID for distributed tracing
}

/**
 * Canvas update message data
 */
export interface CanvasUpdateData {
  canvasId: string;
  operation: 'add' | 'update' | 'delete' | 'move';
  elementId?: string;
  elementType?: string;
  position?: { x: number; y: number };
  size?: { width: number; height: number };
  content?: any;
  metadata?: Record<string, any>;
  userId: string;
  timestamp: string;
}

/**
 * AI response message data
 */
export interface AIResponseData {
  requestId: string;
  content: string;
  status: 'in_progress' | 'completed' | 'error';
  confidence?: number;
  metadata?: Record<string, any>;
  model?: string;
  timestamp: string;
}

/**
 * Chat message data
 */
export interface ChatMessageData {
  messageId: string;
  conversationId: string;
  content: string;
  sender: {
    id: string;
    name: string;
    type: 'user' | 'system' | 'ai';
  };
  timestamp: string;
  metadata?: Record<string, any>;
}

/**
 * Status update message data
 */
export interface StatusUpdateData {
  status: 'connected' | 'disconnected' | 'error' | 'processing' | 'ready';
  message?: string;
  timestamp?: string;
  connectionId?: string;
}

/**
 * Error message data
 */
export interface ErrorData {
  error: string;
  code?: string;
  source?: string;
  timestamp: string;
  requestId?: string;
}

/**
 * Prediction message data
 */
export interface PredictionData {
  predictionId: string;
  type: 'content' | 'engagement' | 'performance' | 'audience';
  prediction: any;
  confidence: number;
  metadata?: Record<string, any>;
  timestamp: string;
}

/**
 * Verification message data
 */
export interface VerificationData {
  entityId: string;
  entityType: 'canvas' | 'email' | 'document' | 'content';
  status: 'verified' | 'unverified' | 'pending';
  verificationId?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

/**
 * Connection options for WebSocket client
 */
export interface WebSocketConnectionOptions {
  heartbeatInterval?: number;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  bufferMessages?: boolean;
  authToken?: string;
}

/**
 * Client connection state
 */
export enum ConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}