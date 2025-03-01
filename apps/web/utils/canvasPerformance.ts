/**
 * Canvas Performance Monitoring Utility
 *
 * This utility provides performance monitoring for Canvas operations,
 * including rendering, collaboration, and user interactions.
 */

type PerformanceMetric = {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  metadata?: Record<string, any>;
};

type PerformanceReport = {
  metrics: PerformanceMetric[];
  averages: Record<string, number>;
  timestamp: string;
  sessionId: string;
};

class CanvasPerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private sessionId: string;
  private isEnabled: boolean = true;
  private metricsBuffer: Record<string, number[]> = {};
  private bufferSize: number = 50;
  private thresholds: Record<string, number> = {
    'render': 16, // 60fps target (16ms)
    'collaboration.update': 100,
    'collaboration.sync': 500,
    'interaction.drag': 16,
    'interaction.zoom': 16,
    'interaction.select': 16,
  };

  constructor() {
    this.sessionId = `canvas_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

    // Check if performance API is available
    if (typeof performance === 'undefined') {
      console.warn('Performance API not available, monitoring will be disabled');
      this.isEnabled = false;
    }
  }

  /**
   * Start timing a performance metric
   */
  startMetric(name: string, metadata?: Record<string, any>): string {
    if (!this.isEnabled) return name;

    const id = `${name}_${Date.now()}`;
    this.metrics.push({
      name,
      startTime: performance.now(),
      metadata
    });

    return id;
  }

  /**
   * End timing a performance metric
   */
  endMetric(name: string): number | undefined {
    if (!this.isEnabled) return;

    const index = this.metrics.findIndex(m => m.name === name && m.endTime === undefined);
    if (index === -1) return;

    const now = performance.now();
    const metric = this.metrics[index];
    metric.endTime = now;
    metric.duration = now - metric.startTime;

    // Add to metrics buffer for averaging
    if (!this.metricsBuffer[name]) {
      this.metricsBuffer[name] = [];
    }

    this.metricsBuffer[name].push(metric.duration);

    // Keep buffer at max size
    if (this.metricsBuffer[name].length > this.bufferSize) {
      this.metricsBuffer[name].shift();
    }

    // Check if metric exceeds threshold
    const threshold = this.getThreshold(name);
    if (threshold && metric.duration > threshold) {
      console.warn(`Canvas performance metric "${name}" exceeded threshold: ${metric.duration.toFixed(2)}ms (threshold: ${threshold}ms)`);
    }

    return metric.duration;
  }

  /**
   * Measure a function execution time
   */
  measure<T>(name: string, fn: () => T, metadata?: Record<string, any>): T {
    this.startMetric(name, metadata);
    const result = fn();
    this.endMetric(name);
    return result;
  }

  /**
   * Measure an async function execution time
   */
  async measureAsync<T>(name: string, fn: () => Promise<T>, metadata?: Record<string, any>): Promise<T> {
    this.startMetric(name, metadata);
    try {
      const result = await fn();
      this.endMetric(name);
      return result;
    } catch (error) {
      this.endMetric(name);
      throw error;
    }
  }

  /**
   * Get the average duration for a specific metric
   */
  getAverageMetric(name: string): number | undefined {
    const buffer = this.metricsBuffer[name];
    if (!buffer || buffer.length === 0) return undefined;

    const sum = buffer.reduce((acc, val) => acc + val, 0);
    return sum / buffer.length;
  }

  /**
   * Get all average metrics
   */
  getAllAverageMetrics(): Record<string, number> {
    const averages: Record<string, number> = {};

    Object.keys(this.metricsBuffer).forEach(name => {
      const avg = this.getAverageMetric(name);
      if (avg !== undefined) {
        averages[name] = avg;
      }
    });

    return averages;
  }

  /**
   * Get threshold for a specific metric
   */
  getThreshold(name: string): number | undefined {
    // Check for exact match
    if (this.thresholds[name]) {
      return this.thresholds[name];
    }

    // Check for prefix match
    for (const [key, value] of Object.entries(this.thresholds)) {
      if (name.startsWith(key)) {
        return value;
      }
    }

    return undefined;
  }

  /**
   * Set threshold for a specific metric
   */
  setThreshold(name: string, threshold: number): void {
    this.thresholds[name] = threshold;
  }

  /**
   * Generate a performance report
   */
  generateReport(): PerformanceReport {
    return {
      metrics: this.metrics.filter(m => m.duration !== undefined),
      averages: this.getAllAverageMetrics(),
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId
    };
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics = [];
  }

  /**
   * Enable or disable performance monitoring
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }
}

// Export singleton instance
export const canvasPerformance = new CanvasPerformanceMonitor();

// Export decorator for class methods
export function measurePerformance(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const originalMethod = descriptor.value;

  descriptor.value = function(...args: any[]) {
    const metricName = `${target.constructor.name}.${propertyKey}`;
    return canvasPerformance.measure(metricName, () => originalMethod.apply(this, args));
  };

  return descriptor;
}

// Export decorator for async class methods
export function measureAsyncPerformance(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const originalMethod = descriptor.value;

  descriptor.value = async function(...args: any[]) {
    const metricName = `${target.constructor.name}.${propertyKey}`;
    return await canvasPerformance.measureAsync(metricName, () => originalMethod.apply(this, args));
  };

  return descriptor;
}
