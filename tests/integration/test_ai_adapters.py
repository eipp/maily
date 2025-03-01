import unittest
import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
import json

# Import the adapter components
from apps.api.ai.adapters import (
    OpenAIAdapter,
    AnthropicAdapter,
    GoogleAIAdapter,
    model_adapter_factory
)
from apps.api.ai.adapters.base import ModelRequest, ModelResponse


class TestModelAdapterFactory(unittest.TestCase):
    """Integration tests for the model adapter factory."""

    def test_register_and_get_adapter(self):
        """Test registering and getting an adapter."""
        # Create a mock adapter class
        mock_adapter_class = MagicMock()

        # Register the adapter
        model_adapter_factory.register_adapter("test-adapter", mock_adapter_class)

        # Get the adapter
        adapter = model_adapter_factory.get_adapter("test-adapter")

        # Verify the adapter is an instance of the mock class
        self.assertIsInstance(adapter, mock_adapter_class)

    def test_get_available_adapters(self):
        """Test getting available adapters."""
        # Register a test adapter
        mock_adapter_class = MagicMock()
        model_adapter_factory.register_adapter("test-adapter-2", mock_adapter_class)

        # Get available adapters
        adapters = model_adapter_factory.get_available_adapters()

        # Verify the test adapter is in the list
        self.assertIn("test-adapter-2", adapters)

    def test_get_nonexistent_adapter(self):
        """Test getting a nonexistent adapter."""
        # Try to get a nonexistent adapter
        with self.assertRaises(ValueError):
            model_adapter_factory.get_adapter("nonexistent-adapter")


@pytest.mark.integration
class TestOpenAIAdapter(unittest.TestCase):
    """Integration tests for the OpenAI adapter."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the OpenAI client
        self.openai_patcher = patch('apps.api.ai.adapters.openai_adapter.openai')
        self.mock_openai = self.openai_patcher.start()

        # Configure the mock OpenAI client
        self.mock_completion = AsyncMock()
        self.mock_openai.AsyncOpenAI.return_value.chat.completions.create = self.mock_completion

        # Create an OpenAI adapter
        self.adapter = OpenAIAdapter(api_key="test-openai-key")

    def tearDown(self):
        """Tear down test fixtures."""
        self.openai_patcher.stop()

    @pytest.mark.asyncio
    async def test_generate_text(self):
        """Test generating text with the OpenAI adapter."""
        # Configure the mock completion to return a response
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"
        mock_choice.finish_reason = "stop"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        self.mock_completion.return_value = mock_response

        # Create a request
        request = ModelRequest(
            prompt="Test prompt",
            model="gpt-4",
            max_tokens=100,
            temperature=0.7
        )

        # Call the method
        response = await self.adapter.generate_text(request)

        # Verify the response
        self.assertEqual(response.content, "Test response")
        self.assertEqual(response.model, "gpt-4")
        self.assertEqual(response.usage["total_tokens"], 30)
        self.assertEqual(response.finish_reason, "stop")

        # Verify the OpenAI client was called correctly
        self.mock_completion.assert_called_once()
        call_kwargs = self.mock_completion.call_args[1]
        self.assertEqual(call_kwargs["model"], "gpt-4")
        self.assertEqual(call_kwargs["max_tokens"], 100)
        self.assertEqual(call_kwargs["temperature"], 0.7)

    @pytest.mark.asyncio
    async def test_generate_text_with_error(self):
        """Test generating text with an error."""
        # Configure the mock completion to raise an exception
        self.mock_completion.side_effect = Exception("Test error")

        # Create a request
        request = ModelRequest(
            prompt="Test prompt",
            model="gpt-4",
            max_tokens=100,
            temperature=0.7
        )

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await self.adapter.generate_text(request)


@pytest.mark.integration
class TestAnthropicAdapter(unittest.TestCase):
    """Integration tests for the Anthropic adapter."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the Anthropic client
        self.anthropic_patcher = patch('apps.api.ai.adapters.anthropic_adapter.anthropic')
        self.mock_anthropic = self.anthropic_patcher.start()

        # Configure the mock Anthropic client
        self.mock_completion = AsyncMock()
        self.mock_anthropic.AsyncAnthropic.return_value.messages.create = self.mock_completion

        # Create an Anthropic adapter
        self.adapter = AnthropicAdapter(api_key="test-anthropic-key")

    def tearDown(self):
        """Tear down test fixtures."""
        self.anthropic_patcher.stop()

    @pytest.mark.asyncio
    async def test_generate_text(self):
        """Test generating text with the Anthropic adapter."""
        # Configure the mock completion to return a response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_response.model = "claude-3-opus"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.stop_reason = "stop_sequence"

        self.mock_completion.return_value = mock_response

        # Create a request
        request = ModelRequest(
            prompt="Test prompt",
            model="claude-3-opus",
            max_tokens=100,
            temperature=0.7
        )

        # Call the method
        response = await self.adapter.generate_text(request)

        # Verify the response
        self.assertEqual(response.content, "Test response")
        self.assertEqual(response.model, "claude-3-opus")
        self.assertEqual(response.usage["prompt_tokens"], 10)
        self.assertEqual(response.usage["completion_tokens"], 20)
        self.assertEqual(response.usage["total_tokens"], 30)
        self.assertEqual(response.finish_reason, "stop_sequence")

        # Verify the Anthropic client was called correctly
        self.mock_completion.assert_called_once()
        call_kwargs = self.mock_completion.call_args[1]
        self.assertEqual(call_kwargs["model"], "claude-3-opus")
        self.assertEqual(call_kwargs["max_tokens"], 100)
        self.assertEqual(call_kwargs["temperature"], 0.7)


@pytest.mark.integration
class TestGoogleAIAdapter(unittest.TestCase):
    """Integration tests for the Google AI adapter."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the Google AI client
        self.google_patcher = patch('apps.api.ai.adapters.google_adapter.genai')
        self.mock_genai = self.google_patcher.start()

        # Configure the mock Google AI client
        self.mock_model = MagicMock()
        self.mock_genai.GenerativeModel.return_value = self.mock_model

        # Mock the generate_content method
        self.mock_generate = AsyncMock()
        self.mock_model.generate_content_async = self.mock_generate

        # Create a Google AI adapter
        self.adapter = GoogleAIAdapter(api_key="test-google-key")

    def tearDown(self):
        """Tear down test fixtures."""
        self.google_patcher.stop()

    @pytest.mark.asyncio
    async def test_generate_text(self):
        """Test generating text with the Google AI adapter."""
        # Configure the mock generate to return a response
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].finish_reason = "STOP"
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20
        mock_response.usage_metadata.total_token_count = 30

        self.mock_generate.return_value = mock_response

        # Create a request
        request = ModelRequest(
            prompt="Test prompt",
            model="gemini-1.5-pro",
            max_tokens=100,
            temperature=0.7
        )

        # Call the method
        response = await self.adapter.generate_text(request)

        # Verify the response
        self.assertEqual(response.content, "Test response")
        self.assertEqual(response.model, "gemini-1.5-pro")
        self.assertEqual(response.usage["prompt_tokens"], 10)
        self.assertEqual(response.usage["completion_tokens"], 20)
        self.assertEqual(response.usage["total_tokens"], 30)
        self.assertEqual(response.finish_reason, "STOP")

        # Verify the Google AI client was called correctly
        self.mock_genai.GenerativeModel.assert_called_once_with(
            "gemini-1.5-pro",
            generation_config=self.mock_genai.GenerationConfig.return_value,
            safety_settings=self.mock_genai.HarmCategory.return_value
        )
        self.mock_generate.assert_called_once()
