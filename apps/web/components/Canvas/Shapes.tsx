'use client';

import React, { useMemo } from 'react';
import { Group, Rect, Circle, Text, Line } from 'react-konva';
import { canvasPerformance } from '@/utils/canvasPerformance';

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

interface VisibleRect {
  x: number;
  y: number;
  width: number;
  height: number;
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
  // Filter shapes to only those visible in the viewport
  const visibleShapes = useMemo(() => {
    const startTime = performance.now();

    const filtered = shapes.filter(shape => {
      // Calculate shape bounds
      let bounds: VisibleRect;

      switch (shape.type) {
        case 'rect':
          bounds = {
            x: shape.x,
            y: shape.y,
            width: shape.width || 0,
            height: shape.height || 0,
          };
          break;

        case 'circle':
          const radius = shape.radius || 0;
          bounds = {
            x: shape.x - radius,
            y: shape.y - radius,
            width: radius * 2,
            height: radius * 2,
          };
          break;

        case 'text':
          // Text bounds are approximate
          bounds = {
            x: shape.x,
            y: shape.y,
            width: (shape.text?.length || 0) * (shape.fontSize || 12) * 0.6,
            height: (shape.fontSize || 12) * 1.2,
          };
          break;

        case 'line':
        case 'freehand':
          if (!shape.points || shape.points.length < 2) {
            return false;
          }

          // Calculate bounding box of points
          let minX = Infinity;
          let minY = Infinity;
          let maxX = -Infinity;
          let maxY = -Infinity;

          for (let i = 0; i < shape.points.length; i += 2) {
            const x = shape.points[i];
            const y = shape.points[i + 1];

            minX = Math.min(minX, x);
            minY = Math.min(minY, y);
            maxX = Math.max(maxX, x);
            maxY = Math.max(maxY, y);
          }

          bounds = {
            x: minX,
            y: minY,
            width: maxX - minX,
            height: maxY - minY,
          };
          break;

        default:
          return false;
      }

      // Check if shape bounds intersect with visible rect
      return (
        bounds.x + bounds.width >= visibleRect.x &&
        bounds.x <= visibleRect.x + visibleRect.width &&
        bounds.y + bounds.height >= visibleRect.y &&
        bounds.y <= visibleRect.y + visibleRect.height
      );
    });

    // Measure performance
    const endTime = performance.now();
    canvasPerformance.measure('render.filterShapes', () => {}, {
      totalShapes: shapes.length,
      visibleShapes: filtered.length,
      duration: endTime - startTime,
    });

    return filtered;
  }, [shapes, visibleRect]);

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
          />
        );

      case 'circle':
        return (
          <Circle
            {...commonProps}
            radius={shape.radius}
          />
        );

      case 'text':
        return (
          <Text
            {...commonProps}
            text={shape.text}
            fontSize={shape.fontSize}
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
