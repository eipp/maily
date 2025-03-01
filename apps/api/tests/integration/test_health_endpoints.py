"""Integration tests for health endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main_fixed import app

@pytest.fixture
def test_client():
    """Create a test client for the app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_campaign_service():
    """Mock campaign service for health checks."""
    mock = MagicMock()
    # Configure default healthy responses
    mock.check_db_health.return_value = True
    return mock

@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter for health checks."""
    mock = MagicMock()
    # Configure default healthy responses
    mock.check_redis_health.return_value = True
    return mock

@pytest.fixture
def mock_ai_service():
    """Mock AI service for health checks."""
    mock = MagicMock()
    # Configure default healthy responses
    mock.check_health.return_value = True
    return mock


# Health check tests
def test_health_endpoint_healthy(test_client, monkeypatch,
                                mock_campaign_service,
                                mock_rate_limiter,
                                mock_ai_service):
    """Test the health endpoint with all components healthy."""
    # Apply the mocks
    monkeypatch.setattr('main_fixed.campaign_service', mock_campaign_service)
    monkeypatch.setattr('main_fixed.rate_limiter', mock_rate_limiter)
    monkeypatch.setattr('main_fixed.ai_service', mock_ai_service)

    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["components"]["database"] == "connected"
    assert data["components"]["redis"] == "connected"
    assert data["components"]["ai_service"] == "operational"
    assert "uptime" in data
    assert "services" in data
    assert "timestamp" in data


def test_health_endpoint_degraded_db(test_client, monkeypatch,
                                    mock_campaign_service,
                                    mock_rate_limiter,
                                    mock_ai_service):
    """Test the health endpoint with database unhealthy."""
    # Configure database failure
    mock_campaign_service.check_db_health.return_value = False

    # Apply the mocks
    monkeypatch.setattr('main_fixed.campaign_service', mock_campaign_service)
    monkeypatch.setattr('main_fixed.rate_limiter', mock_rate_limiter)
    monkeypatch.setattr('main_fixed.ai_service', mock_ai_service)

    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["components"]["database"] == "disconnected"
    assert data["components"]["redis"] == "connected"
    assert data["components"]["ai_service"] == "operational"


def test_health_endpoint_degraded_redis(test_client, monkeypatch,
                                        mock_campaign_service,
                                        mock_rate_limiter,
                                        mock_ai_service):
    """Test the health endpoint with Redis unhealthy."""
    # Configure Redis failure
    mock_rate_limiter.check_redis_health.return_value = False

    # Apply the mocks
    monkeypatch.setattr('main_fixed.campaign_service', mock_campaign_service)
    monkeypatch.setattr('main_fixed.rate_limiter', mock_rate_limiter)
    monkeypatch.setattr('main_fixed.ai_service', mock_ai_service)

    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["components"]["database"] == "connected"
    assert data["components"]["redis"] == "disconnected"
    assert data["components"]["ai_service"] == "operational"


def test_health_endpoint_degraded_ai(test_client, monkeypatch,
                                    mock_campaign_service,
                                    mock_rate_limiter,
                                    mock_ai_service):
    """Test the health endpoint with AI service unhealthy."""
    # Configure AI service failure
    mock_ai_service.check_health.return_value = False

    # Apply the mocks
    monkeypatch.setattr('main_fixed.campaign_service', mock_campaign_service)
    monkeypatch.setattr('main_fixed.rate_limiter', mock_rate_limiter)
    monkeypatch.setattr('main_fixed.ai_service', mock_ai_service)

    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["components"]["database"] == "connected"
    assert data["components"]["redis"] == "connected"
    assert data["components"]["ai_service"] == "unavailable"


def test_health_endpoint_all_unhealthy(test_client, monkeypatch,
                                      mock_campaign_service,
                                      mock_rate_limiter,
                                      mock_ai_service):
    """Test the health endpoint with all components unhealthy."""
    # Configure all services to be unhealthy
    mock_campaign_service.check_db_health.return_value = False
    mock_rate_limiter.check_redis_health.return_value = False
    mock_ai_service.check_health.return_value = False

    # Apply the mocks
    monkeypatch.setattr('main_fixed.campaign_service', mock_campaign_service)
    monkeypatch.setattr('main_fixed.rate_limiter', mock_rate_limiter)
    monkeypatch.setattr('main_fixed.ai_service', mock_ai_service)

    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["components"]["database"] == "disconnected"
    assert data["components"]["redis"] == "disconnected"
    assert data["components"]["ai_service"] == "unavailable"


def test_health_endpoint_exception(test_client, monkeypatch,
                                  mock_campaign_service,
                                  mock_rate_limiter,
                                  mock_ai_service):
    """Test the health endpoint when an exception occurs."""
    # Configure an exception
    mock_campaign_service.check_db_health.side_effect = Exception("Test exception")

    # Apply the mocks
    monkeypatch.setattr('main_fixed.campaign_service', mock_campaign_service)
    monkeypatch.setattr('main_fixed.rate_limiter', mock_rate_limiter)
    monkeypatch.setattr('main_fixed.ai_service', mock_ai_service)

    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert "error" in data


# Readiness tests
def test_readiness_endpoint_ready(test_client, monkeypatch,
                                mock_campaign_service,
                                mock_rate_limiter):
    """Test the readiness endpoint when system is ready."""
    # Apply the mocks
    monkeypatch.setattr('main_fixed.campaign_service', mock_campaign_service)
    monkeypatch.setattr('main_fixed.rate_limiter', mock_rate_limiter)

    response = test_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"]["status"] == "healthy"
    assert data["checks"]["redis"]["status"] == "healthy"
    assert "timestamp" in data


def test_readiness_endpoint_not_ready_db(test_client, monkeypatch,
                                       mock_campaign_service,
                                       mock_rate_limiter):
    """Test the readiness endpoint when database is not ready."""
    # Configure database not ready
    mock_campaign_service.check_db_health.return_value = False

    # Apply the mocks
    monkeypatch.setattr('main_fixed.campaign_service', mock_campaign_service)
    monkeypatch.setattr('main_fixed.rate_limiter', mock_rate_limiter)

    response = test_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["database"]["status"] == "unhealthy"
    assert data["checks"]["redis"]["status"] == "healthy"


def test_readiness_endpoint_not_ready_redis(test_client, monkeypatch,
                                          mock_campaign_service,
                                          mock_rate_limiter):
    """Test the readiness endpoint when Redis is not ready."""
    # Configure Redis not ready
    mock_rate_limiter.check_redis_health.return_value = False

    # Apply the mocks
    monkeypatch.setattr('main_fixed.campaign_service', mock_campaign_service)
    monkeypatch.setattr('main_fixed.rate_limiter', mock_rate_limiter)

    response = test_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["database"]["status"] == "healthy"
    assert data["checks"]["redis"]["status"] == "unhealthy"


def test_readiness_endpoint_not_ready_all(test_client, monkeypatch,
                                        mock_campaign_service,
                                        mock_rate_limiter):
    """Test the readiness endpoint when all systems are not ready."""
    # Configure all systems not ready
    mock_campaign_service.check_db_health.return_value = False
    mock_rate_limiter.check_redis_health.return_value = False

    # Apply the mocks
    monkeypatch.setattr('main_fixed.campaign_service', mock_campaign_service)
    monkeypatch.setattr('main_fixed.rate_limiter', mock_rate_limiter)

    response = test_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["database"]["status"] == "unhealthy"
    assert data["checks"]["redis"]["status"] == "unhealthy"


# Liveness tests
def test_liveness_endpoint(test_client):
    """Test the liveness endpoint."""
    response = test_client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "uptime" in data
    assert "timestamp" in data
