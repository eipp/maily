/**
 * Canvas Worker
 *
 * Offloads computationally intensive operations from the main thread
 * to improve UI responsiveness during complex canvas operations.
 */

// Supported operations
const OPERATIONS = {
  CALC_BOUNDS: 'calculateBounds',
  ARRAY_DIFF: 'calculateArrayDiff',
  OPTIMIZE_PATH: 'optimizePath',
  COMPRESS_SHAPES: 'compressShapes',
  GENERATE_THUMBNAIL: 'generateThumbnail',
  SEARCH_DOCUMENT: 'searchDocument',
  BATCH_TRANSFORM: 'batchTransform'
};

// Worker initialization
self.onmessage = function(event) {
  const { operation, data, messageId } = event.data;

  // Validate operation
  if (!Object.values(OPERATIONS).includes(operation)) {
    self.postMessage({
      messageId,
      error: `Unknown operation: ${operation}`
    });
    return;
  }

  try {
    // Process the operation
    const result = processOperation(operation, data);

    // Send result back to main thread
    self.postMessage({
      messageId,
      result
    });
  } catch (error) {
    // Send error back to main thread
    self.postMessage({
      messageId,
      error: error.message || 'Unknown error in worker'
    });
  }
};

/**
 * Process an operation in the worker
 */
function processOperation(operation, data) {
  switch (operation) {
    case OPERATIONS.CALC_BOUNDS:
      return calculateBounds(data.shapes);

    case OPERATIONS.ARRAY_DIFF:
      return calculateArrayDiff(data.oldArray, data.newArray);

    case OPERATIONS.OPTIMIZE_PATH:
      return optimizePath(data.path, data.tolerance);

    case OPERATIONS.COMPRESS_SHAPES:
      return compressShapes(data.shapes);

    case OPERATIONS.GENERATE_THUMBNAIL:
      return generateThumbnail(data.shapes, data.width, data.height);

    case OPERATIONS.SEARCH_DOCUMENT:
      return searchDocument(data.shapes, data.query);

    case OPERATIONS.BATCH_TRANSFORM:
      return batchTransform(data.shapes, data.transformMatrix);

    default:
      throw new Error(`Operation not implemented: ${operation}`);
  }
}

/**
 * Calculate bounds for a collection of shapes
 */
function calculateBounds(shapes) {
  if (!shapes || !shapes.length) {
    return { x: 0, y: 0, width: 0, height: 0 };
  }

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  // Process each shape
  shapes.forEach(shape => {
    const { x, y, width, height } = shape;

    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x + width);
    maxY = Math.max(maxY, y + height);
  });

  return {
    x: minX === Infinity ? 0 : minX,
    y: minY === Infinity ? 0 : minY,
    width: maxX === -Infinity ? 0 : maxX - minX,
    height: maxY === -Infinity ? 0 : maxY - minY
  };
}

/**
 * Calculate difference between two arrays
 */
function calculateArrayDiff(oldArray, newArray) {
  if (!oldArray) oldArray = [];
  if (!newArray) newArray = [];

  const oldSet = new Set(oldArray);
  const newSet = new Set(newArray);

  const added = newArray.filter(item => !oldSet.has(item));
  const removed = oldArray.filter(item => !newSet.has(item));

  return { added, removed };
}

/**
 * Optimize an SVG path or points array
 * by reducing the number of points while preserving shape
 */
function optimizePath(path, tolerance = 1) {
  if (!path || !path.length) {
    return [];
  }

  // If it's an SVG path string, convert to points array
  let points = [];
  if (typeof path === 'string') {
    points = parseSvgPath(path);
  } else {
    points = path;
  }

  // Apply Ramer-Douglas-Peucker algorithm
  const simplified = rdpSimplify(points, tolerance);

  // If original input was a string, convert back to SVG path
  if (typeof path === 'string') {
    return pointsToSvgPath(simplified);
  }

  return simplified;
}

/**
 * Compress shapes data for efficient storage/transmission
 */
function compressShapes(shapes) {
  if (!shapes || !shapes.length) {
    return { compressedData: null, compressionRatio: 0 };
  }

  const originalData = JSON.stringify(shapes);

  // Create a compressed version by removing redundant data
  const compressedShapes = shapes.map(shape => {
    const { id, type, x, y, width, height, rotation } = shape;

    const compressed = { id, type, x, y, width, height };

    // Only include non-zero or non-default properties
    if (rotation) compressed.rotation = rotation;

    // Include only essential style properties
    if (shape.style) {
      compressed.style = {};

      if (shape.style.fill) compressed.style.fill = shape.style.fill;
      if (shape.style.stroke) compressed.style.stroke = shape.style.stroke;
      if (shape.style.strokeWidth) compressed.style.strokeWidth = shape.style.strokeWidth;
    }

    // Include content if present
    if (shape.content) compressed.content = shape.content;

    return compressed;
  });

  const compressedData = JSON.stringify(compressedShapes);
  const compressionRatio = originalData.length / compressedData.length;

  return {
    compressedData,
    compressionRatio,
    originalSize: originalData.length,
    compressedSize: compressedData.length
  };
}

/**
 * Generate a thumbnail for a collection of shapes
 */
function generateThumbnail(shapes, width, height) {
  // This is a placeholder since actual rendering would require a canvas
  // In a real implementation, we would use an OffscreenCanvas
  return {
    message: 'Thumbnail generation requires OffscreenCanvas which is not available in this worker implementation',
    shapesCount: shapes.length,
    requestedSize: { width, height }
  };
}

/**
 * Search for text content within document shapes
 */
function searchDocument(shapes, query) {
  if (!shapes || !shapes.length || !query) {
    return [];
  }

  const queryLower = query.toLowerCase();
  const results = [];

  shapes.forEach(shape => {
    // Check shape content (if it's a text shape)
    if (shape.content && typeof shape.content === 'string' &&
        shape.content.toLowerCase().includes(queryLower)) {
      results.push({
        id: shape.id,
        type: shape.type,
        content: shape.content,
        bounds: {
          x: shape.x,
          y: shape.y,
          width: shape.width,
          height: shape.height
        }
      });
    }

    // Check shape name/label if available
    if (shape.name && typeof shape.name === 'string' &&
        shape.name.toLowerCase().includes(queryLower)) {
      results.push({
        id: shape.id,
        type: shape.type,
        name: shape.name,
        bounds: {
          x: shape.x,
          y: shape.y,
          width: shape.width,
          height: shape.height
        }
      });
    }
  });

  return results;
}

/**
 * Apply transformation matrix to a batch of shapes
 */
function batchTransform(shapes, matrix) {
  if (!shapes || !shapes.length || !matrix) {
    return [];
  }

  return shapes.map(shape => {
    // Clone the shape to avoid modifying the original
    const newShape = { ...shape };

    // Apply transformation
    const transformedPoint = applyTransformationMatrix(
      { x: shape.x, y: shape.y },
      matrix
    );

    newShape.x = transformedPoint.x;
    newShape.y = transformedPoint.y;

    // Handle rotation if present
    if (shape.rotation !== undefined && matrix.rotate !== undefined) {
      newShape.rotation = (shape.rotation + matrix.rotate) % 360;
    }

    // Handle scaling if present
    if (matrix.scaleX !== undefined && matrix.scaleY !== undefined) {
      newShape.width = shape.width * matrix.scaleX;
      newShape.height = shape.height * matrix.scaleY;
    }

    return newShape;
  });
}

// ===== Helper Functions =====

/**
 * Apply a transformation matrix to a point
 */
function applyTransformationMatrix(point, matrix) {
  const { x, y } = point;

  // Basic transformation (more complex transformations would use an actual matrix)
  let newX = x;
  let newY = y;

  // Apply translation
  if (matrix.translateX !== undefined) newX += matrix.translateX;
  if (matrix.translateY !== undefined) newY += matrix.translateY;

  // Apply scaling (from center of shape)
  if (matrix.scaleX !== undefined || matrix.scaleY !== undefined) {
    // This is simplified - real implementation would use actual matrix math
    if (matrix.scaleX !== undefined) newX = newX * matrix.scaleX;
    if (matrix.scaleY !== undefined) newY = newY * matrix.scaleY;
  }

  return { x: newX, y: newY };
}

/**
 * Parse SVG path string into points array
 * This is a simplified version that handles only M and L commands
 */
function parseSvgPath(pathString) {
  const commands = pathString.match(/[MLHVCSQTAZmlhvcsqtaz][^MLHVCSQTAZmlhvcsqtaz]*/g) || [];
  const points = [];

  let currentX = 0;
  let currentY = 0;

  commands.forEach(command => {
    const type = command.charAt(0);
    const args = command.substring(1).trim().split(/[\s,]+/).map(Number);

    switch (type) {
      case 'M': // Move to (absolute)
        currentX = args[0];
        currentY = args[1];
        points.push({ x: currentX, y: currentY });

        // Additional point pairs are treated as line-to commands
        for (let i = 2; i < args.length; i += 2) {
          currentX = args[i];
          currentY = args[i + 1];
          points.push({ x: currentX, y: currentY });
        }
        break;

      case 'L': // Line to (absolute)
        for (let i = 0; i < args.length; i += 2) {
          currentX = args[i];
          currentY = args[i + 1];
          points.push({ x: currentX, y: currentY });
        }
        break;

      // More commands would be implemented in a complete parser
    }
  });

  return points;
}

/**
 * Convert points array back to SVG path string
 */
function pointsToSvgPath(points) {
  if (!points || !points.length) {
    return '';
  }

  let path = `M ${points[0].x} ${points[0].y}`;

  for (let i = 1; i < points.length; i++) {
    path += ` L ${points[i].x} ${points[i].y}`;
  }

  return path;
}

/**
 * Ramer–Douglas–Peucker algorithm for curve simplification
 */
function rdpSimplify(points, epsilon) {
  if (points.length <= 2) {
    return points;
  }

  // Find the point with the maximum distance
  let maxDistance = 0;
  let maxIndex = 0;

  const firstPoint = points[0];
  const lastPoint = points[points.length - 1];

  for (let i = 1; i < points.length - 1; i++) {
    const distance = perpendicularDistance(points[i], firstPoint, lastPoint);

    if (distance > maxDistance) {
      maxDistance = distance;
      maxIndex = i;
    }
  }

  // If max distance is greater than epsilon, recursively simplify
  if (maxDistance > epsilon) {
    // Recursive case
    const firstHalf = rdpSimplify(points.slice(0, maxIndex + 1), epsilon);
    const secondHalf = rdpSimplify(points.slice(maxIndex), epsilon);

    // Concat the two results
    return firstHalf.slice(0, -1).concat(secondHalf);
  } else {
    // Base case
    return [firstPoint, lastPoint];
  }
}

/**
 * Calculate the perpendicular distance from a point to a line
 */
function perpendicularDistance(point, lineStart, lineEnd) {
  const dx = lineEnd.x - lineStart.x;
  const dy = lineEnd.y - lineStart.y;

  // Line length
  const lineLength = Math.sqrt(dx * dx + dy * dy);

  if (lineLength === 0) {
    // Points are the same, return distance to that point
    return Math.sqrt(
      Math.pow(point.x - lineStart.x, 2) +
      Math.pow(point.y - lineStart.y, 2)
    );
  }

  // Calculate the perpendicular distance
  const area = Math.abs(
    (lineEnd.y - lineStart.y) * point.x -
    (lineEnd.x - lineStart.x) * point.y +
    lineEnd.x * lineStart.y -
    lineEnd.y * lineStart.x
  );

  return area / lineLength;
}
