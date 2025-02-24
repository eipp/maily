'use client';

import React, { useRef, useEffect, useState } from 'react';
import { useCanvasWorker } from '../hooks/useCanvasWorker';
import { usePerformanceMonitoring } from '../utils/performance';

interface CanvasProps extends Record<string, unknown> {
  width: number;
  height: number;
  onImageChange?: (imageData: ImageData) => void;
}

const Canvas: React.FC<CanvasProps> = ({ width, height, onImageChange }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [imageData, setImageData] = useState<ImageData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { measureApiCall } = usePerformanceMonitoring('Canvas');
  const worker = useCanvasWorker();

  useEffect(() => {
    if (imageData && canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) {
        ctx.putImageData(imageData, 0, 0);
        onImageChange?.(imageData);
      }
    }
  }, [imageData, onImageChange]);

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !canvasRef.current) return;

    try {
      const img = new Image();
      img.src = URL.createObjectURL(file);
      await img.decode();

      const ctx = canvasRef.current.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, width, height);
        ctx.drawImage(img, 0, 0, width, height);
        const newImageData = ctx.getImageData(0, 0, width, height);
        setImageData(newImageData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading image');
    }
  };

  const handleBrightnessChange = async (value: number) => {
    if (!imageData) return;

    try {
      const result = await measureApiCall(() =>
        worker.transformImage(imageData, 'brightness', value)
      );
      setImageData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error adjusting brightness');
    }
  };

  const handleFilterChange = async (filterType: string) => {
    if (!imageData) return;

    try {
      const result = await measureApiCall(() =>
        worker.applyFilter(imageData, filterType as 'grayscale' | 'sepia' | 'invert')
      );
      setImageData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error applying filter');
    }
  };

  const handleHistogramCompute = async () => {
    if (!imageData) return;

    try {
      const histogram = await measureApiCall(() => worker.computeHistogram(imageData));
      console.log('Histogram:', histogram);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error computing histogram');
    }
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      <div className="relative">
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          className="rounded border border-gray-300"
          role="img"
          aria-label="canvas"
        />
        {error && (
          <div className="absolute inset-x-0 top-0 bg-red-500 p-2 text-sm text-white">{error}</div>
        )}
      </div>

      <div className="flex w-full max-w-md flex-col space-y-2">
        <input
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          className="block w-full text-sm text-gray-500 file:mr-4 file:rounded-full file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-blue-700 hover:file:bg-blue-100"
          aria-label="upload image"
        />

        <input
          type="range"
          min="-100"
          max="100"
          defaultValue="0"
          onChange={e => handleBrightnessChange(Number(e.target.value))}
          className="w-full"
          aria-label="brightness"
        />

        <select
          onChange={e => handleFilterChange(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
          aria-label="filter"
        >
          <option value="">Select Filter</option>
          <option value="grayscale">Grayscale</option>
          <option value="sepia">Sepia</option>
          <option value="invert">Invert</option>
        </select>

        <button
          onClick={handleHistogramCompute}
          className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
        >
          Compute Histogram
        </button>
      </div>
    </div>
  );
};

export default Canvas;
