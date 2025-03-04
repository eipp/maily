/**
 * Canvas utility functions
 */

/**
 * Generates a thumbnail image for a specific layer
 * 
 * @param canvasRef - React ref to the canvas component
 * @param layerId - ID of the layer to generate thumbnail for
 * @returns Base64 encoded thumbnail image
 */
export function generateThumbnailForLayer(
  canvasRef: React.RefObject<any>,
  layerId: string
): string | undefined {
  try {
    if (!canvasRef.current) return undefined;
    
    const stage = canvasRef.current;
    const thumbnailSize = 50; // Size of the thumbnail in pixels
    
    // Create a temporary canvas
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = thumbnailSize;
    tempCanvas.height = thumbnailSize;
    const tempContext = tempCanvas.getContext('2d');
    
    if (!tempContext) return undefined;
    
    // Find all shapes on this layer
    const shapes = stage.find((node: any) => node.attrs?.layerId === layerId);
    
    if (shapes.length === 0) {
      // Create a basic empty thumbnail
      tempContext.fillStyle = '#f0f0f0';
      tempContext.fillRect(0, 0, thumbnailSize, thumbnailSize);
      tempContext.strokeStyle = '#ccc';
      tempContext.strokeRect(0, 0, thumbnailSize, thumbnailSize);
      
      return tempCanvas.toDataURL();
    }
    
    // Calculate the bounding box of all shapes in this layer
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    
    shapes.forEach((shape: any) => {
      const box = shape.getClientRect();
      minX = Math.min(minX, box.x);
      minY = Math.min(minY, box.y);
      maxX = Math.max(maxX, box.x + box.width);
      maxY = Math.max(maxY, box.y + box.height);
    });
    
    // Calculate dimensions
    const width = maxX - minX;
    const height = maxY - minY;
    
    // Calculate scale to fit in thumbnail size while maintaining aspect ratio
    const scale = Math.min(
      thumbnailSize / width,
      thumbnailSize / height
    );
    
    // Draw each shape on temporary canvas
    tempContext.clearRect(0, 0, thumbnailSize, thumbnailSize);
    tempContext.save();
    
    // Center and scale
    const offsetX = (thumbnailSize - width * scale) / 2;
    const offsetY = (thumbnailSize - height * scale) / 2;
    
    tempContext.translate(offsetX, offsetY);
    tempContext.scale(scale, scale);
    tempContext.translate(-minX, -minY);
    
    // Create a simplified thumbnail
    shapes.forEach((shape: any) => {
      const type = shape.getClassName();
      
      switch (type) {
        case 'Rect':
          tempContext.fillStyle = shape.fill();
          tempContext.fillRect(
            shape.x(),
            shape.y(),
            shape.width(),
            shape.height()
          );
          break;
          
        case 'Circle':
          tempContext.fillStyle = shape.fill();
          tempContext.beginPath();
          tempContext.arc(
            shape.x(),
            shape.y(),
            shape.radius(),
            0,
            Math.PI * 2
          );
          tempContext.fill();
          break;
          
        case 'Text':
          tempContext.fillStyle = shape.fill();
          tempContext.font = `${shape.fontSize()}px ${shape.fontFamily() || 'Arial'}`;
          tempContext.fillText(
            shape.text().substring(0, 3) + '...',
            shape.x(),
            shape.y()
          );
          break;
      }
    });
    
    tempContext.restore();
    
    // Return base64 encoded image
    return tempCanvas.toDataURL();
  } catch (error) {
    console.error('Error generating layer thumbnail:', error);
    return undefined;
  }
}

/**
 * Creates a draggable element from a source element
 * Used for custom drag preview for React DnD
 * 
 * @param element - Source element to create drag preview from
 * @returns HTML Element for drag preview
 */
export function createDragPreview(element: HTMLElement): HTMLElement {
  const rect = element.getBoundingClientRect();
  const preview = element.cloneNode(true) as HTMLElement;
  
  // Apply styles for the preview
  preview.style.position = 'fixed';
  preview.style.top = '0';
  preview.style.left = '0';
  preview.style.zIndex = '1000';
  preview.style.width = `${rect.width}px`;
  preview.style.height = `${rect.height}px`;
  preview.style.opacity = '0.8';
  preview.style.pointerEvents = 'none';
  preview.style.transform = 'translate(-50%, -50%)';
  preview.style.boxShadow = '0 5px 10px rgba(0,0,0,0.2)';
  
  // Add a class for styling
  preview.classList.add('drag-preview');
  
  // Add to document body
  document.body.appendChild(preview);
  
  return preview;
}

/**
 * Calculate the bounds of shapes on a layer
 * 
 * @param shapes - Array of shapes
 * @returns Object with minX, minY, maxX, maxY, width, height
 */
export function calculateLayerBounds(shapes: any[]): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
} {
  if (shapes.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 0, height: 0 };
  }
  
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  
  shapes.forEach((shape) => {
    const { x, y, width, height, radius } = shape;
    
    if (shape.type === 'rect') {
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + width!);
      maxY = Math.max(maxY, y + height!);
    } else if (shape.type === 'circle') {
      minX = Math.min(minX, x - radius!);
      minY = Math.min(minY, y - radius!);
      maxX = Math.max(maxX, x + radius!);
      maxY = Math.max(maxY, y + radius!);
    } else if (shape.type === 'text') {
      // Approximation for text size
      const approxWidth = (shape.text?.length || 0) * (shape.fontSize || 12) * 0.6;
      const approxHeight = shape.fontSize || 12;
      
      minX = Math.min(minX, x);
      minY = Math.min(minY, y - approxHeight);
      maxX = Math.max(maxX, x + approxWidth);
      maxY = Math.max(maxY, y);
    }
  });
  
  return {
    minX,
    minY,
    maxX,
    maxY,
    width: maxX - minX,
    height: maxY - minY,
  };
}

/**
 * Create a snapshot of the entire canvas as an image
 * 
 * @param canvasRef - React ref to the canvas component
 * @returns Promise that resolves to a base64 encoded image
 */
export function createCanvasSnapshot(canvasRef: React.RefObject<any>): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!canvasRef.current) {
      reject(new Error('Canvas reference is not available'));
      return;
    }
    
    try {
      const dataURL = canvasRef.current.toDataURL({
        pixelRatio: 2, // Higher quality
        mimeType: 'image/png',
      });
      
      resolve(dataURL);
    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Helper function to create a unique layer name
 * 
 * @param existingLayers - Array of existing layers
 * @param baseName - Base name for the layer
 * @returns Unique layer name
 */
export function createUniqueLayerName(
  existingLayers: { name: string }[],
  baseName: string = 'Layer'
): string {
  const existingNames = existingLayers.map(layer => layer.name);
  let counter = existingLayers.length + 1;
  let newName = `${baseName} ${counter}`;
  
  while (existingNames.includes(newName)) {
    counter++;
    newName = `${baseName} ${counter}`;
  }
  
  return newName;
}