'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import { useCanvasWorker } from '../hooks/useCanvasWorker';
import { usePerformanceMonitoring } from '../utils/performance';
import { createDynamicComponent } from '../utils/dynamicImports';

interface CanvasProps {
  width?: number;
  height?: number;
  className?: string;
}

function Canvas({ width = 800, height = 600, className = '' }: CanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const contextRef = useRef<CanvasRenderingContext2D | null>(null);
  const [imageData, setImageData] = useState<ImageData | null>(null);
  const { transformImage, applyFilter, computeHistogram } = useCanvasWorker();
  const { measureApiCall } = usePerformanceMonitoring('Canvas');

  // Initialize canvas context with performance monitoring
  useEffect(() => {
    if (!canvasRef.current) return;

    measureApiCall(async () => {
      const canvas = canvasRef.current!;
      const context = canvas.getContext('2d');
      
      if (!context) {
        throw new Error('Could not get canvas context');
      }

      // Enable image smoothing for better quality
      context.imageSmoothingEnabled = true;
      context.imageSmoothingQuality = 'high';
      
      contextRef.current = context;
      
      // Set initial canvas state
      context.fillStyle = '#ffffff';
      context.fillRect(0, 0, width, height);
      
      // Get initial image data
      const initialImageData = context.getImageData(0, 0, width, height);
      setImageData(initialImageData);
    });
  }, [width, height, measureApiCall]);

  const draw = useCallback((data: ImageData) => {
    if (!contextRef.current) return;

    requestAnimationFrame(() => {
      contextRef.current!.putImageData(data, 0, 0);
      setImageData(data);
    });
  }, []);

  const handleBrightnessAdjustment = useCallback(async (value: number) => {
    if (!imageData) return;

    try {
      const result = await measureApiCall(() => 
        transformImage(imageData, 'brightness', value)
      );
      draw(result);
    } catch (error) {
      console.error('Error adjusting brightness:', error);
    }
  }, [imageData, transformImage, measureApiCall, draw]);

  const handleFilterApplication = useCallback(async (filterType: 'grayscale' | 'sepia' | 'invert') => {
    if (!imageData) return;

    try {
      const result = await measureApiCall(() => 
        applyFilter(imageData, filterType)
      );
      draw(result);
    } catch (error) {
      console.error('Error applying filter:', error);
    }
  }, [imageData, applyFilter, measureApiCall, draw]);

  const handleHistogramComputation = useCallback(async () => {
    if (!imageData) return;

    try {
      const histogram = await measureApiCall(() => 
        computeHistogram(imageData)
      );
      console.log('Histogram data:', histogram);
      return histogram;
    } catch (error) {
      console.error('Error computing histogram:', error);
      return null;
    }
  }, [imageData, computeHistogram, measureApiCall]);

  const loadImage = useCallback(async (url: string) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.src = URL.createObjectURL(blob);

      await new Promise<void>((resolve, reject) => {
        img.onload = () => {
          if (!contextRef.current) {
            reject(new Error('Canvas context not initialized'));
            return;
          }

          const ctx = contextRef.current;
          const scaleFactor = Math.min(
            width / img.width,
            height / img.height
          );

          const scaledWidth = img.width * scaleFactor;
          const scaledHeight = img.height * scaleFactor;
          const x = (width - scaledWidth) / 2;
          const y = (height - scaledHeight) / 2;

          ctx.clearRect(0, 0, width, height);
          ctx.drawImage(img, x, y, scaledWidth, scaledHeight);

          const newImageData = ctx.getImageData(0, 0, width, height);
          setImageData(newImageData);

          URL.revokeObjectURL(img.src);
          resolve();
        };

        img.onerror = () => reject(new Error('Failed to load image'));
      });
    } catch (error) {
      console.error('Error loading image:', error);
    }
  }, [width, height]);

  return (
    <div className={`canvas-container ${className}`}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="canvas"
      />
      <div className="canvas-controls">
        <button onClick={() => handleBrightnessAdjustment(20)}>
          Increase Brightness
        </button>
        <button onClick={() => handleFilterApplication('grayscale')}>
          Grayscale
        </button>
        <button onClick={handleHistogramComputation}>
          Compute Histogram
        </button>
      </div>
    </div>
  );
}

export default createDynamicComponent(
  () => Promise.resolve({ default: Canvas }),
  {
    ssr: false,
    delay: 300,
    timeout: 5000
  }
); 