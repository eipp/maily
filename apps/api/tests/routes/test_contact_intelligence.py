"""
Contact Intelligence API Integration Tests
-----------------------------------------

This file contains integration tests for the Contact Intelligence API endpoints.

As the solo founder, you can use these tests to verify that the Contact Intelligence
system is functioning correctly after making changes. The AI agents will use these tests
as a reference for understanding expected behavior and validating their implementations.

How to run these tests:
----------------------
From the project root directory:
    pytest apps/api/tests/routes/test_contact_intelligence.py -v

To run a specific test:
    pytest apps/api/tests/routes/test_contact_intelligence.py::test_get_contacts -v

Test Maintenance Guidelines:
---------------------------
1. Each test function has a clear purpose testing one API endpoint
2. When adding new features, add the corresponding test before or alongside the implementation
3. Tests use a TestClient to make requests to the FastAPI application
4. Tests assert both the response status code and the structure of the response data
5. Keep tests focused on validating the API contract, not implementation details
"""

import pytest
from fastapi.testclient import TestClient
from ...main import app

# Test client
client = TestClient(app)

def test_get_contacts():
    """Test getting contacts with filtering"""
    response = client.get("/api/contacts")
    assert response.status_code == 200
    data = response.json()
    assert "contacts" in data
    assert isinstance(data["contacts"], list)
    assert len(data["contacts"]) > 0

def test_get_contact_health():
    """Test getting contact health metrics"""
    response = client.get("/api/contacts/test-id/health")
    assert response.status_code == 200
    data = response.json()
    assert "health_scores" in data
    assert data["health_scores"]["overall"] >= 0
    assert data["health_scores"]["overall"] <= 100
    assert "email_validity" in data["health_scores"]
    assert "engagement" in data["health_scores"]
    assert "deliverability" in data["health_scores"]

def test_validate_contact():
    """Test contact validation"""
    response = client.post("/api/contacts/test-id/validate")
    assert response.status_code == 200
    data = response.json()
    assert "validation_results" in data
    assert "email_syntax" in data["validation_results"]
    assert "domain_reputation" in data["validation_results"]
    assert "smtp_validation" in data["validation_results"]
    assert "cross_platform" in data["validation_results"]
    assert "behavioral_patterns" in data["validation_results"]
    assert "network_validation" in data["validation_results"]
    assert "overall_validity" in data["validation_results"]
    assert "confidence_score" in data["validation_results"]

def test_get_contact_lifecycle():
    """Test getting contact lifecycle metrics"""
    response = client.get("/api/contacts/test-id/lifecycle")
    assert response.status_code == 200
    data = response.json()
    assert "lifecycle_metrics" in data
    assert "current_health_score" in data["lifecycle_metrics"]
    assert "predicted_health_trend" in data["lifecycle_metrics"]
    assert "self_healing_actions" in data["lifecycle_metrics"]
    assert "recommended_actions" in data["lifecycle_metrics"]

def test_get_blockchain_verifications():
    """Test getting blockchain verifications"""
    response = client.get("/api/contacts/test-id/blockchain-verifications")
    assert response.status_code == 200
    data = response.json()
    assert "verifications" in data
    assert isinstance(data["verifications"], list)

def test_get_compliance_data():
    """Test getting compliance data"""
    response = client.get("/api/contacts/test-id/compliance")
    assert response.status_code == 200
    data = response.json()
    assert "compliance_checks" in data
    assert isinstance(data["compliance_checks"], list)

def test_clean_contact_list():
    """Test cleaning contact list"""
    response = client.post(
        "/api/contacts/clean-list",
        json={"user_id": "test-user"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "success"
