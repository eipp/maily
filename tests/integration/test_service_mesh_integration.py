import pytest
import requests
import time
import os
import json
from urllib.parse import urljoin

# Set the base URLs for each service
API_BASE_URL = os.environ.get("API_URL", "http://api-service:8000")
EMAIL_BASE_URL = os.environ.get("EMAIL_URL", "http://email-service:3000")
AI_BASE_URL = os.environ.get("AI_URL", "http://ai-service:5000")

# Test decorator to mark these as integration tests for the service mesh
pytestmark = pytest.mark.service_mesh


@pytest.fixture(scope="module")
def auth_token():
    """Get an authentication token for API requests"""
    auth_response = requests.post(
        urljoin(API_BASE_URL, "/auth/token"),
        json={"username": "test@example.com", "password": "test-password"},
    )
    auth_response.raise_for_status()
    token_data = auth_response.json()
    return token_data["access_token"]


def test_api_health_check():
    """Verify API service is healthy"""
    response = requests.get(urljoin(API_BASE_URL, "/health"))
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # Verify Istio sidecar injection by checking headers
    assert "x-envoy-upstream-service-time" in response.headers


def test_email_service_health_check():
    """Verify Email service is healthy"""
    response = requests.get(urljoin(EMAIL_BASE_URL, "/health"))
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # Verify Istio sidecar injection by checking headers
    assert "x-envoy-upstream-service-time" in response.headers


def test_ai_service_health_check():
    """Verify AI service is healthy"""
    response = requests.get(urljoin(AI_BASE_URL, "/health"))
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # Verify Istio sidecar injection by checking headers
    assert "x-envoy-upstream-service-time" in response.headers


def test_service_to_service_communication(auth_token):
    """Test service-to-service communication through service mesh"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # API service will communicate with email service to get templates
    response = requests.get(
        urljoin(API_BASE_URL, "/templates"),
        headers=headers
    )
    assert response.status_code == 200
    templates = response.json()
    assert len(templates) > 0


def test_ai_service_integration(auth_token):
    """Test API to AI service communication through service mesh"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Generate text using the AI service (via API service)
    response = requests.post(
        urljoin(API_BASE_URL, "/ai/generate"),
        headers=headers,
        json={"prompt": "Write a welcome email", "max_tokens": 50}
    )
    assert response.status_code == 200
    result = response.json()
    assert "text" in result
    assert len(result["text"]) > 0


def test_circuit_breaker_functionality():
    """Test circuit breaker functionality in the service mesh"""
    # Create a payload that will trigger a slow response
    payload = {"delay": 2000}  # 2 seconds delay
    
    # Send multiple concurrent requests to trigger circuit breaker
    concurrent_requests = 10
    responses = []
    
    # Send requests in parallel
    for _ in range(concurrent_requests):
        response = requests.post(
            urljoin(API_BASE_URL, "/test/delay"),
            json=payload,
            timeout=5
        )
        responses.append(response)
    
    # Check if circuit breaker was triggered (at least one request should fail)
    status_codes = [r.status_code for r in responses]
    assert 503 in status_codes, "Circuit breaker was not triggered"


def test_retry_policy():
    """Test retry policy in the service mesh"""
    # Endpoint that randomly fails 50% of the time
    start_time = time.time()
    response = requests.get(urljoin(API_BASE_URL, "/test/flaky"))
    end_time = time.time()
    
    # Request should eventually succeed due to retries
    assert response.status_code == 200
    
    # Check if the time taken indicates retries occurred
    time_taken = end_time - start_time
    assert time_taken > 0.2, "Request succeeded too quickly, retries may not be working"


def test_mutual_tls():
    """Verify mutual TLS is enabled in the service mesh"""
    response = requests.get(urljoin(API_BASE_URL, "/health"))
    
    # Check for mTLS specific headers
    assert "strict-transport-security" in response.headers
    
    # Get details about the connection from the debug endpoint
    debug_response = requests.get(urljoin(API_BASE_URL, "/debug/connection"))
    assert debug_response.status_code == 200
    debug_info = debug_response.json()
    
    # Verify that the connection used mTLS
    assert debug_info["tls"] == "mutual_tls"


def test_canary_deployment_routing():
    """Test canary deployment routing if enabled"""
    # This test assumes there's a canary deployment with version header routing
    VERSIONS = {"stable": 0, "canary": 0}
    
    # Make multiple requests with version header
    for _ in range(50):
        response = requests.get(
            urljoin(API_BASE_URL, "/debug/version"),
            headers={"x-accept-version": "canary"}
        )
        assert response.status_code == 200
        version = response.json().get("version")
        if version in VERSIONS:
            VERSIONS[version] += 1
    
    # Verify both versions received traffic with canary getting some percentage
    assert VERSIONS["stable"] > 0
    assert VERSIONS["canary"] > 0
    
    # Verify without the header, we only get stable version
    for _ in range(10):
        response = requests.get(urljoin(API_BASE_URL, "/debug/version"))
        assert response.status_code == 200
        assert response.json().get("version") == "stable"


def test_timeout_functionality():
    """Test timeout configuration in the service mesh"""
    # Request a delay longer than the configured timeout
    response = requests.post(
        urljoin(API_BASE_URL, "/test/delay"),
        json={"delay": 10000},  # 10 seconds delay
        timeout=7  # local timeout longer than service mesh timeout
    )
    
    # Expect a 504 Gateway Timeout from Istio
    assert response.status_code == 504


def test_traffic_routing_between_services():
    """Test that traffic is properly routed between services"""
    response = requests.get(urljoin(API_BASE_URL, "/routes"))
    assert response.status_code == 200
    routes = response.json()
    
    # Verify that all expected services are in the routes
    services = set()
    for route in routes:
        services.add(route["service"])
    
    assert "api-service" in services
    assert "email-service" in services
    assert "ai-service" in services