"""OpenTelemetry tracing module for distributed tracing.

This module provides OpenTelemetry instrumentation for the Maily API service,
enabling distributed tracing across services and components.
"""

import os
from typing import Optional
from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context.context import Context
from opentelemetry.trace.span import Span
from opentelemetry.trace.status import Status, StatusCode
import logging

logger = logging.getLogger(__name__)

# Environment variables
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://opentelemetry-collector:4317")
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "maily-api")
OTEL_ENVIRONMENT = os.getenv("OTEL_ENVIRONMENT", "production")
OTEL_SAMPLING_RATIO = float(os.getenv("OTEL_SAMPLING_RATIO", "1.0"))  # 1.0 = 100% sampling

class TracingManager:
    """Manager class for OpenTelemetry tracing."""

    def __init__(self):
        """Initialize the tracing manager."""
        self._tracer_provider = None
        self._tracer = None

    def setup_tracing(self, app: FastAPI, sqlalchemy_engine=None, redis_client=None):
        """Set up OpenTelemetry tracing for the FastAPI application.

        Args:
            app: The FastAPI application to instrument
            sqlalchemy_engine: Optional SQLAlchemy engine to instrument
            redis_client: Optional Redis client to instrument
        """
        try:
            # Create a resource with service information
            resource = Resource.create({
                "service.name": OTEL_SERVICE_NAME,
                "service.namespace": "maily",
                "deployment.environment": OTEL_ENVIRONMENT,
            })

            # Configure the tracer provider with the resource
            sampler = TraceIdRatioBased(OTEL_SAMPLING_RATIO)
            self._tracer_provider = TracerProvider(resource=resource, sampler=sampler)

            # Configure the OTLP exporter
            otlp_exporter = OTLPSpanExporter(endpoint=OTEL_EXPORTER_OTLP_ENDPOINT)

            # Add the exporter to the tracer provider
            self._tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

            # Set the tracer provider
            trace.set_tracer_provider(self._tracer_provider)

            # Get a tracer
            self._tracer = trace.get_tracer(__name__, "1.0.0")

            # Instrument FastAPI
            FastAPIInstrumentor.instrument_app(app)

            # Instrument requests library
            RequestsInstrumentor().instrument()

            # Instrument SQLAlchemy if provided
            if sqlalchemy_engine:
                SQLAlchemyInstrumentor().instrument(engine=sqlalchemy_engine)

            # Instrument Redis if provided
            if redis_client:
                RedisInstrumentor().instrument()

            logger.info("OpenTelemetry tracing initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry tracing: {e}")

    def create_span(self, name: str, context: Optional[Context] = None) -> Span:
        """Create a new span.

        Args:
            name: The name of the span
            context: Optional parent context

        Returns:
            The created span
        """
        if not self._tracer:
            logger.warning("Tracer not initialized, returning a no-op span")
            return trace.get_current_span()

        if context:
            return self._tracer.start_span(name, context=context)
        else:
            return self._tracer.start_span(name)

    def extract_context_from_headers(self, headers: dict) -> Context:
        """Extract trace context from HTTP headers.

        Args:
            headers: The HTTP headers

        Returns:
            The extracted context
        """
        return TraceContextTextMapPropagator().extract(headers)

    def inject_context_to_headers(self, headers: dict, context: Optional[Context] = None) -> dict:
        """Inject trace context into HTTP headers.

        Args:
            headers: The HTTP headers to inject into
            context: Optional context to inject, defaults to current context

        Returns:
            The headers with injected context
        """
        if not context:
            context = trace.get_current_span().get_span_context()

        TraceContextTextMapPropagator().inject(headers, context=context)
        return headers

    def record_exception(self, span: Span, exception: Exception, handled: bool = True):
        """Record an exception in a span.

        Args:
            span: The span to record the exception in
            exception: The exception to record
            handled: Whether the exception was handled
        """
        span.record_exception(exception)
        if handled:
            span.set_status(Status(StatusCode.ERROR))
        else:
            span.set_status(Status(StatusCode.ERROR, str(exception)))

    def add_span_attributes(self, span: Span, attributes: dict):
        """Add attributes to a span.

        Args:
            span: The span to add attributes to
            attributes: The attributes to add
        """
        for key, value in attributes.items():
            span.set_attribute(key, value)

    def add_span_event(self, span: Span, name: str, attributes: Optional[dict] = None):
        """Add an event to a span.

        Args:
            span: The span to add the event to
            name: The name of the event
            attributes: Optional attributes for the event
        """
        span.add_event(name, attributes=attributes)

    def shutdown(self):
        """Shutdown the tracer provider."""
        if self._tracer_provider:
            self._tracer_provider.shutdown()

# Create a singleton instance
tracing_manager = TracingManager()

# Middleware for request tracing
async def tracing_middleware(request: Request, call_next):
    """Middleware for request tracing.

    This middleware creates a span for each request and adds request information
    as span attributes.

    Args:
        request: The FastAPI request
        call_next: The next middleware in the chain

    Returns:
        The response from the next middleware
    """
    current_span = trace.get_current_span()

    # Add request information to the span
    current_span.set_attribute("http.method", request.method)
    current_span.set_attribute("http.url", str(request.url))
    current_span.set_attribute("http.host", request.headers.get("host", ""))
    current_span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
    current_span.set_attribute("http.request_id", request.headers.get("x-request-id", ""))

    try:
        response = await call_next(request)
        current_span.set_attribute("http.status_code", response.status_code)
        return response
    except Exception as e:
        tracing_manager.record_exception(current_span, e, handled=False)
        raise
