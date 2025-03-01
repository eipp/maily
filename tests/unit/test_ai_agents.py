from unittest.mock import Mock, patch

import pytest

from backend.ai.agents import (  # Update this import based on your actual implementation
    ContentAgent,
)


@pytest.fixture
def mock_ai_client():
    return Mock()


@pytest.fixture
def content_agent(mock_ai_client):
    return ContentAgent(ai_client=mock_ai_client)


def test_content_agent_generate(content_agent, mock_ai_client):
    # Arrange
    mock_ai_client.generate.return_value = "Generated email content"
    input_data = {
        "topic": "Welcome Email",
        "tone": "friendly",
        "target_audience": "new users",
    }

    # Act
    result = content_agent.generate(input_data)

    # Assert
    assert result == "Generated email content"
    mock_ai_client.generate.assert_called_once()


def test_content_agent_personalize(content_agent, mock_ai_client):
    # Arrange
    mock_ai_client.personalize.return_value = "Personalized content"
    content = "Hello {name}"
    user_data = {"name": "John"}

    # Act
    result = content_agent.personalize(content, user_data)

    # Assert
    assert result == "Personalized content"
    mock_ai_client.personalize.assert_called_once()


@pytest.mark.asyncio
async def test_content_agent_async_generate(content_agent, mock_ai_client):
    # Arrange
    mock_ai_client.generate_async.return_value = "Async generated content"
    input_data = {
        "topic": "Newsletter",
        "tone": "professional",
        "target_audience": "existing customers",
    }

    # Act
    result = await content_agent.generate_async(input_data)

    # Assert
    assert result == "Async generated content"
    mock_ai_client.generate_async.assert_called_once()
