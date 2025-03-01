"""
Tests for the ContentGenerationAdapter using the mock AI framework.
Demonstrates how to effectively test AI-dependent components.
"""
import pytest
from unittest.mock import patch
import json

from apps.api.ai.adapters.base import ModelRequest, ModelResponse
from tests.unit.ai.mock_ai_adapter import MockModelAdapter, AITestFactory


# Sample adapter class we'll be testing
class ContentGenerationAdapter:
    """Adapter for AI-powered content generation."""

    def __init__(self, ai_provider):
        self.ai_provider = ai_provider

    async def generate_subject_line(self, params):
        """Generate an email subject line based on provided parameters."""
        prompt = f"""
        Generate a compelling subject line for an email with the following parameters:
        - product: {params.get('product', '')}
        - audience: {params.get('audience', '')}
        - tone: {params.get('tone', 'neutral')}

        Make it concise, engaging, and optimized for good open rates.
        """

        request = ModelRequest(
            prompt=prompt,
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=50
        )

        try:
            response = await self.ai_provider.generate(request)
            # Return just the content string, trimmed of whitespace
            return response.content.strip()
        except Exception as e:
            # Log error and return a fallback subject
            print(f"Error generating subject line: {str(e)}")
            return "Update from " + params.get('product', 'us')

    async def generate_email_content(self, params):
        """Generate complete email content based on provided parameters."""
        prompt = f"""
        Generate email content for {params.get('purpose', 'marketing')} with:
        - product: {params.get('product', '')}
        - audience: {params.get('audience', '')}
        - tone: {params.get('tone', 'neutral')}
        - key_points: {json.dumps(params.get('key_points', []))}

        Include a header, body paragraphs, and call-to-action.
        """

        request = ModelRequest(
            prompt=prompt,
            model_name="gpt-4o",
            temperature=0.8,
            max_tokens=800
        )

        try:
            response = await self.ai_provider.generate(request)
            return {
                "content": response.content.strip(),
                "tokens_used": response.usage.get("total_tokens", 0),
                "model": response.model_name
            }
        except Exception as e:
            # Log error and return an error result
            print(f"Error generating email content: {str(e)}")
            return {
                "error": str(e),
                "content": None,
                "tokens_used": 0
            }


# Tests for ContentGenerationAdapter
@pytest.mark.asyncio
class TestContentGenerationAdapter:

    @pytest.fixture
    def mock_provider(self):
        """Create and configure a mock AI provider for testing."""
        mock = MockModelAdapter()
        return mock

    @pytest.fixture
    def adapter(self, mock_provider):
        """Create a ContentGenerationAdapter with the mock provider."""
        return ContentGenerationAdapter(mock_provider)

    async def test_generate_subject_line(self, mock_provider, adapter):
        """Test generating an email subject line."""
        # Configure mock response
        mock_provider.mock_response(
            prompt_pattern="Generate a compelling subject line",
            response=ModelResponse(
                content="Exciting New Features for You",
                model_name="gpt-4o",
                usage={"prompt_tokens": 120, "completion_tokens": 6, "total_tokens": 126}
            )
        )

        # Call adapter
        result = await adapter.generate_subject_line({
            "product": "Maily",
            "audience": "marketers",
            "tone": "professional"
        })

        # Assertions
        assert result == "Exciting New Features for You"

        # Verify correct prompt was sent
        calls = mock_provider.get_calls()
        assert len(calls) == 1
        assert "product: Maily" in calls[0].prompt
        assert "audience: marketers" in calls[0].prompt
        assert "tone: professional" in calls[0].prompt

    async def test_generate_email_content(self, mock_provider, adapter):
        """Test generating complete email content."""
        # Configure mock response
        mock_content = """
        # Welcome to Our Maily Update!

        Dear valued customer,

        We're excited to share our latest features with you...

        ## Key Updates:
        - Enhanced analytics dashboard
        - New email templates

        Try these features today!
        """

        mock_provider.mock_response(
            prompt_pattern="Generate email content",
            response=ModelResponse(
                content=mock_content,
                model_name="gpt-4o",
                usage={"prompt_tokens": 150, "completion_tokens": 80, "total_tokens": 230}
            )
        )

        # Call adapter
        result = await adapter.generate_email_content({
            "product": "Maily",
            "audience": "existing users",
            "tone": "friendly",
            "purpose": "product update",
            "key_points": ["New dashboard", "Email templates"]
        })

        # Assertions
        assert result["content"] == mock_content.strip()
        assert result["tokens_used"] == 230
        assert result["model"] == "gpt-4o"

        # Verify correct prompt was sent
        calls = mock_provider.get_calls()
        assert len(calls) == 1
        assert "purpose: product update" in calls[0].prompt
        assert "key_points" in calls[0].prompt

    async def test_handle_ai_provider_errors(self, mock_provider, adapter):
        """Test that provider errors are handled gracefully."""
        # Configure mock to raise an error
        mock_provider.mock_error(
            prompt_pattern="Generate a compelling subject line",
            error=Exception("API rate limit exceeded")
        )

        # Call adapter - should handle the error and return fallback
        result = await adapter.generate_subject_line({
            "product": "Maily",
            "audience": "developers"
        })

        # Should return the fallback subject
        assert result == "Update from Maily"

    async def test_with_test_factory(self):
        """Test using the AITestFactory for quick mock setup."""
        # Use the test factory to create a pre-configured mock
        mock_provider = AITestFactory.create_default_mock()

        # Create adapter with this mock
        adapter = ContentGenerationAdapter(mock_provider)

        # Call adapter - will use the default mock response
        result = await adapter.generate_subject_line({
            "product": "Maily"
        })

        # Should return the default mock content
        assert result == "This is a default mock response"

    async def test_with_failing_test_factory(self):
        """Test using the failing mock setup from factory."""
        # Use the test factory to create a pre-configured failing mock
        mock_provider = AITestFactory.create_failing_mock()

        # Create adapter with this mock
        adapter = ContentGenerationAdapter(mock_provider)

        # Call adapter - should handle the error gracefully
        result = await adapter.generate_subject_line({
            "product": "Maily"
        })

        # Should return the fallback subject
        assert result == "Update from Maily"
