#!/usr/bin/env python3
"""
Test script for OpenTelemetry tracing implementation.

This script tests the OpenTelemetry tracing implementation by:
1. Making requests to the API service
2. Verifying that traces are being generated and exported
3. Checking trace context propagation

Usage:
    python test-opentelemetry.py [--endpoint URL] [--collector URL]

Options:
    --endpoint URL     API endpoint to test (default: http://localhost:8000)
    --collector URL    OpenTelemetry Collector endpoint (default: http://localhost:4317)
"""

import argparse
import json
import logging
import os
import random
import sys
import time
import uuid
from datetime import datetime

import requests
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description="Test OpenTelemetry tracing implementation")
parser.add_argument(
    "--endpoint",
    default="http://localhost:8000",
    help="API endpoint to test (default: http://localhost:8000)",
)
parser.add_argument(
    "--collector",
    default="http://localhost:4317",
    help="OpenTelemetry Collector endpoint (default: http://localhost:4317)",
)
args = parser.parse_args()

# Initialize OpenTelemetry
resource = Resource.create(
    {
        "service.name": "opentelemetry-test",
        "service.namespace": "maily",
        "deployment.environment": "test",
    }
)

trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint=args.collector)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

tracer = trace.get_tracer(__name__)
propagator = TraceContextTextMapPropagator()


def make_request(url, method="GET", headers=None, data=None):
    """Make a request to the API service with trace context propagation.

    Args:
        url: The URL to request
        method: The HTTP method to use
        headers: Optional headers to include
        data: Optional data to send

    Returns:
        The response from the API service
    """
    headers = headers or {}

    # Create a span for the request
    with tracer.start_as_current_span(f"{method} {url}") as span:
        # Add some attributes to the span
        span.set_attribute("http.method", method)
        span.set_attribute("http.url", url)

        # Inject trace context into headers
        propagator.inject(headers)

        # Add request ID header
        request_id = str(uuid.uuid4())
        headers["X-Request-ID"] = request_id
        span.set_attribute("request_id", request_id)

        # Make the request
        logger.info(f"Making {method} request to {url}")
        response = requests.request(method, url, headers=headers, json=data)

        # Add response attributes to the span
        span.set_attribute("http.status_code", response.status_code)

        return response


def test_health_endpoint(base_url):
    """Test the health endpoint.

    Args:
        base_url: The base URL of the API service

    Returns:
        True if the test passed, False otherwise
    """
    url = f"{base_url}/health"

    with tracer.start_as_current_span("test_health_endpoint") as span:
        try:
            response = make_request(url)

            if response.status_code != 200:
                logger.error(f"Health endpoint returned status code {response.status_code}")
                span.set_attribute("test.status", "failed")
                return False

            data = response.json()
            logger.info(f"Health endpoint response: {data}")

            if data.get("status") not in ["healthy", "degraded"]:
                logger.error(f"Health endpoint returned unexpected status: {data.get('status')}")
                span.set_attribute("test.status", "failed")
                return False

            span.set_attribute("test.status", "passed")
            return True
        except Exception as e:
            logger.error(f"Error testing health endpoint: {e}")
            span.set_attribute("test.status", "failed")
            span.record_exception(e)
            return False


def test_create_campaign(base_url):
    """Test creating a campaign.

    Args:
        base_url: The base URL of the API service

    Returns:
        True if the test passed, False otherwise
    """
    url = f"{base_url}/create_campaign"

    with tracer.start_as_current_span("test_create_campaign") as span:
        try:
            # Create test data
            campaign_data = {
                "name": f"Test Campaign {datetime.now().isoformat()}",
                "subject": "Test Subject",
                "task": "Create a test email campaign about product updates",
                "model_name": "gpt-4",
                "audience": {
                    "segments": ["active_users"],
                    "exclusions": []
                }
            }

            # Add API key header (replace with actual API key)
            headers = {
                "X-API-Key": os.environ.get("MAILY_API_KEY", "test-api-key")
            }

            response = make_request(url, method="POST", headers=headers, data=campaign_data)

            if response.status_code != 200 and response.status_code != 201:
                logger.error(f"Create campaign endpoint returned status code {response.status_code}")
                span.set_attribute("test.status", "failed")
                return False

            data = response.json()
            logger.info(f"Create campaign response: {data}")

            if "campaign_id" not in data:
                logger.error("Create campaign response missing campaign_id")
                span.set_attribute("test.status", "failed")
                return False

            span.set_attribute("test.status", "passed")
            span.set_attribute("campaign.id", data["campaign_id"])
            return True
        except Exception as e:
            logger.error(f"Error testing create campaign endpoint: {e}")
            span.set_attribute("test.status", "failed")
            span.record_exception(e)
            return False


def test_trace_context_propagation(base_url):
    """Test trace context propagation across multiple requests.

    Args:
        base_url: The base URL of the API service

    Returns:
        True if the test passed, False otherwise
    """
    with tracer.start_as_current_span("test_trace_context_propagation") as parent_span:
        try:
            # Make a request to the health endpoint
            health_url = f"{base_url}/health"
            health_response = make_request(health_url)

            if health_response.status_code != 200:
                logger.error(f"Health endpoint returned status code {health_response.status_code}")
                parent_span.set_attribute("test.status", "failed")
                return False

            # Extract the request ID from the response headers
            request_id = health_response.headers.get("X-Request-ID")

            if not request_id:
                logger.error("Health response missing X-Request-ID header")
                parent_span.set_attribute("test.status", "failed")
                return False

            # Make another request with the same trace context
            headers = {}
            propagator.inject(headers)
            headers["X-Request-ID"] = request_id

            # Make a request to another endpoint
            second_url = f"{base_url}/health"
            second_response = requests.get(second_url, headers=headers)

            if second_response.status_code != 200:
                logger.error(f"Second request returned status code {second_response.status_code}")
                parent_span.set_attribute("test.status", "failed")
                return False

            parent_span.set_attribute("test.status", "passed")
            return True
        except Exception as e:
            logger.error(f"Error testing trace context propagation: {e}")
            parent_span.set_attribute("test.status", "failed")
            parent_span.record_exception(e)
            return False


def main():
    """Run the tests."""
    base_url = args.endpoint

    with tracer.start_as_current_span("opentelemetry_test") as root_span:
        logger.info(f"Testing OpenTelemetry tracing implementation against {base_url}")

        # Test the health endpoint
        health_result = test_health_endpoint(base_url)
        root_span.set_attribute("test.health.passed", health_result)

        # Test creating a campaign
        campaign_result = test_create_campaign(base_url)
        root_span.set_attribute("test.create_campaign.passed", campaign_result)

        # Test trace context propagation
        propagation_result = test_trace_context_propagation(base_url)
        root_span.set_attribute("test.trace_context_propagation.passed", propagation_result)

        # Overall result
        overall_result = all([health_result, campaign_result, propagation_result])
        root_span.set_attribute("test.overall.passed", overall_result)

        if overall_result:
            logger.info("All tests passed!")
        else:
            logger.error("Some tests failed")

        # Wait for spans to be exported
        logger.info("Waiting for spans to be exported...")
        time.sleep(5)

        return 0 if overall_result else 1


if __name__ == "__main__":
    sys.exit(main())
