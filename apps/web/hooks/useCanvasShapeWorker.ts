'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Shape } from '@/components/Canvas/Shapes';
import { VisibleRect } from '@/utils/canvasUtils';
import { canvasPerformance } from '@/utils/canvasPerformance';

// Type definitions
type WorkerResponseType = 
  | 'selection' 
  | 'collision' 
  | 'buildSpatialIndex'
  | 'filterShapes';

interface WorkerResponse {
  type: WorkerResponseType;
  result: any;
  duration: number;
  success: boolean;
  error?: string;
}

/**
 * Custom hook for using the canvas shapes WebWorker
 * Handles offloading heavy calculations to a worker thread
 */
export function useCanvasShapeWorker() {
  const [isReady, setIsReady] = useState(false);
  const workerRef = useRef<Worker | null>(null);
  const callbacksRef = useRef<Map<string, (data: any) => void>>(new Map());
  
  // Initialize worker
  useEffect(() => {
    // We need to use a dynamic import with Next.js
    if (typeof window !== 'undefined') {
      try {
        workerRef.current = new Worker(new URL('../workers/canvas-shapes.worker.ts', import.meta.url));
        
        // Set up message handler
        workerRef.current.onmessage = (event: MessageEvent<WorkerResponse>) => {
          const { type, result, success, error, duration } = event.data;
          
          // Record performance metrics
          canvasPerformance.measure(`worker.${type}`, () => {}, {
            duration,
            success,
            resultSize: Array.isArray(result) ? result.length : 0,
          });
          
          // Get and execute callback for this request type
          const callback = callbacksRef.current.get(type);
          if (callback) {
            if (success) {
              callback(result);
            } else {
              console.error(`Worker error (${type}):`, error);
              callback(null);
            }
          }
        };
        
        setIsReady(true);
      } catch (error) {
        console.error('Failed to initialize canvas worker:', error);
      }
    }
    
    // Clean up worker on unmount
    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
      }
    };
  }, []);
  
  /**
   * Find shapes that intersect with a selection rectangle
   */
  const findShapesInSelection = useCallback((
    shapes: Shape[],
    selectionRect: VisibleRect,
    callback: (selectedShapes: Shape[]) => void
  ) => {
    if (!isReady || !workerRef.current) {
      // Fallback to main thread if worker is not ready
      const startTime = performance.now();
      
      const selectedShapes = shapes.filter(shape => {
        // Simple bounding box check for fallback
        return (
          shape.x <= selectionRect.x + selectionRect.width &&
          shape.x + (shape.width || 0) >= selectionRect.x &&
          shape.y <= selectionRect.y + selectionRect.height &&
          shape.y + (shape.height || 0) >= selectionRect.y
        );
      });
      
      const duration = performance.now() - startTime;
      canvasPerformance.measure('mainThread.selection', () => {}, {
        duration,
        count: selectedShapes.length,
      });
      
      callback(selectedShapes);
      return;
    }
    
    // Store callback
    callbacksRef.current.set('selection', callback);
    
    // Send message to worker
    workerRef.current.postMessage({
      type: 'selection',
      shapes,
      selectionRect,
    });
  }, [isReady]);
  
  /**
   * Find shapes at a specific point (for collision detection)
   */
  const findShapesAtPoint = useCallback((
    shapes: Shape[],
    point: { x: number, y: number },
    callback: (collidingShapes: Shape[]) => void
  ) => {
    if (!isReady || !workerRef.current) {
      // Fallback is complex for point collision, so just return a simplified version
      const startTime = performance.now();
      
      const collidingShapes = shapes.filter(shape => {
        if (shape.type === 'circle' && shape.radius) {
          const dx = point.x - shape.x;
          const dy = point.y - shape.y;
          return Math.sqrt(dx*dx + dy*dy) <= shape.radius;
        }
        
        // Simple bounding box for other shapes
        const width = shape.width || 0;
        const height = shape.height || 0;
        return (
          point.x >= shape.x && 
          point.x <= shape.x + width && 
          point.y >= shape.y && 
          point.y <= shape.y + height
        );
      });
      
      const duration = performance.now() - startTime;
      canvasPerformance.measure('mainThread.collision', () => {}, {
        duration,
        count: collidingShapes.length,
      });
      
      callback(collidingShapes);
      return;
    }
    
    // Store callback
    callbacksRef.current.set('collision', callback);
    
    // Send message to worker
    workerRef.current.postMessage({
      type: 'collision',
      shapes,
      point,
    });
  }, [isReady]);
  
  /**
   * Filter shapes to only those visible in the viewport
   */
  const filterVisibleShapes = useCallback((
    shapes: Shape[],
    visibleRect: VisibleRect,
    callback: (visibleShapes: Shape[]) => void
  ) => {
    if (!isReady || !workerRef.current) {
      // Simple fallback - just return all shapes
      callback(shapes);
      return;
    }
    
    // Store callback
    callbacksRef.current.set('filterShapes', callback);
    
    // Send message to worker
    workerRef.current.postMessage({
      type: 'filterShapes',
      shapes,
      visibleRect,
    });
  }, [isReady]);
  
  /**
   * Build a spatial index for shapes
   */
  const buildSpatialIndex = useCallback((
    shapes: Shape[],
    gridSize: number = 1000,
    callback: (index: Record<string, Shape[]>) => void
  ) => {
    if (!isReady || !workerRef.current) {
      // No fallback for spatial index
      callback({});
      return;
    }
    
    // Store callback
    callbacksRef.current.set('buildSpatialIndex', callback);
    
    // Send message to worker
    workerRef.current.postMessage({
      type: 'buildSpatialIndex',
      shapes,
      gridSize,
    });
  }, [isReady]);
  
  return {
    isReady,
    findShapesInSelection,
    findShapesAtPoint,
    filterVisibleShapes,
    buildSpatialIndex,
  };
}