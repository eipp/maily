import { useEffect, useRef } from 'react';

// Performance benchmarks
const PERFORMANCE_BENCHMARKS = {
  FPS_THRESHOLD: 30,
  LOAD_TIME_THRESHOLD: 2000, // 2 seconds
  RENDER_TIME_THRESHOLD: 50, // 50ms
  API_RESPONSE_THRESHOLD: 200, // 200ms
};

export function measurePerformance() {
  if (typeof window === 'undefined' || !window.performance) {
    return null;
  }

  try {
    const navigationEntry = window.performance.getEntriesByType(
      'navigation'
    )[0] as PerformanceNavigationTiming;
    const paintEntries = window.performance.getEntriesByType('paint');
    const lcpEntry = window.performance.getEntriesByName('largest-contentful-paint').pop();

    const metrics = {
      navigationTiming: navigationEntry || null,
      paintTiming: paintEntries || null,
      largestContentfulPaint: lcpEntry || null,
      loadTime: navigationEntry ? navigationEntry.loadEventEnd - navigationEntry.startTime : null,
      firstPaint: paintEntries?.find(entry => entry.name === 'first-paint')?.startTime || null,
      firstContentfulPaint:
        paintEntries?.find(entry => entry.name === 'first-contentful-paint')?.startTime || null,
    };

    // Check against benchmarks
    if (metrics.loadTime && metrics.loadTime > PERFORMANCE_BENCHMARKS.LOAD_TIME_THRESHOLD) {
      console.warn(
        `Page load time (${metrics.loadTime}ms) exceeds threshold (${PERFORMANCE_BENCHMARKS.LOAD_TIME_THRESHOLD}ms)`
      );
    }

    return metrics;
  } catch (error) {
    console.error('Error measuring performance:', error);
    return null;
  }
}

export function measureFrameRate() {
  if (typeof window === 'undefined' || !window.performance) {
    return;
  }

  let frameCount = 0;
  let lastTime = window.performance.now();
  let animationFrameId: number;

  const countFrames = () => {
    const currentTime = window.performance.now();
    frameCount++;

    if (currentTime - lastTime >= 1000) {
      const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));

      if (fps < PERFORMANCE_BENCHMARKS.FPS_THRESHOLD) {
        console.warn(
          `Low FPS detected: ${fps} (threshold: ${PERFORMANCE_BENCHMARKS.FPS_THRESHOLD})`
        );
      } else {
        console.log('Current FPS:', fps);
      }

      frameCount = 0;
      lastTime = currentTime;
    }

    animationFrameId = requestAnimationFrame(countFrames);
  };

  animationFrameId = requestAnimationFrame(countFrames);

  // Return cleanup function
  return () => {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
  };
}

export function usePerformanceMonitoring(componentName: string) {
  const renderStartTime = useRef<number>(0);
  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    // Start FPS monitoring
    cleanupRef.current = measureFrameRate();

    // Measure initial render time
    renderStartTime.current = performance.now();

    return () => {
      if (cleanupRef.current) {
        cleanupRef.current();
      }
    };
  }, []);

  useEffect(() => {
    const renderTime = performance.now() - renderStartTime.current;
    if (renderTime > PERFORMANCE_BENCHMARKS.RENDER_TIME_THRESHOLD) {
      console.warn(
        `${componentName} render time (${renderTime}ms) exceeds threshold (${PERFORMANCE_BENCHMARKS.RENDER_TIME_THRESHOLD}ms)`
      );
    }
  });

  return {
    measureApiCall: async <T>(apiCall: () => Promise<T>): Promise<T> => {
      const startTime = performance.now();
      try {
        const result = await apiCall();
        const duration = performance.now() - startTime;

        if (duration > PERFORMANCE_BENCHMARKS.API_RESPONSE_THRESHOLD) {
          console.warn(
            `API call exceeded response threshold: ${duration}ms (threshold: ${PERFORMANCE_BENCHMARKS.API_RESPONSE_THRESHOLD}ms)`
          );
        }

        return result;
      } catch (error) {
        const duration = performance.now() - startTime;
        console.error(`API call failed after ${duration}ms:`, error);
        throw error;
      }
    },
  };
}

export function createPerformanceObserver(callback: (entry: PerformanceEntry) => void) {
  if (typeof window === 'undefined' || !window.PerformanceObserver) {
    console.warn('PerformanceObserver not supported');
    return null;
  }

  try {
    const observer = new PerformanceObserver(list => {
      list.getEntries().forEach(callback);
    });

    observer.observe({
      entryTypes: ['navigation', 'resource', 'paint', 'largest-contentful-paint'],
    });

    return observer;
  } catch (error) {
    console.error('Error creating PerformanceObserver:', error);
    return null;
  }
}
