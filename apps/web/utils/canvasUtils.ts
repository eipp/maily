import { Shape } from '@/components/Canvas/Shapes';

export interface VisibleRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * Determines if a shape is visible within the given viewport rectangle
 */
export function isShapeVisible(shape: Shape, visibleRect: VisibleRect): boolean {
  // Calculate shape bounds
  const bounds = getShapeBounds(shape);
  
  // Check if shape bounds intersect with visible rect
  return (
    bounds.x + bounds.width >= visibleRect.x &&
    bounds.x <= visibleRect.x + visibleRect.width &&
    bounds.y + bounds.height >= visibleRect.y &&
    bounds.y <= visibleRect.y + visibleRect.height
  );
}

/**
 * Calculates the bounding box for a shape
 */
export function getShapeBounds(shape: Shape): VisibleRect {
  switch (shape.type) {
    case 'rect':
      return {
        x: shape.x,
        y: shape.y,
        width: shape.width || 0,
        height: shape.height || 0,
      };

    case 'circle': {
      const radius = shape.radius || 0;
      return {
        x: shape.x - radius,
        y: shape.y - radius,
        width: radius * 2,
        height: radius * 2,
      };
    }

    case 'text': {
      // Text bounds are approximate
      const fontSize = shape.fontSize || 12;
      const textWidth = (shape.text?.length || 0) * fontSize * 0.6;
      return {
        x: shape.x,
        y: shape.y,
        width: textWidth,
        height: fontSize * 1.2,
      };
    }

    case 'line':
    case 'freehand': {
      if (!shape.points || shape.points.length < 2) {
        return { x: 0, y: 0, width: 0, height: 0 };
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

      // Add a small buffer for line width
      const buffer = (shape.strokeWidth || 1) * 2;
      
      return {
        x: minX - buffer,
        y: minY - buffer,
        width: (maxX - minX) + (buffer * 2),
        height: (maxY - minY) + (buffer * 2),
      };
    }

    default:
      return { x: 0, y: 0, width: 0, height: 0 };
  }
}

/**
 * Calculates the quadtree sector for a shape (for spatial indexing)
 */
export function getShapeSector(shape: Shape, gridSize: number): string {
  const bounds = getShapeBounds(shape);
  const centerX = bounds.x + bounds.width / 2;
  const centerY = bounds.y + bounds.height / 2;
  
  const sectorX = Math.floor(centerX / gridSize);
  const sectorY = Math.floor(centerY / gridSize);
  
  return `${sectorX},${sectorY}`;
}

/**
 * Partitions shapes into spatial buckets for faster rendering and collision detection
 */
export function buildSpatialIndex(shapes: Shape[], gridSize: number = 1000): Record<string, Shape[]> {
  const index: Record<string, Shape[]> = {};
  
  for (const shape of shapes) {
    const sector = getShapeSector(shape, gridSize);
    
    if (!index[sector]) {
      index[sector] = [];
    }
    
    index[sector].push(shape);
  }
  
  return index;
}

/**
 * Gets visible shapes efficiently using spatial indexing
 */
export function getVisibleShapes(
  shapes: Shape[], 
  visibleRect: VisibleRect, 
  gridSize: number = 1000
): Shape[] {
  // For small number of shapes, simple filtering is more efficient
  if (shapes.length < 100) {
    return shapes.filter(shape => isShapeVisible(shape, visibleRect));
  }
  
  // For larger canvases, use spatial indexing
  const startX = Math.floor(visibleRect.x / gridSize);
  const startY = Math.floor(visibleRect.y / gridSize);
  const endX = Math.floor((visibleRect.x + visibleRect.width) / gridSize);
  const endY = Math.floor((visibleRect.y + visibleRect.height) / gridSize);
  
  // Build spatial index if needed
  const index = buildSpatialIndex(shapes, gridSize);
  const candidateShapes: Shape[] = [];
  
  // Collect shapes from visible sectors
  for (let x = startX; x <= endX; x++) {
    for (let y = startY; y <= endY; y++) {
      const sector = `${x},${y}`;
      if (index[sector]) {
        candidateShapes.push(...index[sector]);
      }
    }
  }
  
  // Final precise check (removes duplicates too)
  const visibleShapeIds = new Set<string>();
  const visibleShapes: Shape[] = [];
  
  for (const shape of candidateShapes) {
    if (!visibleShapeIds.has(shape.id) && isShapeVisible(shape, visibleRect)) {
      visibleShapeIds.add(shape.id);
      visibleShapes.push(shape);
    }
  }
  
  return visibleShapes;
}