"""OpenTelemetry tracing module for AI Mesh Network.

This module provides OpenTelemetry instrumentation for the AI Mesh Network,
enabling distributed tracing across agents, memory operations, and LLM calls.
"""

import os
import time
import logging
import asyncio
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context.context import Context
from opentelemetry.trace.span import Span
from opentelemetry.trace.status import Status, StatusCode

logger = logging.getLogger("ai_service.utils.tracing")

# Environment variables
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://opentelemetry-collector:4317")
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "ai-mesh-network")
OTEL_ENVIRONMENT = os.getenv("OTEL_ENVIRONMENT", "production")
OTEL_SAMPLING_RATIO = float(os.getenv("OTEL_SAMPLING_RATIO", "1.0"))  # 1.0 = 100% sampling

class AIMeshTracingManager:
    """Manager class for AI Mesh Network OpenTelemetry tracing."""

    def __init__(self):
        """Initialize the tracing manager."""
        self._tracer_provider = None
        self._tracer = None

    def setup_tracing(self, app: FastAPI, redis_client=None):
        """Set up OpenTelemetry tracing for the AI Mesh Network.

        Args:
            app: The FastAPI application to instrument
            redis_client: Optional Redis client to instrument
        """
        try:
            # Create a resource with service information
            resource = Resource.create({
                "service.name": OTEL_SERVICE_NAME,
                "service.namespace": "maily.ai_mesh",
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

            # Instrument httpx library (standardized HTTP client)
            HTTPXInstrumentor().instrument()

            # Instrument Redis if provided
            if redis_client:
                RedisInstrumentor().instrument()

            logger.info("OpenTelemetry tracing initialized successfully for AI Mesh Network")
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry tracing for AI Mesh Network: {e}")

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
    
    def trace_memory_operation(self, operation: str):
        """Decorator for tracing memory operations.
        
        Args:
            operation: The memory operation being performed (e.g., "retrieve", "store")
            
        Returns:
            A decorator that traces the function
        """
        def decorator(func):
            async def async_wrapper(self, *args, **kwargs):
                with self._tracer.start_as_current_span(f"memory.{operation}") as span:
                    # Add attributes about the memory operation
                    span.set_attribute("memory.operation", operation)
                    if hasattr(self, "network_id"):
                        span.set_attribute("network.id", self.network_id)
                    
                    # Extract and add key attributes from args/kwargs
                    if operation == "retrieve" and len(args) > 0:
                        span.set_attribute("memory.query", str(args[0]))
                    if "memory_id" in kwargs:
                        span.set_attribute("memory.id", kwargs["memory_id"])
                    
                    try:
                        start_time = time.time()
                        result = await func(self, *args, **kwargs)
                        duration = time.time() - start_time
                        span.set_attribute("memory.operation.duration", duration)
                        
                        # Add result metadata as attributes
                        if operation == "retrieve" and isinstance(result, list):
                            span.set_attribute("memory.result.count", len(result))
                        
                        return result
                    except Exception as e:
                        self.record_exception(span, e)
                        raise
            
            def sync_wrapper(self, *args, **kwargs):
                with self._tracer.start_as_current_span(f"memory.{operation}") as span:
                    # Add attributes about the memory operation
                    span.set_attribute("memory.operation", operation)
                    if hasattr(self, "network_id"):
                        span.set_attribute("network.id", self.network_id)
                    
                    # Extract and add key attributes from args/kwargs
                    if operation == "retrieve" and len(args) > 0:
                        span.set_attribute("memory.query", str(args[0]))
                    if "memory_id" in kwargs:
                        span.set_attribute("memory.id", kwargs["memory_id"])
                    
                    try:
                        start_time = time.time()
                        result = func(self, *args, **kwargs)
                        duration = time.time() - start_time
                        span.set_attribute("memory.operation.duration", duration)
                        
                        # Add result metadata as attributes
                        if operation == "retrieve" and isinstance(result, list):
                            span.set_attribute("memory.result.count", len(result))
                        
                        return result
                    except Exception as e:
                        self.record_exception(span, e)
                        raise
            
            # Return appropriate wrapper based on whether the function is async
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def trace_agent_task(self, agent_type: str):
        """Decorator for tracing agent tasks.
        
        Args:
            agent_type: The type of agent (e.g., "content", "design")
            
        Returns:
            A decorator that traces the function
        """
        def decorator(func):
            async def async_wrapper(self, *args, **kwargs):
                with self._tracer.start_as_current_span(f"agent.{agent_type}.task") as span:
                    # Add attributes about the agent task
                    span.set_attribute("agent.type", agent_type)
                    if hasattr(self, "network_id"):
                        span.set_attribute("network.id", self.network_id)
                    if hasattr(self, "agent_id"):
                        span.set_attribute("agent.id", self.agent_id)
                    
                    # Extract task information from args/kwargs
                    if len(args) > 0 and hasattr(args[0], "task_id"):
                        span.set_attribute("task.id", args[0].task_id)
                    if "task" in kwargs and hasattr(kwargs["task"], "task_id"):
                        span.set_attribute("task.id", kwargs["task"].task_id)
                    
                    try:
                        start_time = time.time()
                        result = await func(self, *args, **kwargs)
                        duration = time.time() - start_time
                        span.set_attribute("agent.task.duration", duration)
                        
                        # Add status attribute based on result
                        if result and hasattr(result, "status"):
                            span.set_attribute("agent.task.status", result.status)
                        
                        return result
                    except Exception as e:
                        self.record_exception(span, e)
                        raise
            
            def sync_wrapper(self, *args, **kwargs):
                with self._tracer.start_as_current_span(f"agent.{agent_type}.task") as span:
                    # Add attributes about the agent task
                    span.set_attribute("agent.type", agent_type)
                    if hasattr(self, "network_id"):
                        span.set_attribute("network.id", self.network_id)
                    if hasattr(self, "agent_id"):
                        span.set_attribute("agent.id", self.agent_id)
                    
                    # Extract task information from args/kwargs
                    if len(args) > 0 and hasattr(args[0], "task_id"):
                        span.set_attribute("task.id", args[0].task_id)
                    if "task" in kwargs and hasattr(kwargs["task"], "task_id"):
                        span.set_attribute("task.id", kwargs["task"].task_id)
                    
                    try:
                        start_time = time.time()
                        result = func(self, *args, **kwargs)
                        duration = time.time() - start_time
                        span.set_attribute("agent.task.duration", duration)
                        
                        # Add status attribute based on result
                        if result and hasattr(result, "status"):
                            span.set_attribute("agent.task.status", result.status)
                        
                        return result
                    except Exception as e:
                        self.record_exception(span, e)
                        raise
            
            # Return appropriate wrapper based on whether the function is async
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def trace_llm_call(self, model: str):
        """Decorator for tracing LLM API calls.
        
        Args:
            model: The model being used (e.g., "claude-3-sonnet")
            
        Returns:
            A decorator that traces the function
        """
        def decorator(func):
            async def wrapper(self, *args, **kwargs):
                with self._tracer.start_as_current_span("llm.call") as span:
                    # Add attributes about the LLM call
                    span.set_attribute("llm.model", model)
                    span.set_attribute("llm.provider", model.split("-")[0])  # Extract provider from model name
                    
                    # Add prompt information if available
                    if len(args) > 0:
                        span.set_attribute("llm.prompt_length", len(str(args[0])))
                    if "prompt" in kwargs:
                        span.set_attribute("llm.prompt_length", len(str(kwargs["prompt"])))
                    
                    try:
                        start_time = time.time()
                        result = await func(self, *args, **kwargs)
                        duration = time.time() - start_time
                        span.set_attribute("llm.call.duration", duration)
                        
                        # Add response metadata
                        if result and hasattr(result, "content"):
                            span.set_attribute("llm.response_length", len(str(result.content)))
                        elif isinstance(result, str):
                            span.set_attribute("llm.response_length", len(result))
                        
                        # Add token information if available
                        if result and hasattr(result, "usage"):
                            span.set_attribute("llm.prompt_tokens", result.usage.prompt_tokens)
                            span.set_attribute("llm.completion_tokens", result.usage.completion_tokens)
                            span.set_attribute("llm.total_tokens", result.usage.total_tokens)
                        
                        return result
                    except Exception as e:
                        self.record_exception(span, e)
                        span.set_attribute("llm.error", str(e))
                        raise
            
            return wrapper
        
        return decorator

# Create a singleton instance
tracing_manager = AIMeshTracingManager()

# Middleware for WebSocket tracing
async def websocket_tracing_middleware(websocket: Any, call_next):
    """Middleware for WebSocket tracing.

    This middleware creates a span for each WebSocket connection and adds
    connection information as span attributes.

    Args:
        websocket: The FastAPI WebSocket connection
        call_next: The next middleware in the chain

    Returns:
        The response from the next middleware
    """
    current_span = trace.get_current_span()

    # Add WebSocket information to the span
    current_span.set_attribute("websocket.path", websocket.url.path)
    current_span.set_attribute("websocket.client", str(websocket.client))
    
    # Extract network ID if available in path parameters
    if hasattr(websocket, "path_params") and "network_id" in websocket.path_params:
        current_span.set_attribute("network.id", websocket.path_params["network_id"])

    try:
        # Add event for WebSocket connection
        current_span.add_event("websocket.connect")
        
        # Call the next middleware
        await call_next(websocket)
    except Exception as e:
        # Record exception in span
        tracing_manager.record_exception(current_span, e, handled=False)
        current_span.add_event("websocket.error", {"error": str(e)})
        raise
    finally:
        # Add event for WebSocket disconnect
        current_span.add_event("websocket.disconnect")