#!/usr/bin/env python3
"""
Tests for the adapter implementation.

These tests verify that the adapter implementation correctly handles:
1. Authentication with both API key and Bearer token
2. Data conversion between fixed and router formats
3. Endpoint routing between implementations
4. Response standardization
"""

import os
import sys
import pytest
import json
from fastapi.testclient import TestClient

# Import test configuration
from adapter_test_config import (
    test_client,
    fixed_auth_headers,
    router_auth_headers,
    fixed_campaign_data,
    router_campaign_data
)

class TestAdapterAuthentication:
    """Test authentication compatibility."""

    def test_fixed_auth_with_api_key(self, test_client, fixed_auth_headers):
        """Test authentication with API key."""
        response = test_client.get("/health", headers=fixed_auth_headers)
        assert response.status_code == 200

    def test_router_auth_with_bearer_token(self, test_client, router_auth_headers):
        """Test authentication with Bearer token."""
        response = test_client.get("/health", headers=router_auth_headers)
        assert response.status_code == 200

    def test_missing_auth(self, test_client):
        """Test authentication failure with missing auth."""
        response = test_client.get("/api/v1/campaigns")
        assert response.status_code == 401

    def test_invalid_api_key(self, test_client):
        """Test authentication failure with invalid API key."""
        response = test_client.get("/api/v1/campaigns", headers={"X-API-Key": "invalid-key"})
        assert response.status_code == 401

    def test_invalid_bearer_token(self, test_client):
        """Test authentication failure with invalid Bearer token."""
        response = test_client.get("/api/v1/campaigns", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401

class TestDataFormatCompatibility:
    """Test data format compatibility."""

    def test_fixed_format_create_campaign(self, test_client, fixed_auth_headers, fixed_campaign_data):
        """Test campaign creation with fixed format data."""
        response = test_client.post(
            "/api/v1/campaigns",
            headers=fixed_auth_headers,
            json=fixed_campaign_data
        )
        assert response.status_code == 201
        data = response.json()

        # Check standardized response format
        assert "data" in data
        assert "status" in data
        assert data["status"] == "success"

        # Check campaign data
        campaign = data["data"]
        assert "id" in campaign  # Standardized field name
        assert "status" in campaign
        assert campaign["status"] == "DRAFT"  # Uppercase status

    def test_router_format_create_campaign(self, test_client, router_auth_headers, router_campaign_data):
        """Test campaign creation with router format data."""
        response = test_client.post(
            "/api/v1/campaigns",
            headers=router_auth_headers,
            json=router_campaign_data
        )
        assert response.status_code == 201
        data = response.json()

        # Check standardized response format
        assert "data" in data
        assert "status" in data
        assert data["status"] == "success"

        # Check campaign data
        campaign = data["data"]
        assert "id" in campaign  # Standardized field name
        assert "name" in campaign
        assert campaign["name"] == router_campaign_data["name"]
        assert "status" in campaign
        assert campaign["status"] == "DRAFT"  # Uppercase status

class TestEndpointCompatibility:
    """Test endpoint compatibility."""

    def test_fixed_endpoint_compatibility(self, test_client, fixed_auth_headers, fixed_campaign_data):
        """Test fixed endpoint compatibility."""
        # Test legacy endpoint
        response = test_client.post(
            "/create_campaign",
            headers=fixed_auth_headers,
            json=fixed_campaign_data
        )
        assert response.status_code == 201

    def test_router_endpoint_compatibility(self, test_client, router_auth_headers, router_campaign_data):
        """Test router endpoint compatibility."""
        # Test standardized endpoint with router auth
        response = test_client.post(
            "/api/v1/campaigns",
            headers=router_auth_headers,
            json=router_campaign_data
        )
        assert response.status_code == 201

class TestResponseStandardization:
    """Test response standardization."""

    def test_standardized_success_response(self, test_client, fixed_auth_headers):
        """Test standardized success response format."""
        response = test_client.get("/health", headers=fixed_auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Check standardized response format
        assert "status" in data
        assert data["status"] == "success" or data["status"] == "healthy"

    def test_standardized_error_response(self, test_client):
        """Test standardized error response format."""
        response = test_client.get("/api/v1/campaigns")  # Missing auth
        assert response.status_code == 401
        data = response.json()

        # Check standardized error response
        assert "status" in data
        assert data["status"] == "error"
        assert "error" in data

class TestCompleteCampaignWorkflow:
    """Test complete campaign workflow with both implementations."""

    def test_fixed_implementation_workflow(self, test_client, fixed_auth_headers, fixed_campaign_data):
        """Test complete workflow using fixed implementation."""
        # 1. Create campaign
        create_response = test_client.post(
            "/api/v1/campaigns",
            headers=fixed_auth_headers,
            json=fixed_campaign_data
        )
        assert create_response.status_code == 201
        campaign_id = create_response.json()["data"]["id"]

        # 2. Get campaign details
        get_response = test_client.get(
            f"/api/v1/campaigns/{campaign_id}",
            headers=fixed_auth_headers
        )
        assert get_response.status_code == 200

        # 3. Update campaign
        update_response = test_client.put(
            f"/api/v1/campaigns/{campaign_id}",
            headers=fixed_auth_headers,
            json={"name": "Updated Campaign"}
        )
        assert update_response.status_code == 200

        # 4. Send campaign
        send_response = test_client.post(
            f"/api/v1/campaigns/{campaign_id}/send",
            headers=fixed_auth_headers
        )
        assert send_response.status_code == 200

        # 5. Get campaign analytics
        analytics_response = test_client.get(
            f"/api/v1/campaigns/{campaign_id}/analytics",
            headers=fixed_auth_headers
        )
        assert analytics_response.status_code == 200

    def test_router_implementation_workflow(self, test_client, router_auth_headers, router_campaign_data):
        """Test complete workflow using router implementation."""
        # 1. Create campaign
        create_response = test_client.post(
            "/api/v1/campaigns",
            headers=router_auth_headers,
            json=router_campaign_data
        )
        assert create_response.status_code == 201
        campaign_id = create_response.json()["data"]["id"]

        # 2. Get campaign details
        get_response = test_client.get(
            f"/api/v1/campaigns/{campaign_id}",
            headers=router_auth_headers
        )
        assert get_response.status_code == 200

        # 3. Update campaign
        update_response = test_client.put(
            f"/api/v1/campaigns/{campaign_id}",
            headers=router_auth_headers,
            json={"name": "Updated Campaign"}
        )
        assert update_response.status_code == 200

        # 4. Send campaign
        send_response = test_client.post(
            f"/api/v1/campaigns/{campaign_id}/send",
            headers=router_auth_headers
        )
        assert send_response.status_code == 200

        # 5. Get campaign analytics
        analytics_response = test_client.get(
            f"/api/v1/campaigns/{campaign_id}/analytics",
            headers=router_auth_headers
        )
        assert analytics_response.status_code == 200
