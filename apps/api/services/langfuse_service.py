"""Langfuse integration for OctoTools.

This module provides Langfuse integration for OctoTools, allowing for
monitoring and tracking of AI operations.
"""

import os
import time
from typing import Dict, Any, List, Optional

from cryptography.fernet import Fernet
from loguru import logger
from octotools import Planner, Executor

from ..ai.config import OCTOTOOLS_CONFIG
from .database import get_db_connection

# Initialize encryption
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)


class OctoToolsLangfuseTracer:
    """Langfuse tracer for OctoTools operations."""

    def __init__(self, langfuse_client, user_id: int):
        """Initialize the Langfuse tracer.

        Args:
            langfuse_client: Langfuse client
            user_id: User ID
        """
        self.langfuse = langfuse_client
        self.user_id = user_id
        self.active_traces = {}

    def start_trace(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace.

        Args:
            operation_name: Name of the operation
            metadata: Optional metadata

        Returns:
            Trace ID
        """
        if not self.langfuse:
            return f"trace_{time.time()}"

        metadata = metadata or {}
        metadata["user_id"] = self.user_id

        trace = self.langfuse.trace(
            name=operation_name,
            metadata=metadata
        )

        trace_id = trace.id
        self.active_traces[trace_id] = trace

        return trace_id

    def start_span(self, trace_id: str, span_name: str, input_data: Optional[Dict[str, Any]] = None) -> str:
        """Start a new span within a trace.

        Args:
            trace_id: Trace ID
            span_name: Name of the span
            input_data: Optional input data

        Returns:
            Span ID
        """
        if not self.langfuse or trace_id not in self.active_traces:
            return f"span_{time.time()}"

        trace = self.active_traces[trace_id]
        span = trace.span(
            name=span_name,
            input=input_data
        )

        return span.id

    def end_span(self, trace_id: str, span_id: str, output: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
        """End a span.

        Args:
            trace_id: Trace ID
            span_id: Span ID
            output: Optional output data
            error: Optional error message
        """
        if not self.langfuse or trace_id not in self.active_traces:
            return

        # In a real implementation, you would store spans as well
        # For simplicity, we're just ending the span directly
        if error:
            self.langfuse.update_span(span_id, output=output, error=error)
        else:
            self.langfuse.update_span(span_id, output=output)

    def end_trace(self, trace_id: str, output: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
        """End a trace.

        Args:
            trace_id: Trace ID
            output: Optional output data
            error: Optional error message
        """
        if not self.langfuse or trace_id not in self.active_traces:
            return

        trace = self.active_traces[trace_id]

        if error:
            trace.update(output=output, error=error)
        else:
            trace.update(output=output)

        del self.active_traces[trace_id]


class OctoToolsLangfuseWrapper:
    """Wrapper for OctoTools with Langfuse integration."""

    def __init__(self, langfuse_client, user_id: int):
        """Initialize the OctoTools Langfuse wrapper.

        Args:
            langfuse_client: Langfuse client
            user_id: User ID
        """
        self.tracer = OctoToolsLangfuseTracer(langfuse_client, user_id)
        self.user_id = user_id
        self._model_config = None

    @property
    def model_config(self) -> Dict[str, Any]:
        """Get the model configuration for the user.

        Returns:
            Model configuration
        """
        if self._model_config is None:
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "SELECT provider, model_name, api_key FROM user_configs WHERE user_id = %s",
                    (self.user_id,),
                )
                results = cur.fetchall()
                cur.close()
                conn.close()

                config = {}

                for provider, model_name, encrypted_key in results:
                    api_key = cipher_suite.decrypt(encrypted_key.encode()).decode()
                    config[provider] = {
                        "model": model_name,
                        "api_key": api_key
                    }

                    # Set environment variable for the current session
                    os.environ[f"{provider.upper()}_API_KEY"] = api_key

                if not config:
                    # Use default configuration
                    config = {
                        "openai": {
                            "model": OCTOTOOLS_CONFIG["model"]["planner"],
                            "api_key": OCTOTOOLS_CONFIG["api_keys"]["openai"]
                        }
                    }

                self._model_config = config

            except Exception as e:
                logger.error(f"Failed to get model configuration: {e}")
                # Use default configuration
                self._model_config = {
                    "openai": {
                        "model": OCTOTOOLS_CONFIG["model"]["planner"],
                        "api_key": OCTOTOOLS_CONFIG["api_keys"]["openai"]
                    }
                }

        return self._model_config

    def create_planner(self) -> Planner:
        """Create a planner with the user's configuration.

        Returns:
            Configured Planner
        """
        config = self.model_config.get("openai", {})
        model_name = config.get("model", OCTOTOOLS_CONFIG["model"]["planner"])

        return Planner(
            model_name=model_name,
            max_steps=OCTOTOOLS_CONFIG["model"]["max_steps"],
            timeout=OCTOTOOLS_CONFIG["model"]["timeout"]
        )

    def create_executor(self) -> Executor:
        """Create an executor with the user's configuration.

        Returns:
            Configured Executor
        """
        config = self.model_config.get("openai", {})
        model_name = config.get("model", OCTOTOOLS_CONFIG["model"]["executor"])

        return Executor(
            model_name=model_name
        )

    async def execute_with_tracing(
        self,
        planner: Planner,
        executor: Executor,
        query: str,
        toolbox: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a query with tracing.

        Args:
            planner: OctoTools planner
            executor: OctoTools executor
            query: Query to execute
            toolbox: OctoTools toolbox
            context: Optional context

        Returns:
            Execution result
        """
        trace_id = self.tracer.start_trace("octotools_execution", {
            "query": query,
            "context": context
        })

        try:
            # Start planning span
            planning_span = self.tracer.start_span(trace_id, "planning", {
                "query": query,
                "context": context
            })

            # Execute the query
            result = await planner.execute(
                query=query,
                toolbox=toolbox,
                executor=executor,
                context=context
            )

            # End planning span
            self.tracer.end_span(trace_id, planning_span, {
                "result": result
            })

            # End trace
            self.tracer.end_trace(trace_id, {
                "result": result
            })

            return result
        except Exception as e:
            logger.error(f"Execution failed: {str(e)}")
            self.tracer.end_trace(trace_id, error=str(e))
            raise
