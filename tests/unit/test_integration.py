"""Integration tests for the email generation system."""

import re
from typing import Any, Dict

import pytest

from backend.ai.adapters import ModelFactory
from backend.ai.agents import EmailAgent
from backend.ai.monitoring import AIMonitoring


def test_email_agent_initialization(mock_env, mock_monitoring):
    """Test email agent initialization with different models."""
    models = ["r1-1776", "gpt-4", "gemini-pro", "claude-3-opus"]

    for model_name in models:
        agent = EmailAgent(model_name=model_name)
        assert agent.llm is not None
        assert agent.content_agent is not None
        assert agent.user_proxy is not None


def test_subject_generation(mock_env, mock_monitoring, test_prompts):
    """Test email subject generation workflow."""
    models = ["r1-1776", "gpt-4", "gemini-pro", "claude-3-opus"]
    context = {
        "purpose": "Product launch",
        "audience": "Enterprise customers",
        "message": "New AI features",
        "tone": "Professional",
    }

    for model_name in models:
        agent = EmailAgent(model_name=model_name)
        subject = agent.generate_subject(context)

        # Verify subject
        assert subject is not None
        assert isinstance(subject, str)
        assert len(subject) > 0

        # Check if subject matches expected patterns
        patterns = test_prompts["email_subject"]["patterns"]
        assert any(re.search(pattern, subject, re.IGNORECASE) for pattern in patterns)


def test_body_generation(mock_env, mock_monitoring, test_prompts):
    """Test email body generation workflow."""
    models = ["r1-1776", "gpt-4", "gemini-pro", "claude-3-opus"]
    context = {
        "subject": "Introducing AI-Powered Email Generation",
        "purpose": "Product launch",
        "audience": "Enterprise customers",
        "message": "New AI features",
        "tone": "Professional",
        "cta": "Schedule demo",
    }

    for model_name in models:
        agent = EmailAgent(model_name=model_name)
        body = agent.generate_body(context)

        # Verify body
        assert body is not None
        assert isinstance(body, str)
        assert len(body) > 0

        # Check if body matches expected patterns
        patterns = test_prompts["email_body"]["patterns"]
        assert any(re.search(pattern, body, re.IGNORECASE) for pattern in patterns)


def test_full_email_generation(mock_env, mock_monitoring):
    """Test complete email generation workflow."""
    agent = EmailAgent(model_name="gpt-4")  # Use any model

    # Generate subject
    context = {
        "purpose": "Product launch",
        "audience": "Enterprise customers",
        "message": "New AI features",
        "tone": "Professional",
    }

    subject = agent.generate_subject(context)
    assert subject is not None

    # Update context with subject
    context["subject"] = subject
    context["cta"] = "Schedule demo"

    # Generate body
    body = agent.generate_body(context)
    assert body is not None

    # Verify email structure
    assert re.search(r"Dear|Hello|Hi", body, re.IGNORECASE)
    assert re.search(r"Best|Regards|Sincerely", body, re.IGNORECASE)
    assert context["cta"].lower() in body.lower()


def test_error_handling(mock_env, mock_monitoring):
    """Test error handling in the email generation workflow."""
    agent = EmailAgent(model_name="gpt-4")  # Use any model

    # Test with empty context
    empty_context = {}
    subject = agent.generate_subject(empty_context)
    body = agent.generate_body(empty_context)
    assert subject is not None  # Should handle missing fields gracefully
    assert body is not None

    # Test with invalid fields
    invalid_context = {
        "purpose": None,
        "audience": "",
        "message": " ",
        "tone": 123,  # Wrong type
    }
    subject = agent.generate_subject(invalid_context)
    body = agent.generate_body(invalid_context)
    assert subject is not None  # Should handle invalid fields gracefully
    assert body is not None


def test_model_switching(mock_env, mock_monitoring):
    """Test dynamic model switching."""
    context = {
        "purpose": "Product launch",
        "audience": "Enterprise customers",
        "message": "New AI features",
        "tone": "Professional",
    }

    # Generate with different models
    results = {}
    for model_name in ["r1-1776", "gpt-4", "gemini-pro", "claude-3-opus"]:
        agent = EmailAgent(model_name=model_name)
        subject = agent.generate_subject(context)
        results[model_name] = subject

    # Verify all models generated unique content
    subjects = list(results.values())
    assert len(subjects) == len(set(subjects))  # All subjects should be unique


def test_concurrent_generation(mock_env, mock_monitoring):
    """Test concurrent email generation."""
    import concurrent.futures

    def generate_email(model_name: str) -> Dict[str, str]:
        agent = EmailAgent(model_name=model_name)
        context = {
            "purpose": "Product launch",
            "audience": "Enterprise customers",
            "message": "New AI features",
            "tone": "Professional",
        }

        subject = agent.generate_subject(context)
        context["subject"] = subject
        context["cta"] = "Schedule demo"
        body = agent.generate_body(context)

        return {"subject": subject, "body": body}

    models = ["r1-1776", "gpt-4", "gemini-pro", "claude-3-opus"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(models)) as executor:
        future_to_model = {
            executor.submit(generate_email, model): model for model in models
        }

        results = {}
        for future in concurrent.futures.as_completed(future_to_model):
            model = future_to_model[future]
            try:
                results[model] = future.result()
            except Exception as e:
                results[model] = {"error": str(e)}

    # Verify results
    assert len(results) == len(models)
    for model, result in results.items():
        assert "subject" in result
        assert "body" in result
