"""Integration tests for campaign workflows."""

import pytest
from fastapi.testclient import TestClient

import os
import sys

from main_fixed import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    # For our testing purposes, we'll use a simple mock token
    return {"Authorization": "Bearer mock_token_for_testing"}


@pytest.fixture
def test_campaign():
    return {
        "name": "Test Campaign",
        "subject": "Test Subject",
        "content": "Hello {{name}}, this is a test email.",
        "sender_email": "sender@example.com",
        "sender_name": "Test Sender",
    }


def test_campaign_creation_workflow(auth_headers, test_campaign):
    # 1. Create campaign
    response = client.post("/campaigns", headers=auth_headers, json=test_campaign)
    assert response.status_code == 201
    campaign_id = response.json()["id"]

    # 2. Verify campaign was created
    response = client.get(f"/campaigns/{campaign_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == test_campaign["name"]

    # 3. Update campaign
    update_data = {"name": "Updated Campaign Name"}
    response = client.patch(
        f"/campaigns/{campaign_id}", headers=auth_headers, json=update_data
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Campaign Name"

    # 4. List campaigns
    response = client.get("/campaigns", headers=auth_headers)
    assert response.status_code == 200
    campaigns = response.json()
    assert any(c["id"] == campaign_id for c in campaigns)


def test_campaign_sending_workflow(auth_headers, test_campaign):
    # 1. Create campaign
    response = client.post("/campaigns", headers=auth_headers, json=test_campaign)
    assert response.status_code == 201
    campaign_id = response.json()["id"]

    # 2. Add recipients
    recipients = [
        {"email": "recipient1@example.com", "name": "Recipient 1"},
        {"email": "recipient2@example.com", "name": "Recipient 2"},
    ]
    response = client.post(
        f"/campaigns/{campaign_id}/recipients", headers=auth_headers, json=recipients
    )
    assert response.status_code == 200

    # 3. Send test email
    test_recipient = {"email": "test@example.com", "name": "Test User"}
    response = client.post(
        f"/campaigns/{campaign_id}/test", headers=auth_headers, json=test_recipient
    )
    assert response.status_code == 200

    # 4. Schedule campaign
    schedule_data = {"send_at": "2024-12-31T12:00:00Z"}
    response = client.post(
        f"/campaigns/{campaign_id}/schedule", headers=auth_headers, json=schedule_data
    )
    assert response.status_code == 200

    # 5. Get campaign status
    response = client.get(f"/campaigns/{campaign_id}/status", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "scheduled"


def test_campaign_analytics_workflow(auth_headers, test_campaign):
    # 1. Create and send campaign
    response = client.post("/campaigns", headers=auth_headers, json=test_campaign)
    campaign_id = response.json()["id"]

    # 2. Get campaign analytics
    response = client.get(f"/campaigns/{campaign_id}/analytics", headers=auth_headers)
    assert response.status_code == 200
    analytics = response.json()
    assert "sent_count" in analytics
    assert "open_rate" in analytics
    assert "click_rate" in analytics

    # 3. Get detailed events
    response = client.get(
        f"/campaigns/{campaign_id}/events",
        headers=auth_headers,
        params={"event_type": "open"},
    )
    assert response.status_code == 200

    # 4. Export analytics
    response = client.get(f"/campaigns/{campaign_id}/export", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
