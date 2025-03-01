"""
Integration tests for service interactions between key services.
Tests the complete workflow and interactions between services.
"""
import pytest
from unittest.mock import patch, MagicMock
import asyncio
import time

from apps.api.services.campaign_service import CampaignService
from apps.api.services.email_service import EmailService
from apps.api.services.cross_platform_analytics import CrossPlatformAnalytics


@pytest.fixture
async def setup_test_services():
    """Setup test database and services"""
    # Mock dependencies
    db_mock = MagicMock()
    provider_mock = MagicMock()

    # Initialize services with mocked dependencies
    email_service = EmailService(db=db_mock, email_provider=provider_mock)
    campaign_service = CampaignService(db=db_mock, email_service=email_service)
    analytics_service = CrossPlatformAnalytics(db=db_mock)

    # Return services for use in tests
    yield {
        "email_service": email_service,
        "campaign_service": campaign_service,
        "analytics_service": analytics_service,
        "db": db_mock,
    }

    # Cleanup (if needed)
    await asyncio.sleep(0)  # Ensure any pending tasks complete


@pytest.mark.asyncio
async def test_track_email_events_in_analytics_when_campaign_sent(setup_test_services):
    """Test that email events are tracked in analytics when campaign is sent"""
    services = setup_test_services
    campaign_service = services["campaign_service"]
    analytics_service = services["analytics_service"]
    db = services["db"]

    # Setup mocks
    campaign_id = "test-campaign-123"
    db.get_campaign.return_value = {
        "id": campaign_id,
        "name": "Test Campaign",
        "subject": "Test Subject",
        "content": "<p>Test content</p>",
        "recipients": ["test@example.com"],
        "status": "draft"
    }

    # Send campaign
    await campaign_service.send_campaign(campaign_id)

    # Allow time for event processing
    await asyncio.sleep(0.1)

    # Verify analytics data
    analytics = await analytics_service.get_campaign_analytics(campaign_id)

    # Assert analytics were updated
    assert analytics is not None
    assert analytics.get("sent", 0) > 0
    assert analytics.get("delivered", 0) > 0

    # Verify campaign status was updated
    db.update_campaign.assert_called()
    campaign_update_args = db.update_campaign.call_args[0]
    assert campaign_id in campaign_update_args
    assert "status" in campaign_update_args[1]
    assert campaign_update_args[1]["status"] == "sent"


@pytest.mark.asyncio
async def test_update_campaign_status_when_all_emails_sent(setup_test_services):
    """Test that campaign status is updated when all emails are sent"""
    services = setup_test_services
    campaign_service = services["campaign_service"]
    email_service = services["email_service"]
    db = services["db"]

    # Setup test data
    campaign_id = "test-campaign-456"
    recipients = ["user1@example.com", "user2@example.com"]

    db.get_campaign.return_value = {
        "id": campaign_id,
        "name": "Test Campaign",
        "subject": "Test Subject",
        "content": "<p>Test content</p>",
        "recipients": recipients,
        "status": "draft"
    }

    # Mock successful email sending
    email_service.send_email.return_value = {"status": "sent", "message_id": "test-msg-id"}

    # Send campaign
    await campaign_service.send_campaign(campaign_id)

    # Verify campaign status was updated to sent
    db.update_campaign.assert_called()
    campaign_update_args = db.update_campaign.call_args[0]
    assert campaign_id in campaign_update_args
    assert campaign_update_args[1]["status"] == "sent"

    # Verify email was sent to all recipients
    assert email_service.send_email.call_count == len(recipients)


@pytest.mark.asyncio
async def test_handle_provider_failures_gracefully(setup_test_services):
    """Test that provider failures are handled gracefully"""
    services = setup_test_services
    campaign_service = services["campaign_service"]
    email_service = services["email_service"]
    db = services["db"]

    # Setup test data
    campaign_id = "test-campaign-789"
    recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]

    db.get_campaign.return_value = {
        "id": campaign_id,
        "name": "Test Campaign",
        "subject": "Test Subject",
        "content": "<p>Test content</p>",
        "recipients": recipients,
        "status": "draft"
    }

    # Simulate provider failure for the second recipient
    def send_email_side_effect(to, subject, content, **kwargs):
        if to == "user2@example.com":
            raise Exception("Provider error")
        return {"status": "sent", "message_id": f"test-msg-id-{to}"}

    email_service.send_email.side_effect = send_email_side_effect

    # Send campaign
    await campaign_service.send_campaign(campaign_id)

    # Verify campaign status was updated to partially_sent
    db.update_campaign.assert_called()
    campaign_update_args = db.update_campaign.call_args[0]
    assert campaign_id in campaign_update_args
    assert campaign_update_args[1]["status"] == "partially_sent"

    # Verify error was tracked
    analytics_args = db.track_campaign_error.call_args[0]
    assert campaign_id in analytics_args
    assert "Provider error" in str(analytics_args[1])
