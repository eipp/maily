import pytest

from models import Campaign
from apps.api.ai import consolidated_ai_service

# No longer need to instantiate AIService
# from services.ai_service import AIService


def test_content_generation(mock_ai_service):
    """Test AI content generation."""
    # Use the consolidated service directly
    # service = AIService(ai_provider=mock_ai_service)

    # Mock the consolidated service
    consolidated_ai_service._model_adapter = mock_ai_service

    prompt = "Write a welcome email"
    tone = "Professional"

    content = consolidated_ai_service.generate_text(prompt=prompt, tone=tone)

    assert content is not None
    assert isinstance(content, str)
    assert len(content) > 0


def test_subject_line_optimization(mock_ai_service):
    """Test subject line optimization."""
    # service = AIService(ai_provider=mock_ai_service)

    # Mock the consolidated service
    consolidated_ai_service._model_adapter = mock_ai_service

    original_subject = "Welcome to our platform"

    suggestions = consolidated_ai_service.optimize_subject_line(original_subject)

    assert isinstance(suggestions, list)
    assert len(suggestions) > 0
    assert all(isinstance(s, str) for s in suggestions)


def test_campaign_performance_analysis(mock_ai_service, test_campaign):
    """Test campaign performance analysis."""
    # service = AIService(ai_provider=mock_ai_service)

    # Mock the consolidated service
    consolidated_ai_service._model_adapter = mock_ai_service

    campaign_data = {
        "opens": 100,
        "clicks": 50,
        "bounces": 5,
        "unsubscribes": 2,
        "total_sent": 200,
    }

    analysis = consolidated_ai_service.analyze_campaign_performance(campaign_data)

    assert "score" in analysis
    assert "suggestions" in analysis
    assert "insights" in analysis
    assert isinstance(analysis["score"], (int, float))
    assert isinstance(analysis["suggestions"], list)
    assert isinstance(analysis["insights"], list)


def test_audience_segmentation(mock_ai_service):
    """Test AI-powered audience segmentation."""
    # service = AIService(ai_provider=mock_ai_service)

    # Mock the consolidated service
    consolidated_ai_service._model_adapter = mock_ai_service

    user_data = [
        {
            "email": "user1@example.com",
            "engagement_score": 0.8,
            "last_active": "2024-02-20",
            "interests": ["technology", "marketing"],
        },
        {
            "email": "user2@example.com",
            "engagement_score": 0.3,
            "last_active": "2024-01-15",
            "interests": ["business", "finance"],
        },
    ]

    segments = consolidated_ai_service.segment_audience(user_data)

    assert isinstance(segments, dict)
    assert "high_engagement" in segments
    assert "low_engagement" in segments
    assert isinstance(segments["high_engagement"], list)
    assert isinstance(segments["low_engagement"], list)


def test_content_personalization(mock_ai_service):
    """Test content personalization."""
    # service = AIService(ai_provider=mock_ai_service)

    # Mock the consolidated service
    consolidated_ai_service._model_adapter = mock_ai_service

    base_content = "Welcome to our platform!"
    user_data = {
        "name": "John",
        "interests": ["technology"],
        "usage_history": ["feature_a", "feature_b"],
    }

    personalized_content = consolidated_ai_service.personalize_content(base_content, user_data)

    assert isinstance(personalized_content, str)
    assert len(personalized_content) > 0
    assert "John" in personalized_content


def test_error_handling(mock_ai_service):
    """Test error handling in AI service."""
    # service = AIService(ai_provider=mock_ai_service)

    # Mock the consolidated service
    consolidated_ai_service._model_adapter = mock_ai_service

    # Test with invalid prompt
    with pytest.raises(ValueError):
        consolidated_ai_service.generate_text(prompt="", tone="Professional")

    # Test with invalid tone
    with pytest.raises(ValueError):
        consolidated_ai_service.generate_text(prompt="Write content", tone="InvalidTone")

    # Test with invalid campaign data
    with pytest.raises(ValueError):
        consolidated_ai_service.analyze_campaign_performance({})


def test_content_validation(mock_ai_service):
    """Test content validation and safety checks."""
    # service = AIService(ai_provider=mock_ai_service)

    # Mock the consolidated service
    consolidated_ai_service._model_adapter = mock_ai_service

    unsafe_content = "SPAM! Buy now! Limited time offer!!!"

    validation_result = consolidated_ai_service.validate_content(unsafe_content)

    assert isinstance(validation_result, dict)
    assert "is_safe" in validation_result
    assert "issues" in validation_result
    assert not validation_result["is_safe"]
    assert len(validation_result["issues"]) > 0


def test_performance_prediction(mock_ai_service, test_campaign):
    """Test campaign performance prediction."""
    # service = AIService(ai_provider=mock_ai_service)

    # Mock the consolidated service
    consolidated_ai_service._model_adapter = mock_ai_service

    campaign_content = "Welcome to our platform!"
    target_audience = ["technology", "marketing"]

    prediction = consolidated_ai_service.predict_performance(campaign_content, target_audience)

    assert isinstance(prediction, dict)
    assert "estimated_open_rate" in prediction
    assert "estimated_click_rate" in prediction
    assert "confidence_score" in prediction
    assert 0 <= prediction["estimated_open_rate"] <= 1
    assert 0 <= prediction["estimated_click_rate"] <= 1
    assert 0 <= prediction["confidence_score"] <= 1
