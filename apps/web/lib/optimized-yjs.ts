import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';
import { throttle, debounce } from 'lodash';
import { canvasPerformance } from '@/utils/canvasPerformance';

/**
 * OptimizedYjsProvider
 *
 * An optimized wrapper around the Yjs WebsocketProvider that implements:
 * - Throttling for high-frequency updates
 * - Performance monitoring
 * - Batched updates
 * - Connection state management
 */
export class OptimizedYjsProvider {
  private doc: Y.Doc;
  private provider: WebsocketProvider;
  private roomName: string;
  private userId: string;
  private isConnected: boolean = false;
  private pendingUpdates: Map<string, any> = new Map();
  private updateCallbacks: Set<(update: any) => void> = new Set();
  private syncCallbacks: Set<() => void> = new Set();
  private connectionCallbacks: Set<(isConnected: boolean) => void> = new Set();
  private awarenessCallbacks: Set<(awareness: Map<number, any>) => void> = new Set();

  // Throttled functions
  private throttledBroadcastUpdate: (path: string, update: any) => void;
  private debouncedProcessPendingUpdates: () => void;

  constructor(
    serverUrl: string,
    roomName: string,
    userId: string,
    options: {
      updateThrottleMs?: number;
      updateDebounceMs?: number;
      connect?: boolean;
    } = {}
  ) {
    const {
      updateThrottleMs = 50,
      updateDebounceMs = 200,
      connect = true,
    } = options;

    this.roomName = roomName;
    this.userId = userId;

    // Create Yjs document
    this.doc = new Y.Doc();

    // Create WebSocket provider
    this.provider = new WebsocketProvider(
      serverUrl,
      roomName,
      this.doc,
      {
        connect,
        awareness: {
          // Set local user data
          clientID: Math.floor(Math.random() * 100000000),
          timeout: 30000,
        },
      }
    );

    // Set up awareness
    this.provider.awareness.setLocalStateField('user', {
      id: userId,
      name: 'User',
      color: `#${Math.floor(Math.random() * 16777215).toString(16)}`,
      timestamp: new Date().toISOString(),
    });

    // Set up event listeners
    this.setupEventListeners();

    // Create throttled update function
    this.throttledBroadcastUpdate = throttle(
      (path: string, update: any) => {
        this.broadcastUpdateImmediate(path, update);
      },
      updateThrottleMs,
      { leading: true, trailing: true }
    );

    // Create debounced function to process pending updates
    this.debouncedProcessPendingUpdates = debounce(
      () => {
        this.processPendingUpdates();
      },
      updateDebounceMs,
      { maxWait: updateDebounceMs * 2 }
    );
  }

  /**
   * Set up event listeners for the Yjs document and provider
   */
  private setupEventListeners(): void {
    // Listen for connection status changes
    this.provider.on('status', ({ status }: { status: string }) => {
      const isConnected = status === 'connected';
      this.isConnected = isConnected;

      // Notify connection listeners
      this.connectionCallbacks.forEach(callback => {
        callback(isConnected);
      });

      // Measure connection performance
      if (isConnected) {
        canvasPerformance.endMetric('collaboration.connect');
      } else {
        canvasPerformance.startMetric('collaboration.connect');
      }
    });

    // Listen for document updates
    this.doc.on('update', (update: Uint8Array, origin: any) => {
      // Skip updates from self
      if (origin === this.provider) return;

      canvasPerformance.startMetric('collaboration.update');

      // Process updates from other clients
      this.processRemoteUpdate(update);

      canvasPerformance.endMetric('collaboration.update');
    });

    // Listen for awareness updates
    this.provider.awareness.on('change', () => {
      const states = this.provider.awareness.getStates();

      // Notify awareness listeners
      this.awarenessCallbacks.forEach(callback => {
        callback(states);
      });
    });
  }

  /**
   * Process updates from remote clients
   */
  private processRemoteUpdate(update: Uint8Array): void {
    // Notify update listeners
    this.updateCallbacks.forEach(callback => {
      callback(update);
    });
  }

  /**
   * Process all pending updates in a batch
   */
  private processPendingUpdates(): void {
    if (this.pendingUpdates.size === 0) return;

    canvasPerformance.startMetric('collaboration.batchUpdate', {
      updateCount: this.pendingUpdates.size,
    });

    // Create a transaction to batch all updates
    this.doc.transact(() => {
      this.pendingUpdates.forEach((update, path) => {
        this.applyUpdate(path, update);
      });
    }, this.provider);

    // Clear pending updates
    this.pendingUpdates.clear();

    canvasPerformance.endMetric('collaboration.batchUpdate');
  }

  /**
   * Apply an update to the Yjs document
   */
  private applyUpdate(path: string, update: any): void {
    try {
      // Get or create the shared map for this path
      const sharedMap = this.doc.getMap(path);

      // Apply the update based on its type
      if (typeof update === 'object' && update !== null) {
        Object.entries(update).forEach(([key, value]) => {
          sharedMap.set(key, value);
        });
      } else {
        // For primitive values, use a default key
        sharedMap.set('value', update);
      }
    } catch (error) {
      console.error('Error applying update to Yjs document:', error);
    }
  }

  /**
   * Broadcast an update immediately without throttling
   */
  private broadcastUpdateImmediate(path: string, update: any): void {
    if (!this.isConnected) {
      // Queue update for when connection is restored
      this.pendingUpdates.set(path, update);
      return;
    }

    canvasPerformance.startMetric('collaboration.broadcastUpdate', {
      path,
      updateSize: JSON.stringify(update).length,
    });

    this.applyUpdate(path, update);

    canvasPerformance.endMetric('collaboration.broadcastUpdate');
  }

  /**
   * Broadcast an update to all clients (throttled)
   */
  broadcastUpdate(path: string, update: any): void {
    // Store in pending updates
    this.pendingUpdates.set(path, update);

    // Throttle the update
    this.throttledBroadcastUpdate(path, update);

    // Schedule processing of pending updates
    this.debouncedProcessPendingUpdates();
  }

  /**
   * Get data from the Yjs document
   */
  getData(path: string, key?: string): any {
    const sharedMap = this.doc.getMap(path);

    if (key) {
      return sharedMap.get(key);
    } else {
      // Convert to regular object
      const data: Record<string, any> = {};
      sharedMap.forEach((value, key) => {
        data[key] = value;
      });
      return data;
    }
  }

  /**
   * Subscribe to updates
   */
  onUpdate(callback: (update: any) => void): () => void {
    this.updateCallbacks.add(callback);

    // Return unsubscribe function
    return () => {
      this.updateCallbacks.delete(callback);
    };
  }

  /**
   * Subscribe to connection state changes
   */
  onConnectionChange(callback: (isConnected: boolean) => void): () => void {
    this.connectionCallbacks.add(callback);
    callback(this.isConnected);

    // Return unsubscribe function
    return () => {
      this.connectionCallbacks.delete(callback);
    };
  }

  /**
   * Subscribe to awareness changes
   */
  onAwarenessChange(callback: (awareness: Map<number, any>) => void): () => void {
    this.awarenessCallbacks.add(callback);
    callback(this.provider.awareness.getStates());

    // Return unsubscribe function
    return () => {
      this.awarenessCallbacks.delete(callback);
    };
  }

  /**
   * Subscribe to document sync completion
   */
  onSync(callback: () => void): () => void {
    this.syncCallbacks.add(callback);

    // Return unsubscribe function
    return () => {
      this.syncCallbacks.delete(callback);
    };
  }

  /**
   * Update user awareness state
   */
  updateAwareness(state: Record<string, any>): void {
    const currentState = this.provider.awareness.getLocalState() || {};

    this.provider.awareness.setLocalStateField('user', {
      ...currentState.user,
      ...state,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Update cursor position in awareness
   */
  updateCursor(x: number, y: number): void {
    this.updateAwareness({
      cursor: { x, y }
    });
  }

  /**
   * Get all connected users
   */
  getConnectedUsers(): any[] {
    const states = this.provider.awareness.getStates();
    const users: any[] = [];

    states.forEach((state, clientId) => {
      if (state.user) {
        users.push({
          ...state.user,
          clientId,
        });
      }
    });

    return users;
  }

  /**
   * Connect to the collaboration server
   */
  connect(): void {
    if (!this.provider.wsconnected) {
      canvasPerformance.startMetric('collaboration.connect');
      this.provider.connect();
    }
  }

  /**
   * Disconnect from the collaboration server
   */
  disconnect(): void {
    this.provider.disconnect();
  }

  /**
   * Destroy the provider and clean up resources
   */
  destroy(): void {
    this.disconnect();
    this.doc.destroy();
  }
}

/**
 * Create a hook for using the OptimizedYjsProvider in React components
 */
export function createOptimizedYjsHook() {
  let providerInstance: OptimizedYjsProvider | null = null;

  return function useOptimizedYjs(
    serverUrl: string,
    roomName: string,
    userId: string,
    options: {
      updateThrottleMs?: number;
      updateDebounceMs?: number;
      connect?: boolean;
    } = {}
  ): OptimizedYjsProvider {
    if (!providerInstance) {
      providerInstance = new OptimizedYjsProvider(serverUrl, roomName, userId, options);
    }

    return providerInstance;
  };
}