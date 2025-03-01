"""
Distributed Tracing Module for Maily Application

This module implements distributed tracing functionality using OpenTelemetry, allowing
the tracking of request flows across services. Key features include:

1. Service and request context propagation
2. Automatic instrumentation of FastAPI, SQLAlchemy, Redis and HTTP clients
3. Span enrichment with custom attributes
4. Sampling configuration based on environment
5. Export to Jaeger, Zipkin or OTLP collectors
6. Integration with logging for correlation
7. Custom span processors for advanced use cases
"""

import os
import logging
from functools import wraps
from typing import Optional, Dict, Any, Callable, List, Union
from contextvars import ContextVar

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context.context import Context
from opentelemetry.trace.span import Span
from opentelemetry.trace.status import Status, StatusCode

# Instrumentation modules
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Exporters (choose based on environment)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter

# Configure logger
logger = logging.getLogger(__name__)

# Environment configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "maily-api")
ENV = os.getenv("ENVIRONMENT", "development")
TRACE_SAMPLE_RATE = float(os.getenv("TRACE_SAMPLE_RATE", "1.0"))  # 1.0 = 100%

# Tracing backend configuration
TRACING_BACKEND = os.getenv("TRACING_BACKEND", "jaeger")  # jaeger, zipkin, otlp, console
JAEGER_AGENT_HOST = os.getenv("JAEGER_AGENT_HOST", "localhost")
JAEGER_AGENT_PORT = int(os.getenv("JAEGER_AGENT_PORT", "6831"))
ZIPKIN_ENDPOINT = os.getenv("ZIPKIN_ENDPOINT", "http://localhost:9411/api/v2/spans")
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "localhost:4317")

# Context for accessing the current span within middleware
current_span_var: ContextVar[Optional[Span]] = ContextVar("current_span", default=None)


class MailyTracerProvider:
    """
    Singleton class to manage OpenTelemetry tracing configuration
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MailyTracerProvider, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._tracer = None
        self._trace_provider = None
        self._setup_tracing()

    def _setup_tracing(self):
        """Configure the tracing system based on environment settings"""
        # Configure resource attributes
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: SERVICE_NAME,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: ENV,
            "service.version": os.getenv("SERVICE_VERSION", "unknown"),
        })

        # Configure sampling based on environment
        if ENV == "production":
            # Use parent-based sampling with configured rate
            sampler = sampling.ParentBased(
                root=sampling.TraceIdRatioBased(TRACE_SAMPLE_RATE)
            )
        else:
            # In dev/staging environments, sample everything
            sampler = sampling.AlwaysOnSampler()

        # Create trace provider with resource and sampler
        self._trace_provider = TracerProvider(
            resource=resource,
            sampler=sampler,
        )

        # Register span processors based on configured backend
        if TRACING_BACKEND == "jaeger":
            # Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=JAEGER_AGENT_HOST,
                agent_port=JAEGER_AGENT_PORT,
            )
            self._trace_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
            logger.info(f"Jaeger exporter configured at {JAEGER_AGENT_HOST}:{JAEGER_AGENT_PORT}")

        elif TRACING_BACKEND == "zipkin":
            # Zipkin exporter
            zipkin_exporter = ZipkinExporter(
                endpoint=ZIPKIN_ENDPOINT,
                service_name=SERVICE_NAME,
            )
            self._trace_provider.add_span_processor(
                BatchSpanProcessor(zipkin_exporter)
            )
            logger.info(f"Zipkin exporter configured at {ZIPKIN_ENDPOINT}")

        elif TRACING_BACKEND == "otlp":
            # OTLP exporter (for platforms like Grafana Tempo, Honeycomb, etc.)
            otlp_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT)
            self._trace_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
            logger.info(f"OTLP exporter configured at {OTLP_ENDPOINT}")

        else:
            # Console exporter (default)
            console_exporter = ConsoleSpanExporter()
            self._trace_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
            logger.info("Console exporter configured")

        # Set global trace provider
        trace.set_tracer_provider(self._trace_provider)

        # Get a tracer instance
        self._tracer = trace.get_tracer(SERVICE_NAME)

        logger.info(f"Tracing initialized for service {SERVICE_NAME} in {ENV} environment")

    @property
    def tracer(self):
        """Get the configured tracer"""
        return self._tracer

    @property
    def trace_provider(self):
        """Get the trace provider"""
        return self._trace_provider


class TracingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for distributed tracing across services.
    Extracts trace context from incoming requests and adds custom attributes to spans.
    """
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.tracer_provider = MailyTracerProvider()
        self.tracer = self.tracer_provider.tracer
        self.propagator = TraceContextTextMapPropagator()

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract context from request headers
        carrier = dict(request.headers)
        context = self.propagator.extract(carrier=carrier)

        # Start a new span under the extracted context
        with self.tracer.start_as_current_span(
            name=f"{request.method} {request.url.path}",
            context=context,
            kind=trace.SpanKind.SERVER,
        ) as span:
            # Store span in context var for access elsewhere
            current_span_var.set(span)

            # Add request attributes to span
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.scheme", request.url.scheme)
            span.set_attribute("http.host", request.url.hostname)
            span.set_attribute("http.path", request.url.path)
            span.set_attribute("http.client_ip", request.client.host if request.client else None)

            # Extract user and request information where possible
            try:
                headers = dict(request.headers)
                if "authorization" in headers:
                    auth_header = headers["authorization"]
                    if auth_header.startswith("Bearer "):
                        span.set_attribute("auth.token_present", True)
                        # Note: We don't store the actual token for security reasons

                if "user-agent" in headers:
                    span.set_attribute("http.user_agent", headers["user-agent"])

                if "x-request-id" in headers:
                    span.set_attribute("request.id", headers["x-request-id"])

                # Add query parameters (excluding sensitive data)
                query_params = dict(request.query_params)
                for key, value in query_params.items():
                    if not _is_sensitive_param(key):
                        span.set_attribute(f"http.query.{key}", value)

            except Exception as e:
                logger.warning(f"Error extracting request information for tracing: {e}")

            try:
                # Process the request
                response = await call_next(request)

                # Add response attributes
                span.set_attribute("http.status_code", response.status_code)

                if response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR))
                    span.set_attribute("error", True)
                    if response.status_code >= 500:
                        span.set_attribute("server.error", True)
                    else:
                        span.set_attribute("client.error", True)
                else:
                    span.set_status(Status(StatusCode.OK))

                return response

            except Exception as exc:
                # Record exception in the span
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                span.set_attribute("error", True)
                span.set_attribute("server.error", True)
                raise
            finally:
                # Clear the context var
                current_span_var.set(None)


def _is_sensitive_param(param: str) -> bool:
    """
    Check if a parameter name might contain sensitive information

    Args:
        param: Parameter name to check

    Returns:
        True if the parameter might contain sensitive data
    """
    sensitive_keywords = {
        "password", "token", "secret", "key", "auth",
        "credential", "private", "ssn", "account",
        "card", "cvv", "social", "tax", "credit"
    }

    param_lower = param.lower()
    return any(keyword in param_lower for keyword in sensitive_keywords)


def get_current_span() -> Optional[Span]:
    """
    Get the current span from context

    Returns:
        Current span or None if not in a span context
    """
    return current_span_var.get()


def trace_function(name: Optional[str] = None, kind: trace.SpanKind = trace.SpanKind.INTERNAL,
                  attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace a function execution

    Args:
        name: Optional custom span name, defaults to function name
        kind: Span kind (default: INTERNAL)
        attributes: Initial attributes to set on the span

    Returns:
        Decorator function
    """
    def decorator(func):
        span_name = name if name is not None else func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = MailyTracerProvider().tracer
            with tracer.start_as_current_span(span_name, kind=kind) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = MailyTracerProvider().tracer
            with tracer.start_as_current_span(span_name, kind=kind) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def setup_tracing(app: FastAPI,
                  db_engine=None,
                  redis_client=None,
                  enable_logging_integration=True):
    """
    Set up tracing for a FastAPI application

    Args:
        app: FastAPI application
        db_engine: Optional SQLAlchemy engine to instrument
        redis_client: Optional Redis client to instrument
        enable_logging_integration: Whether to integrate with logging

    Returns:
        The instrumented application
    """
    # Initialize tracing provider
    tracer_provider = MailyTracerProvider()

    # Add custom middleware
    app.add_middleware(TracingMiddleware)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Instrument requests and httpx
    RequestsInstrumentor().instrument()
    HTTPXInstrumentor().instrument()

    # Instrument SQLAlchemy if provided
    if db_engine:
        SQLAlchemyInstrumentor().instrument(
            engine=db_engine,
            service=SERVICE_NAME
        )

    # Instrument Redis if provided
    if redis_client:
        RedisInstrumentor().instrument(client=redis_client)

    # Integrate with logging system
    if enable_logging_integration:
        LoggingInstrumentor().instrument(
            set_logging_format=True,
            log_level=logging.INFO,
        )

    # Register shutdown handler
    @app.on_event("shutdown")
    async def shutdown_tracing():
        tracer_provider.trace_provider.shutdown()

    logger.info("Tracing setup complete")
    return app


# Utility functions for working with spans
def add_span_attribute(key: str, value: Any):
    """
    Add an attribute to the current span

    Args:
        key: Attribute key
        value: Attribute value
    """
    span = get_current_span()
    if span:
        span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Add an event to the current span

    Args:
        name: Event name
        attributes: Event attributes
    """
    span = get_current_span()
    if span:
        span.add_event(name, attributes)


def set_span_status(status: StatusCode, description: Optional[str] = None):
    """
    Set the status of the current span

    Args:
        status: Status code
        description: Optional description
    """
    span = get_current_span()
    if span:
        span.set_status(Status(status, description))


def record_span_exception(exception: Exception, escaped: bool = False):
    """
    Record an exception in the current span

    Args:
        exception: Exception to record
        escaped: Whether the exception was escaped/handled
    """
    span = get_current_span()
    if span:
        span.record_exception(exception, escaped=escaped)


# Import at the end to avoid circular imports
import asyncio
