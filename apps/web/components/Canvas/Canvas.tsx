'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Stage, Layer, Group } from 'react-konva';
import Konva from 'konva';
import { canvasPerformance } from '@/utils/canvasPerformance';
import { canvasBatch } from '@/utils/canvasBatch';

// Types
interface CanvasProps {
  width: number;
  height: number;
  children: React.ReactNode;
  padding?: number;
  onViewportChange?: (viewport: ViewportData) => void;
}

interface ViewportData {
  x: number;
  y: number;
  scale: number;
  width: number;
  height: number;
  visibleRect: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  pointerPosition?: {
    x: number;
    y: number;
  };
}

/**
 * Canvas component
 *
 * This component implements virtualization for large canvas documents,
 * only rendering elements that are visible in the current viewport.
 */
export const Canvas: React.FC<CanvasProps> = ({
  width,
  height,
  children,
  padding = 100,
  onViewportChange,
}) => {
  // Refs
  const stageRef = useRef<Konva.Stage>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // State
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [dimensions, setDimensions] = useState({ width, height });
  const [visibleRect, setVisibleRect] = useState({ x: 0, y: 0, width: 0, height: 0 });

  // Calculate visible area based on current viewport
  const calculateVisibleRect = useCallback(() => {
    if (!stageRef.current) return;

    const stage = stageRef.current;
    const pos = stage.position();
    const stageScale = stage.scaleX();

    // Calculate visible rectangle in world coordinates
    const visibleRect = {
      x: -pos.x / stageScale,
      y: -pos.y / stageScale,
      width: dimensions.width / stageScale,
      height: dimensions.height / stageScale,
    };

    // Add padding to visible rect to prevent popping at edges
    const paddedRect = {
      x: visibleRect.x - padding / stageScale,
      y: visibleRect.y - padding / stageScale,
      width: visibleRect.width + (2 * padding) / stageScale,
      height: visibleRect.height + (2 * padding) / stageScale,
    };

    // Batch the update to avoid multiple renders
    canvasBatch.queueUpdate('visibleRect', () => {
      setVisibleRect(paddedRect);

      // Notify parent of viewport change
      if (onViewportChange) {
        onViewportChange({
          x: pos.x,
          y: pos.y,
          scale: stageScale,
          width: dimensions.width,
          height: dimensions.height,
          visibleRect: paddedRect,
          pointerPosition: stage.getPointerPosition() || undefined,
        });
      }
    });
  }, [dimensions, padding, onViewportChange]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const newWidth = containerRef.current.offsetWidth;
        const newHeight = containerRef.current.offsetHeight;

        setDimensions({
          width: newWidth,
          height: newHeight,
        });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  // Update visible rect when scale or position changes
  useEffect(() => {
    calculateVisibleRect();
  }, [scale, position, dimensions, calculateVisibleRect]);

  // Handle wheel event for zooming
  const handleWheel = useCallback((e: Konva.KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();

    const startTime = performance.now();

    const stage = stageRef.current;
    if (!stage) return;

    const oldScale = stage.scaleX();

    // Calculate new scale
    const pointer = stage.getPointerPosition();
    if (!pointer) return;

    const mousePointTo = {
      x: (pointer.x - stage.x()) / oldScale,
      y: (pointer.y - stage.y()) / oldScale,
    };

    // Determine zoom direction and calculate new scale
    const zoomDirection = e.evt.deltaY < 0 ? 1 : -1;
    const SCALE_FACTOR = 1.1;
    const newScale = zoomDirection > 0
      ? oldScale * SCALE_FACTOR
      : oldScale / SCALE_FACTOR;

    // Limit scale to reasonable bounds
    const MAX_SCALE = 5;
    const MIN_SCALE = 0.1;
    const limitedScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, newScale));

    // Calculate new position
    const newPos = {
      x: pointer.x - mousePointTo.x * limitedScale,
      y: pointer.y - mousePointTo.y * limitedScale,
    };

    // Batch the scale and position updates
    canvasBatch.queueUpdate('zoom', () => {
      // Apply new scale and position
      stage.scale({ x: limitedScale, y: limitedScale });
      stage.position(newPos);
      
      // Update state
      setScale(limitedScale);
      setPosition(newPos);
    });

    // Measure performance
    const endTime = performance.now();
    canvasPerformance.measure('interaction.zoom', () => {}, {
      oldScale,
      newScale: limitedScale,
      duration: endTime - startTime,
    });
  }, []);

  // Handle drag events
  const handleDragStart = useCallback(() => {
    canvasPerformance.startMetric('interaction.drag');
  }, []);

  const handleDragEnd = useCallback((e: Konva.KonvaEventObject<DragEvent>) => {
    const stage = stageRef.current;
    if (!stage) return;

    // Batch position update
    canvasBatch.queueUpdate('drag', () => {
      setPosition(stage.position());
    });

    canvasPerformance.endMetric('interaction.drag');
  }, []);

  // Render function with virtualization
  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      <Stage
        ref={stageRef}
        width={dimensions.width}
        height={dimensions.height}
        onWheel={handleWheel}
        draggable
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <Layer>
          <Group>
            {/* Pass visible rect to children for virtualization */}
            {React.Children.map(children, child => {
              if (React.isValidElement(child)) {
                return React.cloneElement(child as React.ReactElement<any>, {
                  visibleRect,
                  scale,
                });
              }
              return child;
            })}
          </Group>
        </Layer>
      </Stage>
    </div>
  );
};
