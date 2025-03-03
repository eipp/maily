'use client';

import React, { useState, useEffect } from 'react';
import { Group, Rect, Circle, Text, Line } from 'react-konva';
import { canvasPerformance } from '@/utils/canvasPerformance';
import { VisibleRect } from '@/utils/canvasUtils';
import { useCanvasShapeWorker } from '@/hooks/useCanvasShapeWorker';

// Types
export interface Shape {
  id: string;
  type: 'rect' | 'circle' | 'text' | 'line' | 'freehand';
  x: number;
  y: number;
  width?: number;
  height?: number;
  radius?: number;
  points?: number[];
  text?: string;
  fontSize?: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  rotation?: number;
  opacity?: number;
  draggable?: boolean;
  isSelected?: boolean;
}

interface ShapesProps {
  shapes: Shape[];
  visibleRect: VisibleRect;
  scale: number;
  onShapeClick?: (id: string) => void;
  onShapeDragStart?: (id: string) => void;
  onShapeDragEnd?: (id: string, x: number, y: number) => void;
}

/**
 * Shapes component
 *
 * This component renders only the shapes that are visible in the current viewport,
 * improving performance for large canvas documents.
 */
export const Shapes: React.FC<ShapesProps> = ({
  shapes,
  visibleRect,
  scale,
  onShapeClick,
  onShapeDragStart,
  onShapeDragEnd,
}) => {
  // Use WebWorker for filtering shapes if available
  const [visibleShapes, setVisibleShapes] = useState<Shape[]>([]);
  const { filterVisibleShapes } = useCanvasShapeWorker();

  // Update visibleShapes when input shapes or viewportRect changes
  useEffect(() => {
    const startTime = performance.now();
    
    // Use worker to filter shapes
    filterVisibleShapes(shapes, visibleRect, (filteredShapes) => {
      setVisibleShapes(filteredShapes || shapes);
      
      // Measure performance
      const endTime = performance.now();
      canvasPerformance.measure('render.filterShapes', () => {}, {
        totalShapes: shapes.length,
        visibleShapes: filteredShapes ? filteredShapes.length : shapes.length,
        duration: endTime - startTime,
      });
    });
  }, [shapes, visibleRect, filterVisibleShapes]);

  // Render shapes based on their type
  const renderShape = (shape: Shape) => {
    const commonProps = {
      key: shape.id,
      id: shape.id,
      x: shape.x,
      y: shape.y,
      fill: shape.fill,
      stroke: shape.stroke,
      strokeWidth: shape.strokeWidth,
      rotation: shape.rotation,
      opacity: shape.opacity,
      draggable: shape.draggable,
      onClick: () => onShapeClick?.(shape.id),
      onDragStart: () => onShapeDragStart?.(shape.id),
      onDragEnd: (e: any) => {
        if (onShapeDragEnd) {
          onShapeDragEnd(shape.id, e.target.x(), e.target.y());
        }
      },
    };

    switch (shape.type) {
      case 'rect':
        return (
          <Rect
            {...commonProps}
            width={shape.width}
            height={shape.height}
            perfectDrawEnabled={false} // Performance optimization
          />
        );

      case 'circle':
        return (
          <Circle
            {...commonProps}
            radius={shape.radius}
            perfectDrawEnabled={false} // Performance optimization
          />
        );

      case 'text':
        return (
          <Text
            {...commonProps}
            text={shape.text}
            fontSize={shape.fontSize}
            perfectDrawEnabled={false} // Performance optimization
          />
        );

      case 'line':
      case 'freehand':
        return (
          <Line
            {...commonProps}
            points={shape.points}
            tension={shape.type === 'freehand' ? 0.5 : 0}
            lineCap="round"
            lineJoin="round"
            perfectDrawEnabled={false} // Performance optimization
          />
        );

      default:
        return null;
    }
  };

  // Render with performance measurement
  return (
    <Group>
      {visibleShapes.map(shape => renderShape(shape))}
    </Group>
  );
};