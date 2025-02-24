'use client';

import { useEffect, useRef, useCallback } from 'react';
import { usePerformanceMonitoring } from '../utils/performance';

type WorkerOperation = 'transform' | 'filter' | 'histogram';
type FilterType = 'grayscale' | 'sepia' | 'invert';
type TransformType = 'brightness' | 'contrast' | 'saturation';

interface WorkerMessage {
  operation: WorkerOperation;
  imageData: ImageData;
  type?: FilterType | TransformType;
  value?: number;
}

interface WorkerResponse {
  result: ImageData | { red: number[]; green: number[]; blue: number[] };
  error: string | null;
}

export function useCanvasWorker() {
  const workerRef = useRef<Worker | null>(null);
  const { measureApiCall } = usePerformanceMonitoring('CanvasWorker');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      workerRef.current = new Worker(new URL('../workers/canvas.worker.ts', import.meta.url));
    }

    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
      }
    };
  }, []);

  const processImage = useCallback(
    async (message: WorkerMessage): Promise<WorkerResponse['result']> => {
      if (!workerRef.current) {
        throw new Error('Worker not initialized');
      }

      return measureApiCall(() => {
        return new Promise((resolve, reject) => {
          const worker = workerRef.current!;

          const handleMessage = (e: MessageEvent<WorkerResponse>) => {
            worker.removeEventListener('message', handleMessage);
            if (e.data.error) {
              reject(new Error(e.data.error));
            } else {
              resolve(e.data.result);
            }
          };

          worker.addEventListener('message', handleMessage);
          worker.postMessage(message);
        });
      });
    },
    [measureApiCall]
  );

  const transformImage = useCallback(
    async (imageData: ImageData, type: TransformType, value: number): Promise<ImageData> => {
      const result = await processImage({
        operation: 'transform',
        imageData,
        type,
        value,
      });
      return result as ImageData;
    },
    [processImage]
  );

  const applyFilter = useCallback(
    async (imageData: ImageData, type: FilterType): Promise<ImageData> => {
      const result = await processImage({
        operation: 'filter',
        imageData,
        type,
      });
      return result as ImageData;
    },
    [processImage]
  );

  const computeHistogram = useCallback(
    async (imageData: ImageData): Promise<{ red: number[]; green: number[]; blue: number[] }> => {
      const result = await processImage({
        operation: 'histogram',
        imageData,
      });
      return result as { red: number[]; green: number[]; blue: number[] };
    },
    [processImage]
  );

  return {
    transformImage,
    applyFilter,
    computeHistogram,
  };
}
