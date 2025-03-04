/**
 * Standardized metrics configuration for all services
 * 
 * This module provides a consistent metrics configuration across all services.
 */

import { MeterProvider, MetricReader } from '@opentelemetry/sdk-metrics';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { PrometheusExporter } from '@opentelemetry/exporter-prometheus';
import { Host } from '@opentelemetry/host-metrics';

/**
 * Metrics configuration options
 */
export interface MetricsConfig {
  /**
   * Service name
   */
  serviceName: string;
  
  /**
   * Service version
   */
  serviceVersion?: string;
  
  /**
   * Environment
   */
  environment?: string;
  
  /**
   * Additional resource attributes
   */
  resourceAttributes?: Record<string, string>;
  
  /**
   * Prometheus exporter configuration
   */
  prometheus?: {
    /**
     * Port to expose metrics on
     */
    port?: number;
    
    /**
     * Endpoint to expose metrics on
     */
    endpoint?: string;
  };
  
  /**
   * Whether to collect host metrics
   */
  collectHostMetrics?: boolean;
  
  /**
   * Additional metric readers
   */
  additionalReaders?: MetricReader[];
}

/**
 * Create a standardized metrics provider
 * 
 * @param config Metrics configuration
 * @returns Meter provider and optional host metrics collector
 */
export function createMetricsProvider(config: MetricsConfig) {
  const {
    serviceName,
    serviceVersion = '1.0.0',
    environment = process.env.NODE_ENV || 'development',
    resourceAttributes = {},
    prometheus = { port: 9464, endpoint: '/metrics' },
    collectHostMetrics = true,
    additionalReaders = [],
  } = config;
  
  // Create resource
  const resource = Resource.default().merge(
    new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
      [SemanticResourceAttributes.SERVICE_VERSION]: serviceVersion,
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: environment,
      ...resourceAttributes,
    })
  );
  
  // Create Prometheus exporter
  const prometheusExporter = new PrometheusExporter({
    port: prometheus.port,
    endpoint: prometheus.endpoint,
  });
  
  // Create meter provider
  const meterProvider = new MeterProvider({
    resource,
  });
  
  // Register readers
  meterProvider.addMetricReader(prometheusExporter);
  
  // Add additional readers
  for (const reader of additionalReaders) {
    meterProvider.addMetricReader(reader);
  }
  
  // Create host metrics collector
  let hostMetrics: Host | null = null;
  
  if (collectHostMetrics) {
    hostMetrics = new Host({
      meterProvider,
      name: `${serviceName}-host-metrics`,
    });
    
    // Start collecting host metrics
    hostMetrics.start();
  }
  
  // Return the meter provider and host metrics collector
  return {
    meterProvider,
    hostMetrics,
  };
}

/**
 * Express middleware for HTTP metrics
 * 
 * @param meter Meter to use for metrics
 * @returns Express middleware
 */
export function createHttpMetricsMiddleware(meter: any) {
  // Create metrics
  const httpRequestCounter = meter.createCounter('http_requests_total', {
    description: 'Total number of HTTP requests',
  });
  
  const httpRequestDuration = meter.createHistogram('http_request_duration_seconds', {
    description: 'HTTP request duration in seconds',
  });
  
  // Return middleware
  return (req: any, res: any, next: any) => {
    const start = process.hrtime();
    
    // Handle response finish
    res.on('finish', () => {
      const duration = process.hrtime(start);
      const durationSeconds = duration[0] + duration[1] / 1e9;
      
      const labels = {
        method: req.method,
        route: req.route?.path || 'unknown',
        status_code: res.statusCode,
      };
      
      // Record metrics
      httpRequestCounter.add(1, labels);
      httpRequestDuration.record(durationSeconds, labels);
    });
    
    next();
  };
}

export default { createMetricsProvider, createHttpMetricsMiddleware };