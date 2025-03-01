import { logger } from '../utils/logger';

/**
 * Time window for metrics aggregation
 */
export enum TimeWindow {
  MINUTE = 60 * 1000,
  FIVE_MINUTES = 5 * 60 * 1000,
  FIFTEEN_MINUTES = 15 * 60 * 1000,
  HOUR = 60 * 60 * 1000,
  DAY = 24 * 60 * 60 * 1000,
}

/**
 * Metric data point with timestamp
 */
export interface MetricDataPoint<T> {
  timestamp: number;
  value: T;
}

/**
 * Database query metrics
 */
export interface QueryMetrics {
  duration: number;
  rowCount: number;
  optimized: boolean;
}

/**
 * Query optimization metrics
 */
export interface OptimizationMetrics {
  duration: number;
  improvement: number;
}

/**
 * Statistical summary
 */
export interface StatsSummary {
  min: number;
  max: number;
  avg: number;
  p50: number;  // median
  p90: number;  // 90th percentile
  p95: number;  // 95th percentile
  p99: number;  // 99th percentile
  count: number;
}

/**
 * Performance metrics for tracking and analyzing performance data
 */
export class PerformanceMetrics {
  // Store metrics with timestamps
  private queryExecutions: MetricDataPoint<QueryMetrics>[] = [];
  private queryOptimizations: MetricDataPoint<OptimizationMetrics>[] = [];
  private slowQueries: MetricDataPoint<string>[] = [];
  private cacheHits: MetricDataPoint<string>[] = [];
  private cacheMisses: MetricDataPoint<string>[] = [];

  // Maximum number of data points to store (prevent memory issues)
  private readonly maxDataPoints = 10000;

  // Retention period (default: 24 hours)
  private readonly retentionPeriod = 24 * 60 * 60 * 1000;

  constructor() {
    // Set up automatic cleanup
    setInterval(() => this.cleanup(), 15 * 60 * 1000); // Every 15 minutes
  }

  /**
   * Record a query execution
   * @param duration Query execution duration in milliseconds
   * @param rowCount Number of rows returned or affected
   * @param optimized Whether the query was optimized
   */
  public recordQueryExecution(duration: number, rowCount: number, optimized = false): void {
    this.queryExecutions.push({
      timestamp: Date.now(),
      value: { duration, rowCount, optimized },
    });

    this.ensureCapacity(this.queryExecutions);
  }

  /**
   * Record a query optimization
   * @param duration Optimization duration in milliseconds
   * @param improvement Estimated performance improvement (%)
   */
  public recordQueryOptimization(duration: number, improvement: number): void {
    this.queryOptimizations.push({
      timestamp: Date.now(),
      value: { duration, improvement },
    });

    this.ensureCapacity(this.queryOptimizations);
  }

  /**
   * Record a slow query
   * @param query SQL query
   */
  public recordSlowQuery(query: string): void {
    this.slowQueries.push({
      timestamp: Date.now(),
      value: query,
    });

    this.ensureCapacity(this.slowQueries);
  }

  /**
   * Record a cache hit
   * @param queryKey Query key
   */
  public recordCacheHit(queryKey: string): void {
    this.cacheHits.push({
      timestamp: Date.now(),
      value: queryKey,
    });

    this.ensureCapacity(this.cacheHits);
  }

  /**
   * Record a cache miss
   * @param queryKey Query key
   */
  public recordCacheMiss(queryKey: string): void {
    this.cacheMisses.push({
      timestamp: Date.now(),
      value: queryKey,
    });

    this.ensureCapacity(this.cacheMisses);
  }

  /**
   * Get query execution metrics for a time window
   * @param window Time window
   * @returns Stats summary
   */
  public getQueryExecutionStats(window: TimeWindow = TimeWindow.HOUR): StatsSummary {
    const dataPoints = this.filterByTimeWindow(this.queryExecutions, window);
    const durations = dataPoints.map(dp => dp.value.duration);

    return this.calculateStats(durations);
  }

  /**
   * Get query optimization metrics for a time window
   * @param window Time window
   * @returns Stats summary
   */
  public getQueryOptimizationStats(window: TimeWindow = TimeWindow.HOUR): StatsSummary {
    const dataPoints = this.filterByTimeWindow(this.queryOptimizations, window);
    const improvements = dataPoints.map(dp => dp.value.improvement);

    return this.calculateStats(improvements);
  }

  /**
   * Get slow query frequency for a time window
   * @param window Time window
   * @returns Frequency count
   */
  public getSlowQueryFrequency(window: TimeWindow = TimeWindow.HOUR): number {
    const dataPoints = this.filterByTimeWindow(this.slowQueries, window);
    return dataPoints.length;
  }

  /**
   * Get cache hit ratio for a time window
   * @param window Time window
   * @returns Cache hit ratio (0-1)
   */
  public getCacheHitRatio(window: TimeWindow = TimeWindow.HOUR): number {
    const hits = this.filterByTimeWindow(this.cacheHits, window).length;
    const misses = this.filterByTimeWindow(this.cacheMisses, window).length;

    const total = hits + misses;
    if (total === 0) {
      return 0;
    }

    return hits / total;
  }

  /**
   * Get metrics report for all metrics
   * @param window Time window
   * @returns Metrics report
   */
  public getMetricsReport(window: TimeWindow = TimeWindow.HOUR): any {
    return {
      queryExecution: this.getQueryExecutionStats(window),
      queryOptimization: this.getQueryOptimizationStats(window),
      slowQueryFrequency: this.getSlowQueryFrequency(window),
      cacheHitRatio: this.getCacheHitRatio(window),
      window: {
        duration: window,
        start: new Date(Date.now() - window).toISOString(),
        end: new Date().toISOString(),
      },
    };
  }

  /**
   * Get time series data for query execution durations
   * @param window Time window
   * @param bucketSize Time bucket size in milliseconds
   * @returns Time series data
   */
  public getQueryDurationTimeSeries(
    window: TimeWindow = TimeWindow.HOUR,
    bucketSize: number = 60000 // 1 minute
  ): { timestamp: number; avg: number; count: number }[] {
    const now = Date.now();
    const startTime = now - window;

    // Filter data points within the time window
    const dataPoints = this.filterByTimeWindow(this.queryExecutions, window);

    // Create buckets
    const buckets: Map<number, number[]> = new Map();

    // Calculate bucket start times
    const numBuckets = Math.ceil(window / bucketSize);
    for (let i = 0; i < numBuckets; i++) {
      const bucketStart = startTime + (i * bucketSize);
      buckets.set(bucketStart, []);
    }

    // Assign data points to buckets
    for (const dp of dataPoints) {
      const bucketIndex = Math.floor((dp.timestamp - startTime) / bucketSize);
      const bucketStart = startTime + (bucketIndex * bucketSize);

      if (buckets.has(bucketStart)) {
        buckets.get(bucketStart)!.push(dp.value.duration);
      }
    }

    // Calculate averages for each bucket
    const result: { timestamp: number; avg: number; count: number }[] = [];

    for (const [timestamp, values] of buckets.entries()) {
      const count = values.length;
      const avg = count > 0 ? values.reduce((sum, val) => sum + val, 0) / count : 0;

      result.push({
        timestamp,
        avg,
        count,
      });
    }

    return result;
  }

  /**
   * Get time series data for query optimization improvement
   * @param window Time window
   * @param bucketSize Time bucket size in milliseconds
   * @returns Time series data
   */
  public getOptimizationImprovementTimeSeries(
    window: TimeWindow = TimeWindow.HOUR,
    bucketSize: number = 60000 // 1 minute
  ): { timestamp: number; avg: number; count: number }[] {
    const now = Date.now();
    const startTime = now - window;

    // Filter data points within the time window
    const dataPoints = this.filterByTimeWindow(this.queryOptimizations, window);

    // Create buckets
    const buckets: Map<number, number[]> = new Map();

    // Calculate bucket start times
    const numBuckets = Math.ceil(window / bucketSize);
    for (let i = 0; i < numBuckets; i++) {
      const bucketStart = startTime + (i * bucketSize);
      buckets.set(bucketStart, []);
    }

    // Assign data points to buckets
    for (const dp of dataPoints) {
      const bucketIndex = Math.floor((dp.timestamp - startTime) / bucketSize);
      const bucketStart = startTime + (bucketIndex * bucketSize);

      if (buckets.has(bucketStart)) {
        buckets.get(bucketStart)!.push(dp.value.improvement);
      }
    }

    // Calculate averages for each bucket
    const result: { timestamp: number; avg: number; count: number }[] = [];

    for (const [timestamp, values] of buckets.entries()) {
      const count = values.length;
      const avg = count > 0 ? values.reduce((sum, val) => sum + val, 0) / count : 0;

      result.push({
        timestamp,
        avg,
        count,
      });
    }

    return result;
  }

  /**
   * Filter data points by time window
   * @param dataPoints Data points
   * @param window Time window
   * @returns Filtered data points
   */
  private filterByTimeWindow<T>(
    dataPoints: MetricDataPoint<T>[],
    window: TimeWindow
  ): MetricDataPoint<T>[] {
    const now = Date.now();
    const cutoff = now - window;

    return dataPoints.filter(dp => dp.timestamp >= cutoff);
  }

  /**
   * Calculate statistical summary
   * @param values Numeric values
   * @returns Stats summary
   */
  private calculateStats(values: number[]): StatsSummary {
    if (values.length === 0) {
      return {
        min: 0,
        max: 0,
        avg: 0,
        p50: 0,
        p90: 0,
        p95: 0,
        p99: 0,
        count: 0,
      };
    }

    // Sort values for percentiles
    const sortedValues = [...values].sort((a, b) => a - b);

    // Calculate basics
    const min = sortedValues[0];
    const max = sortedValues[sortedValues.length - 1];
    const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
    const count = values.length;

    // Calculate percentiles
    const p50 = this.getPercentile(sortedValues, 50);
    const p90 = this.getPercentile(sortedValues, 90);
    const p95 = this.getPercentile(sortedValues, 95);
    const p99 = this.getPercentile(sortedValues, 99);

    return {
      min,
      max,
      avg,
      p50,
      p90,
      p95,
      p99,
      count,
    };
  }

  /**
   * Calculate percentile value
   * @param sortedValues Sorted values
   * @param percentile Percentile (0-100)
   * @returns Percentile value
   */
  private getPercentile(sortedValues: number[], percentile: number): number {
    if (sortedValues.length === 0) {
      return 0;
    }

    if (sortedValues.length === 1) {
      return sortedValues[0];
    }

    const index = (percentile / 100) * (sortedValues.length - 1);
    const lower = Math.floor(index);
    const upper = Math.ceil(index);

    if (lower === upper) {
      return sortedValues[lower];
    }

    const weight = index - lower;
    return sortedValues[lower] * (1 - weight) + sortedValues[upper] * weight;
  }

  /**
   * Ensure collection doesn't exceed max capacity
   * @param collection Data collection
   */
  private ensureCapacity<T>(collection: MetricDataPoint<T>[]): void {
    if (collection.length > this.maxDataPoints) {
      // Remove oldest data points
      collection.splice(0, collection.length - this.maxDataPoints);
    }
  }

  /**
   * Clean up old data points
   */
  private cleanup(): void {
    const now = Date.now();
    const cutoff = now - this.retentionPeriod;

    // Remove data points older than retention period
    this.removeOldDataPoints(this.queryExecutions, cutoff);
    this.removeOldDataPoints(this.queryOptimizations, cutoff);
    this.removeOldDataPoints(this.slowQueries, cutoff);
    this.removeOldDataPoints(this.cacheHits, cutoff);
    this.removeOldDataPoints(this.cacheMisses, cutoff);

    logger.debug('Cleaned up old performance metrics', {
      retentionPeriod: this.retentionPeriod,
      queryExecutions: this.queryExecutions.length,
      queryOptimizations: this.queryOptimizations.length,
      slowQueries: this.slowQueries.length,
    });
  }

  /**
   * Remove data points older than cutoff
   * @param collection Data collection
   * @param cutoff Cutoff timestamp
   */
  private removeOldDataPoints<T>(
    collection: MetricDataPoint<T>[],
    cutoff: number
  ): void {
    let i = 0;
    while (i < collection.length && collection[i].timestamp < cutoff) {
      i++;
    }

    if (i > 0) {
      collection.splice(0, i);
    }
  }
}
