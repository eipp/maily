import { renderHook, act } from '@testing-library/react';
import {
  measurePerformance,
  measureFrameRate,
  usePerformanceMonitoring,
  createPerformanceObserver,
} from '../../utils/performance';

describe('Performance Utilities', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(window, 'requestAnimationFrame').mockImplementation(cb => {
      setTimeout(() => cb(performance.now()), 16);
      return 1;
    });
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  describe('measurePerformance', () => {
    it('returns null when window.performance is not available', () => {
      const originalPerformance = window.performance;
      const windowWithPerformance = window as { performance?: unknown };
      delete windowWithPerformance.performance;

      expect(measurePerformance()).toBeNull();

      window.performance = originalPerformance;
    });

    it('measures performance metrics', () => {
      const mockNavigationTiming = {
        startTime: 0,
        loadEventEnd: 1000,
        duration: 1000,
        entryType: 'navigation',
        name: 'navigation',
        toJSON: () => ({}),
        domComplete: 1000,
        domContentLoadedEventEnd: 800,
        domContentLoadedEventStart: 700,
        domInteractive: 600,
        loadEventStart: 900,
        redirectCount: 0,
        type: 'navigate',
        unloadEventEnd: 500,
        unloadEventStart: 400,
        activationStart: 0,
        initiatorType: 'navigation',
        nextHopProtocol: 'h2',
        renderBlockingStatus: 'blocking',
        responseStart: 300,
        transferSize: 1000,
        encodedBodySize: 800,
        decodedBodySize: 1000,
        serverTiming: [],
        connectEnd: 200,
        connectStart: 100,
        domainLookupEnd: 90,
        domainLookupStart: 80,
        fetchStart: 70,
        requestStart: 60,
        responseEnd: 50,
        secureConnectionStart: 40,
      } as unknown as PerformanceNavigationTiming;

      const mockPaintEntries: PerformancePaintTiming[] = [
        {
          name: 'first-paint',
          startTime: 100,
          duration: 0,
          entryType: 'paint',
          toJSON: () => ({}),
        },
        {
          name: 'first-contentful-paint',
          startTime: 200,
          duration: 0,
          entryType: 'paint',
          toJSON: () => ({}),
        },
      ];

      const mockLCP: PerformanceEntry = {
        startTime: 500,
        duration: 0,
        entryType: 'largest-contentful-paint',
        name: 'largest-contentful-paint',
        toJSON: () => ({}),
      };

      jest.spyOn(window.performance, 'getEntriesByType').mockImplementation((type: string) => {
        if (type === 'navigation') return [mockNavigationTiming];
        if (type === 'paint') return mockPaintEntries;
        return [];
      });

      jest.spyOn(window.performance, 'getEntriesByName').mockReturnValue([mockLCP]);

      const metrics = measurePerformance();

      expect(metrics).toEqual(
        expect.objectContaining({
          loadTime: 1000,
          firstPaint: 100,
          firstContentfulPaint: 200,
        })
      );
    });

    it('handles errors gracefully', () => {
      jest.spyOn(window.performance, 'getEntriesByType').mockImplementation(() => {
        throw new Error('Test error');
      });

      expect(measurePerformance()).toBeNull();
      expect(console.error).toHaveBeenCalledWith('Error measuring performance:', expect.any(Error));
    });
  });

  describe('measureFrameRate', () => {
    it('should measure frame rate correctly', () => {
      const cleanup = measureFrameRate();

      // Simulate 10 frames
      for (let i = 0; i < 10; i++) {
        jest.advanceTimersByTime(16);
      }

      cleanup?.();

      // Verify frame rate calculation
      const entries = performance.getEntriesByType('measure');
      expect(entries.length).toBeGreaterThan(0);
    });
  });

  describe('usePerformanceMonitoring', () => {
    it('measures render time and warns if threshold exceeded', async () => {
      renderHook(() => usePerformanceMonitoring('TestComponent'));

      // Simulate slow render
      jest.spyOn(performance, 'now').mockReturnValueOnce(0).mockReturnValueOnce(100);

      act(() => {
        jest.runOnlyPendingTimers();
      });

      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('TestComponent render time')
      );
    });

    it('measures API call duration and warns if threshold exceeded', async () => {
      const { result } = renderHook(() => usePerformanceMonitoring('TestComponent'));

      const slowApiCall = () =>
        new Promise<string>(resolve => {
          setTimeout(() => resolve('data'), 300);
        });

      jest.spyOn(performance, 'now').mockReturnValueOnce(0).mockReturnValueOnce(300);

      await act(async () => {
        await result.current.measureApiCall(slowApiCall);
      });

      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('API call exceeded response threshold:')
      );
    });

    it('handles API call errors', async () => {
      const { result } = renderHook(() => usePerformanceMonitoring('TestComponent'));

      const failingApiCall = () => Promise.reject(new Error('API Error'));

      await expect(result.current.measureApiCall(failingApiCall)).rejects.toThrow('API Error');

      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('API call failed after'),
        expect.any(Error)
      );
    });
  });

  describe('createPerformanceObserver', () => {
    it('creates observer and observes specified entry types', () => {
      const mockObserve = jest.fn();
      const mockDisconnect = jest.fn();

      class MockPerformanceObserver {
        constructor(callback: (list: PerformanceObserverEntryList) => void) {
          this.callback = callback;
        }
        observe = mockObserve;
        disconnect = mockDisconnect;
        callback: (list: PerformanceObserverEntryList) => void;
      }

      const windowWithPerformanceObserver = window as unknown as {
        PerformanceObserver: typeof MockPerformanceObserver;
      };
      windowWithPerformanceObserver.PerformanceObserver = MockPerformanceObserver;

      const callback = jest.fn();
      const observer = createPerformanceObserver(callback);

      expect(observer).toBeTruthy();
      expect(mockObserve).toHaveBeenCalledWith({
        entryTypes: ['navigation', 'resource', 'paint', 'largest-contentful-paint'],
      });
    });

    it('handles observer creation errors', () => {
      class MockPerformanceObserver {
        constructor() {
          throw new Error('Observer error');
        }
      }

      const windowWithPerformanceObserver = window as unknown as {
        PerformanceObserver: typeof MockPerformanceObserver;
      };
      windowWithPerformanceObserver.PerformanceObserver = MockPerformanceObserver;

      const callback = jest.fn();
      const observer = createPerformanceObserver(callback);

      expect(observer).toBeNull();
      expect(console.error).toHaveBeenCalledWith(
        'Error creating PerformanceObserver:',
        expect.any(Error)
      );
    });

    it('returns null when PerformanceObserver is not supported', () => {
      const windowWithPerformanceObserver = window as { PerformanceObserver?: unknown };
      delete windowWithPerformanceObserver.PerformanceObserver;

      const callback = jest.fn();
      const observer = createPerformanceObserver(callback);

      expect(observer).toBeNull();
      expect(console.warn).toHaveBeenCalledWith('PerformanceObserver not supported');
    });
  });
});
