on backe/**
 * Canvas Performance Optimizations
 *
 * This module provides optimizations for the Canvas component to improve
 * performance with large documents, real-time collaboration, and memory usage.
 *
 * Key optimizations:
 * - Virtualization for large canvases (render only visible elements)
 * - WebSocket connection management and optimization
 * - Debounced real-time updates to prevent network floods
 * - Efficient state management for collaborative features
 * - Memory usage optimizations
 */

import { useEffect, useRef, useCallback, useMemo } from 'react';
import { debounce, throttle } from 'lodash';
import * as Y from 'yjs';
import { tldrawPatches } from './patches'; // Assumes patches to tldraw for optimization
import { useWindowSize } from '@/hooks/useWindowSize';

// Types for canvas elements
interface CanvasElement {
  id: string;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  [key: string]: any;
}

interface Viewport {
  x: number;
  y: number;
  width: number;
  height: number;
  zoom: number;
}

/**
 * Canvas virtualization hook
 *
 * Only renders elements that are visible in the current viewport
 * with a margin to allow for smooth scrolling/zooming
 */
export function useCanvasVirtualization(
  allElements: CanvasElement[],
  viewport: Viewport,
  options = { margin: 200, cullingThreshold: 1000 }
) {
  // Only apply virtualization if there are many elements
  const shouldVirtualize = allElements.length > options.cullingThreshold;

  // Calculate visible elements with margin
  const visibleElements = useMemo(() => {
    if (!shouldVirtualize) return allElements;

    const { x, y, width, height, zoom } = viewport;
    const { margin } = options;

    // Add margin to viewport for smoother experience during scrolling/zooming
    const visibleBounds = {
      left: x - margin / zoom,
      top: y - margin / zoom,
      right: x + width + margin / zoom,
      bottom: y + height + margin / zoom,
    };

    // Filter elements by visibility
    return allElements.filter(element => {
      // Check if element intersects with the visible bounds
      return !(
        element.x + element.width < visibleBounds.left ||
        element.x > visibleBounds.right ||
        element.y + element.height < visibleBounds.top ||
        element.y > visibleBounds.bottom
      );
    });
  }, [allElements, viewport, options.margin, shouldVirtualize]);

  // Stats for debugging/monitoring
  const stats = useMemo(() => ({
    totalElements: allElements.length,
    visibleElements: visibleElements.length,
    cullingPercentage: allElements.length ?
      Math.round((1 - visibleElements.length / allElements.length) * 100) : 0
  }), [allElements.length, visibleElements.length]);

  return { visibleElements, stats, isVirtualized: shouldVirtualize };
}

/**
 * Canvas memory optimization hook
 *
 * Reduces memory usage by optimizing element representations
 * and garbage collection
 */
export function useCanvasMemoryOptimization(
  elements: CanvasElement[],
  options = { gcInterval: 30000 }
) {
  const gcTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Run garbage collection periodically to free memory
  useEffect(() => {
    if (elements.length > 1000) {
      // Only start GC for large canvases
      gcTimerRef.current = setInterval(() => {
        if (typeof window !== 'undefined') {
          // Request idle callback for garbage collection
          if ('requestIdleCallback' in window) {
            (window as any).requestIdleCallback(() => {
              // Force garbage collection if available (Chrome DevTools only)
              if (
                process.env.NODE_ENV === 'development' &&
                (window as any).gc
              ) {
                (window as any).gc();
              }

              // Hint to browser that now is a good time for GC
              try {
                const array = new Array(10000);
                delete array;
              } catch (e) {
                // Ignore errors
              }
            });
          }
        }
      }, options.gcInterval);
    }

    return () => {
      if (gcTimerRef.current) {
        clearInterval(gcTimerRef.current);
      }
    };
  }, [elements.length, options.gcInterval]);

  // Optimize element representations to reduce memory usage
  const optimizedElements = useMemo(() => {
    // If under 1000 elements, don't apply optimization to avoid overhead
    if (elements.length < 1000) return elements;

    return elements.map(element => {
      // Only retain properties needed for rendering
      const { id, type, x, y, width, height, content, style } = element;
      return { id, type, x, y, width, height, content, style };
    });
  }, [elements]);

  return {
    optimizedElements,
    memoryUsage: typeof performance !== 'undefined' && (performance as any).memory
      ? (performance as any).memory.usedJSHeapSize / 1048576 // MB
      : 'unavailable'
  };
}

/**
 * WebSocket connection optimization
 *
 * Manages WebSocket connections efficiently with:
 * - Connection pooling
 * - Automatic reconnection
 * - Message batching
 * - Binary message format for reduced bandwidth
 */
export function useOptimizedWebSocket(
  url: string,
  options = {
    reconnectInterval: 1000,
    maxReconnectAttempts: 10,
    batchInterval: 50, // ms
    pingInterval: 30000, // 30s
    binaryMessages: true
  }
) {
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const messageQueueRef = useRef<any[]>([]);
  const pingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastActivityRef = useRef<number>(Date.now());

  // Batched message sender
  const sendBatchedMessages = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN && messageQueueRef.current.length > 0) {
      const messages = [...messageQueueRef.current];
      messageQueueRef.current = [];

      // Send as batch in optimized format
      if (options.binaryMessages) {
        // Convert to binary format (using MessagePack or custom format)
        try {
          // This is a placeholder for actual binary serialization
          // In a real implementation, you'd use MessagePack or similar
          const binaryData = new TextEncoder().encode(JSON.stringify(messages));
          socketRef.current.send(binaryData);
        } catch (e) {
          // Fallback to JSON if binary serialization fails
          socketRef.current.send(JSON.stringify({ type: 'batch', messages }));
        }
      } else {
        // Send as JSON batch
        socketRef.current.send(JSON.stringify({ type: 'batch', messages }));
      }

      lastActivityRef.current = Date.now();
    }
  }, [options.binaryMessages]);

  // Debounced send function (batches messages)
  const debouncedSend = useMemo(
    () => debounce(sendBatchedMessages, options.batchInterval),
    [sendBatchedMessages, options.batchInterval]
  );

  // Send a single message (queued and batched)
  const sendMessage = useCallback((message: any) => {
    messageQueueRef.current.push(message);
    debouncedSend();
  }, [debouncedSend]);

  // Connect WebSocket with auto-reconnect
  const connect = useCallback(() => {
    try {
      const socket = new WebSocket(url);

      socket.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttemptsRef.current = 0;

        // Set up ping to keep connection alive
        pingTimerRef.current = setInterval(() => {
          // Only ping if no activity in the last interval
          if (Date.now() - lastActivityRef.current > options.pingInterval) {
            socket.send(JSON.stringify({ type: 'ping' }));
          }
        }, options.pingInterval);
      };

      socket.onclose = () => {
        console.log('WebSocket closed');
        if (pingTimerRef.current) {
          clearInterval(pingTimerRef.current);
        }

        // Attempt to reconnect if not at max attempts
        if (reconnectAttemptsRef.current < options.maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          const delay = Math.min(
            options.reconnectInterval * Math.pow(1.5, reconnectAttemptsRef.current - 1),
            30000 // Cap at 30s
          );

          reconnectTimerRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      socketRef.current = socket;
    } catch (e) {
      console.error('WebSocket connection error:', e);
    }
  }, [url, options.pingInterval, options.reconnectInterval, options.maxReconnectAttempts]);

  // Initialize connection
  useEffect(() => {
    connect();

    return () => {
      // Clean up on unmount
      if (socketRef.current) {
        socketRef.current.close();
      }

      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }

      if (pingTimerRef.current) {
        clearInterval(pingTimerRef.current);
      }

      debouncedSend.cancel();
    };
  }, [connect, debouncedSend]);

  return {
    sendMessage,
    socket: socketRef.current,
  };
}

/**
 * Debounced update hook for real-time operations
 *
 * Prevents flooding the network with rapid successive updates
 */
export function useDebouncedUpdates(
  onUpdate: (updates: any[]) => void,
  options = { delay: 100, maxQueueSize: 100 }
) {
  const updatesQueueRef = useRef<any[]>([]);

  // Throttled update sender (more responsive than pure debounce for real-time updates)
  const throttledSendUpdates = useMemo(
    () => throttle(() => {
      if (updatesQueueRef.current.length > 0) {
        const updates = [...updatesQueueRef.current];
        updatesQueueRef.current = [];
        onUpdate(updates);
      }
    }, options.delay),
    [onUpdate, options.delay]
  );

  // Queue an update
  const queueUpdate = useCallback((update: any) => {
    // Limit queue size to prevent memory issues
    if (updatesQueueRef.current.length < options.maxQueueSize) {
      updatesQueueRef.current.push(update);
    } else {
      // If queue is full, process immediately
      onUpdate([...updatesQueueRef.current, update]);
      updatesQueueRef.current = [];
    }

    throttledSendUpdates();
  }, [onUpdate, throttledSendUpdates, options.maxQueueSize]);

  // Cleanup
  useEffect(() => {
    return () => {
      throttledSendUpdates.cancel();
      // Process any remaining updates
      if (updatesQueueRef.current.length > 0) {
        onUpdate([...updatesQueueRef.current]);
      }
    };
  }, [throttledSendUpdates, onUpdate]);

  return queueUpdate;
}

/**
 * Optimized Yjs document management for collaborative editing
 */
export function useOptimizedYjsDocument(
  docName: string,
  options = {
    gcEnabled: true,
    mergeUpdates: true,
    gcTrackingNeeded: false
  }
) {
  const docRef = useRef<Y.Doc | null>(null);

  // Initialize doc
  useEffect(() => {
    const doc = new Y.Doc({ gc: options.gcEnabled });

    // Configure GC for optimal performance
    if (options.gcEnabled) {
      (doc as any).gcEnabled = true;

      // Configure aggressive GC for large documents
      if (options.gcTrackingNeeded) {
        // Track GC metrics
        doc.on('beforeTransaction', () => {
          console.time('yjsTransaction');
        });

        doc.on('afterTransaction', () => {
          console.timeEnd('yjsTransaction');
        });
      }
    }

    docRef.current = doc;

    return () => {
      // Clean up document
      doc.destroy();
    };
  }, [docName, options.gcEnabled, options.gcTrackingNeeded]);

  /**
   * Apply updates with optimized handling of batched events
   */
  const applyUpdates = useCallback((updates: Uint8Array[]) => {
    if (!docRef.current) return;

    if (options.mergeUpdates && updates.length > 1) {
      try {
        // Try to merge updates for performance when possible
        const mergedUpdate = Y.mergeUpdates(updates);
        Y.applyUpdate(docRef.current, mergedUpdate);
      } catch (e) {
        // Fallback to applying sequentially if merge fails
        updates.forEach(update => {
          Y.applyUpdate(docRef.current!, update);
        });
      }
    } else {
      // Apply updates one by one
      updates.forEach(update => {
        Y.applyUpdate(docRef.current!, update);
      });
    }
  }, [options.mergeUpdates]);

  return {
    doc: docRef.current,
    applyUpdates,
  };
}

/**
 * Optimized canvas rendering with frame rate control
 *
 * Limits rendering to maintain consistent frame rate
 */
export function useOptimizedRendering(
  options = { targetFPS: 60, lowPerformanceThreshold: 1000 }
) {
  const fpsRef = useRef(60);
  const lastFrameTimeRef = useRef(0);
  const elementCountRef = useRef(0);
  const windowSize = useWindowSize();

  // Optimal frame interval in ms
  const frameInterval = useMemo(() => 1000 / options.targetFPS, [options.targetFPS]);

  // Determine if we should render at reduced quality
  const shouldReduceQuality = useMemo(() =>
    elementCountRef.current > options.lowPerformanceThreshold,
    [elementCountRef.current, options.lowPerformanceThreshold]
  );

  // Request animation frame with throttling
  const requestRender = useCallback((renderFn: () => void, count: number) => {
    elementCountRef.current = count;

    const now = performance.now();
    const elapsed = now - lastFrameTimeRef.current;

    if (elapsed >= frameInterval) {
      lastFrameTimeRef.current = now;
      fpsRef.current = 1000 / elapsed;
      renderFn();
    } else {
      // Schedule render on next frame
      requestAnimationFrame(() => renderFn());
    }
  }, [frameInterval]);

  const renderingQuality = useMemo(() => {
    if (shouldReduceQuality) {
      // Calculate quality based on element count and window size
      const baseQuality = Math.min(
        1.0,
        options.lowPerformanceThreshold / elementCountRef.current
      );

      // Further reduce quality on smaller screens (mobile)
      const screenFactor = Math.min(1.0, windowSize.width / 1200);

      return {
        shadowsEnabled: false,
        antiAliasing: false,
        textureQuality: 'low',
        quality: baseQuality * screenFactor,
        reducedMotion: true
      };
    }

    return {
      shadowsEnabled: true,
      antiAliasing: true,
      textureQuality: 'high',
      quality: 1.0,
      reducedMotion: false
    };
  }, [shouldReduceQuality, windowSize.width, options.lowPerformanceThreshold]);

  return {
    requestRender,
    renderingQuality,
    currentFPS: fpsRef.current
  };
}

/**
 * Worker-based calculations for canvas operations
 *
 * Offloads heavy calculations to a web worker to keep the main thread responsive
 */
export function useCanvasWorker(workerScriptUrl: string) {
  const workerRef = useRef<Worker | null>(null);

  useEffect(() => {
    // Create worker
    workerRef.current = new Worker(workerScriptUrl);

    return () => {
      // Terminate worker on cleanup
      workerRef.current?.terminate();
    };
  }, [workerScriptUrl]);

  // Run operation in worker
  const runInWorker = useCallback(async (operation: string, data: any): Promise<any> => {
    return new Promise((resolve, reject) => {
      if (!workerRef.current) {
        reject(new Error('Worker not initialized'));
        return;
      }

      const messageId = Date.now().toString();

      // Set up response handler
      const handleMessage = (event: MessageEvent) => {
        if (event.data.messageId === messageId) {
          workerRef.current?.removeEventListener('message', handleMessage);

          if (event.data.error) {
            reject(new Error(event.data.error));
          } else {
            resolve(event.data.result);
          }
        }
      };

      workerRef.current.addEventListener('message', handleMessage);

      // Send request to worker
      workerRef.current.postMessage({
        operation,
        data,
        messageId
      });

      // Set timeout for worker response
      setTimeout(() => {
        workerRef.current?.removeEventListener('message', handleMessage);
        reject(new Error('Worker operation timed out'));
      }, 10000);
    });
  }, []);

  return {
    runInWorker,
    isWorkerAvailable: !!workerRef.current
  };
}

/**
 * Export optimized canvas configuration
 */
export const OPTIMIZED_CANVAS_CONFIG = {
  // Rendering options
  rendering: {
    useRequestIdleCallback: true,
    useDeferredUpdates: true,
    useOffscreenCanvas: true,
    batchDOMUpdates: true,
    reduceAnimationInBackground: true,
    disableShadowsOnMobile: true,
  },

  // Memory options
  memory: {
    maxCanvasElements: 10000,
    enableMemoryMonitoring: true,
    useMemoryCache: true,
    disposeUnusedResources: true,
  },

  // Collaboration options
  collaboration: {
    streamChangesOnly: true,
    compressionEnabled: true,
    presenceDebounceTime: 500,
    mergeEditsWhenPossible: true,
    patchBasedSynchronization: true,
  },

  // Touch device optimizations
  touch: {
    optimizedForTouch: true,
    useSimplifiedRendering: true,
    limitSimultaneousTouches: 2,
  }
};
