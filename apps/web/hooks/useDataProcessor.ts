import { useEffect, useRef, useCallback } from 'react';

interface DataProcessorHook {
  processAnalytics: (data: any[]) => Promise<any[]>;
  isProcessing: boolean;
  error: Error | null;
}

export function useDataProcessor(): DataProcessorHook {
  const workerRef = useRef<Worker | null>(null);
  const processingRef = useRef<boolean>(false);
  const errorRef = useRef<Error | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      workerRef.current = new Worker(
        new URL('../workers/data-processor.worker.ts', import.meta.url)
      );

      workerRef.current.onerror = error => {
        console.error('Worker error:', error);
        errorRef.current = new Error('Worker processing failed');
        processingRef.current = false;
      };
    }

    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
      }
    };
  }, []);

  const processAnalytics = useCallback((data: any[]): Promise<any[]> => {
    return new Promise((resolve, reject) => {
      if (!workerRef.current) {
        reject(new Error('Worker not initialized'));
        return;
      }

      processingRef.current = true;
      errorRef.current = null;

      const handleMessage = (event: MessageEvent) => {
        const { type, data: resultData, message } = event.data;

        if (type === 'analyticsResults') {
          processingRef.current = false;
          workerRef.current?.removeEventListener('message', handleMessage);
          resolve(resultData);
        } else if (type === 'error') {
          processingRef.current = false;
          workerRef.current?.removeEventListener('message', handleMessage);
          const error = new Error(message);
          errorRef.current = error;
          reject(error);
        }
      };

      workerRef.current.addEventListener('message', handleMessage);
      workerRef.current.postMessage({ type: 'processAnalytics', data });
    });
  }, []);

  return {
    processAnalytics,
    isProcessing: processingRef.current,
    error: errorRef.current,
  };
}
