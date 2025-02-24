import { renderHook, act } from '@testing-library/react';
import {
  measurePerformance,
  measureFrameRate,
  usePerformanceMonitoring,
  createPerformanceObserver
} from '../../utils/performance';

describe('Performance Utilities', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
    jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  describe('measurePerformance', () => {
    it('returns null when window.performance is not available', () => {
      const originalPerformance = window.performance;
      delete (window as any).performance;

      expect(measurePerformance()).toBeNull();

      window.performance = originalPerformance;
    });

    it('measures performance metrics', () => {
      const mockNavigationTiming = {
        startTime: 0,
        loadEventEnd: 1000
      };

      const mockPaintEntries = [
        { name: 'first-paint', startTime: 100 },
        { name: 'first-contentful-paint', startTime: 200 }
      ];

      const mockLCP = { startTime: 500 };

      jest.spyOn(window.performance, 'getEntriesByType')
        .mockImplementation((type) => {
          if (type === 'navigation') return [mockNavigationTiming];
          if (type === 'paint') return mockPaintEntries;
          return [];
        });

      jest.spyOn(window.performance, 'getEntriesByName')
        .mockReturnValue([mockLCP]);

      const metrics = measurePerformance();

      expect(metrics).toEqual(expect.objectContaining({
        loadTime: 1000,
        firstPaint: 100,
        firstContentfulPaint: 200
      }));
    });

    it('handles errors gracefully', () => {
      jest.spyOn(window.performance, 'getEntriesByType')
        .mockImplementation(() => { throw new Error('Test error'); });

      expect(measurePerformance()).toBeNull();
      expect(console.error).toHaveBeenCalledWith(
        'Error measuring performance:',
        expect.any(Error)
      );
    });
  });

  describe('measureFrameRate', () => {
    it('measures FPS and logs warnings for low FPS', () => {
      const cleanup = measureFrameRate();

      // Simulate 30 frames in 2 seconds (15 FPS)
      for (let i = 0; i < 30; i++) {
        jest.advanceTimersByTime(1000 / 15);
        window.requestAnimationFrame.mock.calls[i][0](performance.now());
      }

      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('Low FPS detected:')
      );

      cleanup?.();
    });

    it('cleans up animation frame on cleanup', () => {
      const cleanup = measureFrameRate();
      
      cleanup?.();
      
      expect(window.cancelAnimationFrame).toHaveBeenCalled();
    });
  });

  describe('usePerformanceMonitoring', () => {
    it('measures render time and warns if threshold exceeded', async () => {
      const { result } = renderHook(() => usePerformanceMonitoring('TestComponent'));

      // Simulate slow render
      jest.spyOn(performance, 'now')
        .mockReturnValueOnce(0)
        .mockReturnValueOnce(100);

      act(() => {
        jest.runOnlyPendingTimers();
      });

      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('TestComponent render time')
      );
    });

    it('measures API call duration and warns if threshold exceeded', async () => {
      const { result } = renderHook(() => usePerformanceMonitoring('TestComponent'));

      const slowApiCall = () => new Promise(resolve => {
        setTimeout(() => resolve('data'), 300);
      });

      jest.spyOn(performance, 'now')
        .mockReturnValueOnce(0)
        .mockReturnValueOnce(300);

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

      await expect(
        result.current.measureApiCall(failingApiCall)
      ).rejects.toThrow('API Error');

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
        constructor(callback: (list: any) => void) {
          this.callback = callback;
        }
        observe = mockObserve;
        disconnect = mockDisconnect;
        callback: (list: any) => void;
      }

      (window as any).PerformanceObserver = MockPerformanceObserver;

      const callback = jest.fn();
      const observer = createPerformanceObserver(callback);

      expect(observer).toBeTruthy();
      expect(mockObserve).toHaveBeenCalledWith({
        entryTypes: ['navigation', 'resource', 'paint', 'largest-contentful-paint']
      });
    });

    it('handles observer creation errors', () => {
      class MockPerformanceObserver {
        constructor() {
          throw new Error('Observer error');
        }
      }

      (window as any).PerformanceObserver = MockPerformanceObserver;

      const callback = jest.fn();
      const observer = createPerformanceObserver(callback);

      expect(observer).toBeNull();
      expect(console.error).toHaveBeenCalledWith(
        'Error creating PerformanceObserver:',
        expect.any(Error)
      );
    });

    it('returns null when PerformanceObserver is not supported', () => {
      delete (window as any).PerformanceObserver;

      const callback = jest.fn();
      const observer = createPerformanceObserver(callback);

      expect(observer).toBeNull();
      expect(console.warn).toHaveBeenCalledWith(
        'PerformanceObserver not supported'
      );
    });
  });
}); 