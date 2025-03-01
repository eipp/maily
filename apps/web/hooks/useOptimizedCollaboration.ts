import { useState, useEffect, useCallback, useRef } from 'react';
import { OptimizedYjsProvider } from '@/lib/optimized-yjs';
import { canvasPerformance } from '@/utils/canvasPerformance';

interface CollaborationOptions {
  serverUrl: string;
  roomId: string;
  userId: string;
  userName?: string;
  updateThrottleMs?: number;
  updateDebounceMs?: number;
  autoConnect?: boolean;
}

interface CollaborationState {
  isConnected: boolean;
  connectedUsers: any[];
  isLoading: boolean;
  error: Error | null;
}

interface CollaborationActions {
  connect: () => void;
  disconnect: () => void;
  broadcastUpdate: (path: string, update: any) => void;
  getData: (path: string, key?: string) => any;
  updateCursor: (x: number, y: number) => void;
  updateAwareness: (state: Record<string, any>) => void;
}

/**
 * React hook for using the optimized Yjs provider
 */
export function useOptimizedCollaboration(options: CollaborationOptions): [
  CollaborationState,
  CollaborationActions
] {
  const {
    serverUrl,
    roomId,
    userId,
    userName = 'User',
    updateThrottleMs = 50,
    updateDebounceMs = 200,
    autoConnect = true,
  } = options;

  // Provider instance
  const providerRef = useRef<OptimizedYjsProvider | null>(null);

  // State
  const [state, setState] = useState<CollaborationState>({
    isConnected: false,
    connectedUsers: [],
    isLoading: true,
    error: null,
  });

  // Initialize provider
  useEffect(() => {
    canvasPerformance.startMetric('collaboration.initialize');

    try {
      // Create provider instance
      providerRef.current = new OptimizedYjsProvider(
        serverUrl,
        `canvas-${roomId}`,
        userId,
        {
          updateThrottleMs,
          updateDebounceMs,
          connect: autoConnect,
        }
      );

      // Update user info
      providerRef.current.updateAwareness({
        name: userName,
      });

      // Subscribe to connection changes
      const unsubscribeConnection = providerRef.current.onConnectionChange((isConnected) => {
        setState(prev => ({
          ...prev,
          isConnected,
          isLoading: false,
        }));
      });

      // Subscribe to awareness changes
      const unsubscribeAwareness = providerRef.current.onAwarenessChange((awareness) => {
        const users = providerRef.current?.getConnectedUsers() || [];
        setState(prev => ({
          ...prev,
          connectedUsers: users,
        }));
      });

      canvasPerformance.endMetric('collaboration.initialize');

      // Cleanup
      return () => {
        unsubscribeConnection();
        unsubscribeAwareness();

        if (providerRef.current) {
          providerRef.current.destroy();
          providerRef.current = null;
        }
      };
    } catch (error) {
      console.error('Error initializing collaboration:', error);

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error : new Error(String(error)),
      }));

      canvasPerformance.endMetric('collaboration.initialize');

      return () => {};
    }
  }, [serverUrl, roomId, userId, userName, updateThrottleMs, updateDebounceMs, autoConnect]);

  // Connect action
  const connect = useCallback(() => {
    if (providerRef.current) {
      providerRef.current.connect();
    }
  }, []);

  // Disconnect action
  const disconnect = useCallback(() => {
    if (providerRef.current) {
      providerRef.current.disconnect();
    }
  }, []);

  // Broadcast update action
  const broadcastUpdate = useCallback((path: string, update: any) => {
    if (providerRef.current) {
      providerRef.current.broadcastUpdate(path, update);
    }
  }, []);

  // Get data action
  const getData = useCallback((path: string, key?: string) => {
    if (providerRef.current) {
      return providerRef.current.getData(path, key);
    }
    return null;
  }, []);

  // Update cursor action
  const updateCursor = useCallback((x: number, y: number) => {
    if (providerRef.current) {
      providerRef.current.updateCursor(x, y);
    }
  }, []);

  // Update awareness action
  const updateAwareness = useCallback((state: Record<string, any>) => {
    if (providerRef.current) {
      providerRef.current.updateAwareness(state);
    }
  }, []);

  // Actions object
  const actions: CollaborationActions = {
    connect,
    disconnect,
    broadcastUpdate,
    getData,
    updateCursor,
    updateAwareness,
  };

  return [state, actions];
}

/**
 * Throttled version of the updateCursor function
 */
export function useThrottledCursorUpdate(
  updateCursor: (x: number, y: number) => void,
  throttleMs: number = 50
): (x: number, y: number) => void {
  const lastUpdateRef = useRef<{ x: number; y: number } | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const throttledUpdateCursor = useCallback((x: number, y: number) => {
    // Store the latest values
    lastUpdateRef.current = { x, y };

    // If there's already a pending update, don't schedule another one
    if (timeoutRef.current) return;

    // Schedule an update
    timeoutRef.current = setTimeout(() => {
      if (lastUpdateRef.current) {
        updateCursor(lastUpdateRef.current.x, lastUpdateRef.current.y);
      }
      timeoutRef.current = null;
    }, throttleMs);
  }, [updateCursor, throttleMs]);

  // Clean up the timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return throttledUpdateCursor;
}
