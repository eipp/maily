/**
 * OpenTelemetry distributed tracing configuration for Maily services
 */

const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { SimpleSpanProcessor, ConsoleSpanExporter, BatchSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { JaegerExporter } = require('@opentelemetry/exporter-jaeger');
const { ZipkinExporter } = require('@opentelemetry/exporter-zipkin');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');
const { ExpressInstrumentation } = require('@opentelemetry/instrumentation-express');
const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');
const { AwsInstrumentation } = require('@opentelemetry/instrumentation-aws-sdk');
const { MongoDBInstrumentation } = require('@opentelemetry/instrumentation-mongodb');
const { PgInstrumentation } = require('@opentelemetry/instrumentation-pg');
const { RedisInstrumentation } = require('@opentelemetry/instrumentation-redis');
const { AmqplibInstrumentation } = require('@opentelemetry/instrumentation-amqplib');
const { GrpcInstrumentation } = require('@opentelemetry/instrumentation-grpc');
const { CompositePropagator, W3CTraceContextPropagator, W3CBaggagePropagator } = require('@opentelemetry/core');
const { B3Propagator } = require('@opentelemetry/propagator-b3');
const { JaegerPropagator } = require('@opentelemetry/propagator-jaeger');
const opentelemetry = require('@opentelemetry/api');

/**
 * Initialize OpenTelemetry tracing for a service
 * @param {Object} options - Configuration options
 * @param {string} options.serviceName - Name of the service 
 * @param {string} options.environment - Deployment environment (production, staging, development)
 * @param {Object} options.exporters - Exporter configuration
 * @returns {NodeTracerProvider} The configured tracer provider
 */
function initTracing({ 
  serviceName, 
  environment = process.env.NODE_ENV || 'development',
  exporters = { jaeger: true, zipkin: false, console: false }
}) {
  if (!serviceName) {
    throw new Error('serviceName is required for distributed tracing');
  }

  // Create a tracer provider with the service's resource information
  const provider = new NodeTracerProvider({
    resource: new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: environment,
      'maily.version': process.env.SERVICE_VERSION || '1.0.0',
    }),
  });

  // Configure the exporters
  if (exporters.jaeger) {
    const jaegerExporter = new JaegerExporter({
      endpoint: process.env.JAEGER_ENDPOINT || 'http://jaeger-collector.monitoring:14268/api/traces',
    });
    provider.addSpanProcessor(new BatchSpanProcessor(jaegerExporter));
  }

  if (exporters.zipkin) {
    const zipkinExporter = new ZipkinExporter({
      url: process.env.ZIPKIN_ENDPOINT || 'http://zipkin.monitoring:9411/api/v2/spans',
      serviceName,
    });
    provider.addSpanProcessor(new BatchSpanProcessor(zipkinExporter));
  }

  if (exporters.console || environment === 'development') {
    provider.addSpanProcessor(new SimpleSpanProcessor(new ConsoleSpanExporter()));
  }

  // Configure context propagation
  const propagator = new CompositePropagator({
    propagators: [
      new W3CTraceContextPropagator(),
      new W3CBaggagePropagator(),
      new B3Propagator(),
      new JaegerPropagator(),
    ],
  });

  // Register the provider and propagator
  provider.register({
    propagator,
  });

  // Register auto-instrumentations
  registerInstrumentations({
    instrumentations: [
      new HttpInstrumentation(),
      new ExpressInstrumentation({
        requestHook: (span, request) => {
          // Add additional info to spans if needed
          span.setAttribute('http.request.headers.user-agent', request.headers['user-agent']);
          if (request.user && request.user.id) {
            span.setAttribute('enduser.id', request.user.id);
          }
        },
      }),
      new AwsInstrumentation({
        suppressInternalInstrumentation: true,
      }),
      new MongoDBInstrumentation(),
      new PgInstrumentation(),
      new RedisInstrumentation(),
      new AmqplibInstrumentation(),
      new GrpcInstrumentation(),
    ],
  });

  return provider;
}

/**
 * Create a tracer for a specific component within a service
 * @param {string} name - Component name (e.g., 'email-processor', 'campaign-scheduler')
 * @returns {Tracer} OpenTelemetry tracer instance
 */
function getTracer(name) {
  return opentelemetry.trace.getTracer(name);
}

/**
 * Add current context to outgoing HTTP requests
 * @param {Object} headers - HTTP headers object to inject context into
 */
function injectTraceContext(headers) {
  const context = opentelemetry.context.active();
  opentelemetry.propagation.inject(context, headers);
}

/**
 * Extract trace context from incoming HTTP request
 * @param {Object} headers - HTTP headers object to extract context from
 * @returns {Context} OpenTelemetry context
 */
function extractTraceContext(headers) {
  return opentelemetry.propagation.extract(opentelemetry.context.active(), headers);
}

/**
 * Create a middleware for Express to ensure trace context is properly propagated
 */
function createExpressMiddleware() {
  return (req, res, next) => {
    const context = extractTraceContext(req.headers);
    
    // Add trace ID to response headers for easy debugging
    const span = opentelemetry.trace.getSpan(context);
    if (span) {
      const traceId = span.spanContext().traceId;
      res.setHeader('X-Trace-ID', traceId);
    }
    
    return opentelemetry.context.with(context, next);
  };
}

module.exports = {
  initTracing,
  getTracer,
  injectTraceContext,
  extractTraceContext,
  createExpressMiddleware,
};
