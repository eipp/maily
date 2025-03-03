// Types - duplicated here because workers can't import from main thread
interface Shape {
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

interface ShapeSelectionMessage {
  type: 'selection';
  shapes: Shape[];
  selectionRect: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

interface CollisionDetectionMessage {
  type: 'collision';
  shapes: Shape[];
  point: { x: number; y: number };
}

interface SpatialIndexMessage {
  type: 'buildSpatialIndex';
  shapes: Shape[];
  gridSize: number;
}

interface FilterShapesMessage {
  type: 'filterShapes';
  shapes: Shape[];
  visibleRect: VisibleRect;
}

type WorkerMessage = 
  | ShapeSelectionMessage 
  | CollisionDetectionMessage 
  | SpatialIndexMessage
  | FilterShapesMessage;

/**
 * Get the bounds of a shape
 */
function getShapeBounds(shape: Shape): VisibleRect {
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
 * Check if a point is inside a shape
 */
function isPointInShape(shape: Shape, point: { x: number; y: number }): boolean {
  const bounds = getShapeBounds(shape);
  
  switch (shape.type) {
    case 'rect':
      return (
        point.x >= bounds.x &&
        point.x <= bounds.x + bounds.width &&
        point.y >= bounds.y &&
        point.y <= bounds.y + bounds.height
      );
      
    case 'circle': {
      const dx = point.x - shape.x;
      const dy = point.y - shape.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      return distance <= (shape.radius || 0);
    }
    
    case 'text': {
      // Simplified text collision (rect-based)
      return (
        point.x >= bounds.x &&
        point.x <= bounds.x + bounds.width &&
        point.y >= bounds.y &&
        point.y <= bounds.y + bounds.height
      );
    }
    
    case 'line':
    case 'freehand': {
      if (!shape.points || shape.points.length < 4) {
        return false;
      }
      
      // For freehand/line, check distance to segments
      const strokeWidth = shape.strokeWidth || 1;
      const threshold = Math.max(strokeWidth * 2, 10); // Make touch area larger for finger input
      
      for (let i = 0; i < shape.points.length - 2; i += 2) {
        const x1 = shape.points[i];
        const y1 = shape.points[i + 1];
        const x2 = shape.points[i + 2];
        const y2 = shape.points[i + 3];
        
        // Calculate distance from point to line segment
        const length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
        if (length === 0) continue;
        
        const dot = ((point.x - x1) * (x2 - x1) + (point.y - y1) * (y2 - y1)) / (length * length);
        
        if (dot < 0 || dot > 1) {
          // Point is not on the line segment, check distance to endpoints
          const d1 = Math.sqrt((point.x - x1) ** 2 + (point.y - y1) ** 2);
          const d2 = Math.sqrt((point.x - x2) ** 2 + (point.y - y2) ** 2);
          if (Math.min(d1, d2) <= threshold) {
            return true;
          }
        } else {
          // Point is on the line segment, calculate perpendicular distance
          const closestX = x1 + dot * (x2 - x1);
          const closestY = y1 + dot * (y2 - y1);
          const distance = Math.sqrt((point.x - closestX) ** 2 + (point.y - closestY) ** 2);
          
          if (distance <= threshold) {
            return true;
          }
        }
      }
      
      return false;
    }
    
    default:
      return false;
  }
}

/**
 * Check if two rectangles intersect
 */
function doRectsIntersect(r1: VisibleRect, r2: VisibleRect): boolean {
  return (
    r1.x + r1.width >= r2.x &&
    r1.x <= r2.x + r2.width &&
    r1.y + r1.height >= r2.y &&
    r1.y <= r2.y + r2.height
  );
}

/**
 * Determine if a shape is visible in the visible rect
 */
function isShapeVisible(shape: Shape, visibleRect: VisibleRect): boolean {
  const bounds = getShapeBounds(shape);
  return doRectsIntersect(bounds, visibleRect);
}

/**
 * Calculate sector for a shape
 */
function getShapeSector(shape: Shape, gridSize: number): string {
  const bounds = getShapeBounds(shape);
  const centerX = bounds.x + bounds.width / 2;
  const centerY = bounds.y + bounds.height / 2;
  
  const sectorX = Math.floor(centerX / gridSize);
  const sectorY = Math.floor(centerY / gridSize);
  
  return `${sectorX},${sectorY}`;
}

/**
 * Build spatial index for shapes
 */
function buildSpatialIndex(shapes: Shape[], gridSize: number = 1000): Record<string, Shape[]> {
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
 * Filter shapes to those visible in the viewport
 */
function getVisibleShapes(shapes: Shape[], visibleRect: VisibleRect, gridSize: number = 1000): Shape[] {
  // For small number of shapes, simple filtering is more efficient
  if (shapes.length < 100) {
    return shapes.filter(shape => isShapeVisible(shape, visibleRect));
  }
  
  // For larger canvases, use spatial indexing
  const startX = Math.floor(visibleRect.x / gridSize);
  const startY = Math.floor(visibleRect.y / gridSize);
  const endX = Math.floor((visibleRect.x + visibleRect.width) / gridSize);
  const endY = Math.floor((visibleRect.y + visibleRect.height) / gridSize);
  
  // Build spatial index
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

/**
 * Find shapes that intersect with the selection rectangle
 */
function findShapesInSelection(shapes: Shape[], selectionRect: VisibleRect): Shape[] {
  return shapes.filter(shape => {
    const bounds = getShapeBounds(shape);
    return doRectsIntersect(bounds, selectionRect);
  });
}

/**
 * Find shapes that contain the point
 */
function findShapesAtPoint(shapes: Shape[], point: { x: number; y: number }): Shape[] {
  return shapes.filter(shape => isPointInShape(shape, point));
}

// Web Worker event listener
self.onmessage = (event: MessageEvent<WorkerMessage>) => {
  const { type } = event.data;
  
  try {
    const startTime = performance.now();
    let result;
    
    switch (type) {
      case 'selection': {
        const { shapes, selectionRect } = event.data;
        result = findShapesInSelection(shapes, selectionRect);
        break;
      }
      
      case 'collision': {
        const { shapes, point } = event.data;
        result = findShapesAtPoint(shapes, point);
        break;
      }
      
      case 'buildSpatialIndex': {
        const { shapes, gridSize } = event.data;
        result = buildSpatialIndex(shapes, gridSize);
        break;
      }
      
      case 'filterShapes': {
        const { shapes, visibleRect } = event.data;
        result = getVisibleShapes(shapes, visibleRect);
        break;
      }
      
      default:
        throw new Error(`Unknown worker message type: ${type}`);
    }
    
    const duration = performance.now() - startTime;
    
    // Post result back to main thread
    self.postMessage({
      type,
      result,
      duration,
      success: true,
    });
  } catch (error) {
    self.postMessage({
      type,
      error: error instanceof Error ? error.message : String(error),
      success: false,
    });
  }
};

// Export empty type for TypeScript
export {};