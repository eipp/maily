import pytest
from unittest.mock import patch, MagicMock
from services.ai import ContentAgent, AgentError

@pytest.fixture
def mock_llm():
    mock = MagicMock()
    mock.generate.return_value = {
        "choices": [{
            "message": {
                "content": "Test response",
                "role": "assistant"
            }
        }]
    }
    return mock

@pytest.fixture
def content_agent(mock_llm):
    return ContentAgent(llm=mock_llm)

def test_content_agent_initialization():
    with patch('services.ai.get_llm') as mock_get_llm:
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        agent = ContentAgent()
        assert agent.llm == mock_llm

def test_generate_email_campaign(content_agent):
    campaign_input = {
        "target_audience": "Software developers",
        "product_description": "AI email marketing tool",
        "tone": "Professional",
        "key_points": ["Easy to use", "AI-powered"]
    }

    result = content_agent.generate_email_campaign(campaign_input)

    assert "subject" in result
    assert "body" in result
    assert "preview_text" in result
    assert content_agent.llm.generate.called

def test_generate_email_campaign_error(content_agent):
    content_agent.llm.generate.side_effect = Exception("LLM error")

    with pytest.raises(AgentError):
        content_agent.generate_email_campaign({})

def test_personalize_content(content_agent):
    template = "Hello {name}, welcome to {company}!"
    variables = {
        "name": "John",
        "company": "Maily"
    }

    result = content_agent.personalize_content(template, variables)
    assert result == "Hello John, welcome to Maily!"

def test_analyze_campaign_performance(content_agent):
    metrics = {
        "open_rate": 0.25,
        "click_rate": 0.1,
        "conversion_rate": 0.05
    }

    analysis = content_agent.analyze_campaign_performance(metrics)

    assert content_agent.llm.generate.called
    assert isinstance(analysis, dict)
    assert "recommendations" in analysis

def test_optimize_subject_line(content_agent):
    original_subject = "Check out our new features"
    metrics = {
        "open_rate": 0.15,
        "similar_campaigns": [
            {"subject": "Discover our latest updates", "open_rate": 0.25}
        ]
    }

    optimized = content_agent.optimize_subject_line(original_subject, metrics)

    assert content_agent.llm.generate.called
    assert isinstance(optimized, str)
    assert optimized != original_subject

def test_validate_content(content_agent):
    content = {
        "subject": "Special offer!!!",
        "body": "Click here to claim your prize! Limited time offer!"
    }

    validation = content_agent.validate_content(content)

    assert content_agent.llm.generate.called
    assert isinstance(validation, dict)
    assert "spam_score" in validation
    assert "suggestions" in validation
