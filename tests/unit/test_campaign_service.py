from datetime import datetime, timedelta

import pytest

from models import Campaign
from services.campaign_service import CampaignService


def test_create_campaign(db_session, test_user):
    """Test campaign creation."""
    service = CampaignService(db_session)
    campaign_data = {
        "name": "New Campaign",
        "subject": "Test Subject",
        "content": "Test Content",
        "schedule_time": None,
    }

    campaign = service.create_campaign(test_user.id, campaign_data)

    assert campaign.name == "New Campaign"
    assert campaign.user_id == test_user.id
    assert campaign.status == "draft"


def test_schedule_campaign(db_session, test_campaign):
    """Test campaign scheduling."""
    service = CampaignService(db_session)
    schedule_time = datetime.utcnow() + timedelta(days=1)

    updated_campaign = service.schedule_campaign(test_campaign.id, schedule_time)

    assert updated_campaign.status == "scheduled"
    assert updated_campaign.schedule_time == schedule_time


def test_send_campaign(db_session, test_campaign, mock_email_service):
    """Test campaign sending."""
    service = CampaignService(db_session, email_service=mock_email_service)

    # Add test recipients
    recipients = ["test1@example.com", "test2@example.com"]
    result = service.send_campaign(test_campaign.id, recipients)

    assert result["status"] == "sent"
    assert len(result["sent_to"]) == 2

    # Check campaign status update
    campaign = db_session.query(Campaign).get(test_campaign.id)
    assert campaign.status == "sent"


def test_get_campaign_analytics(db_session, test_campaign, mock_email_service):
    """Test retrieving campaign analytics."""
    service = CampaignService(db_session, email_service=mock_email_service)

    analytics = service.get_campaign_analytics(test_campaign.id)

    assert "opens" in analytics
    assert "clicks" in analytics
    assert "bounces" in analytics
    assert analytics["opens"] == 10
    assert analytics["clicks"] == 5


def test_update_campaign(db_session, test_campaign):
    """Test campaign update."""
    service = CampaignService(db_session)
    updates = {"name": "Updated Campaign", "subject": "Updated Subject"}

    updated_campaign = service.update_campaign(test_campaign.id, updates)

    assert updated_campaign.name == "Updated Campaign"
    assert updated_campaign.subject == "Updated Subject"


def test_delete_campaign(db_session, test_campaign):
    """Test campaign deletion."""
    service = CampaignService(db_session)

    service.delete_campaign(test_campaign.id)

    # Verify campaign is deleted
    campaign = db_session.query(Campaign).get(test_campaign.id)
    assert campaign is None


def test_get_user_campaigns(db_session, test_user, test_campaign):
    """Test retrieving user's campaigns."""
    service = CampaignService(db_session)

    # Create additional campaign
    service.create_campaign(
        test_user.id,
        {
            "name": "Second Campaign",
            "subject": "Test Subject",
            "content": "Test Content",
        },
    )

    campaigns = service.get_user_campaigns(test_user.id)

    assert len(campaigns) == 2
    assert any(c.name == "Test Campaign" for c in campaigns)
    assert any(c.name == "Second Campaign" for c in campaigns)


def test_campaign_validation(db_session, test_user):
    """Test campaign validation."""
    service = CampaignService(db_session)

    # Test invalid data
    with pytest.raises(ValueError):
        service.create_campaign(
            test_user.id,
            {
                "name": "",  # Empty name should fail
                "subject": "Test Subject",
                "content": "Test Content",
            },
        )

    with pytest.raises(ValueError):
        service.create_campaign(
            test_user.id,
            {
                "name": "Test Campaign",
                "subject": "Test Subject",
                "content": "",  # Empty content should fail
            },
        )


def test_campaign_scheduling_validation(db_session, test_campaign):
    """Test campaign scheduling validation."""
    service = CampaignService(db_session)

    # Test scheduling in the past
    past_time = datetime.utcnow() - timedelta(days=1)
    with pytest.raises(ValueError):
        service.schedule_campaign(test_campaign.id, past_time)

    # Test scheduling sent campaign
    test_campaign.status = "sent"
    db_session.commit()

    future_time = datetime.utcnow() + timedelta(days=1)
    with pytest.raises(ValueError):
        service.schedule_campaign(test_campaign.id, future_time)
