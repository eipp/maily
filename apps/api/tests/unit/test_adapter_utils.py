"""
Unit tests for adapter utilities.
"""
import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any

from apps.api.ai.adapters.adapter_utils import (
    AdapterInitializer,
    ResponseIteratorFactory,
    CommonModelHelpers
)
from apps.api.ai.adapters.base import ModelResponse


class TestAdapterInitializer:
    """Tests for AdapterInitializer class."""

    def test_initialize_client_with_provided_key(self):
        """Test client initialization with provided API key."""
        mock_client_class = MagicMock()
        api_key = "test_api_key"

        client = AdapterInitializer.initialize_client(
            provider_name="Test",
            api_key_var="TEST_API_KEY",
            client_class=mock_client_class,
            api_key=api_key
        )

        mock_client_class.assert_called_once_with(api_key=api_key)
        assert client == mock_client_class.return_value

    def test_initialize_client_with_env_var(self, monkeypatch):
        """Test client initialization with environment variable."""
        mock_client_class = MagicMock()
        api_key = "env_api_key"
        monkeypatch.setenv("TEST_API_KEY", api_key)

        client = AdapterInitializer.initialize_client(
            provider_name="Test",
            api_key_var="TEST_API_KEY",
            client_class=mock_client_class
        )

        mock_client_class.assert_called_once_with(api_key=api_key)
        assert client == mock_client_class.return_value

    def test_initialize_client_with_missing_key(self):
        """Test client initialization with missing API key."""
        mock_client_class = MagicMock()

        # Ensure the environment variable doesn't exist
        if "TEST_MISSING_KEY" in os.environ:
            del os.environ["TEST_MISSING_KEY"]

        client = AdapterInitializer.initialize_client(
            provider_name="Test",
            api_key_var="TEST_MISSING_KEY",
            client_class=mock_client_class
        )

        mock_client_class.assert_called_once_with(api_key=None)
        assert client == mock_client_class.return_value


class TestResponseIteratorFactory:
    """Tests for ResponseIteratorFactory class."""

    @pytest.mark.asyncio
    async def test_create_iterator(self):
        """Test creating a response iterator."""
        # Create a mock stream
        mock_chunk1 = MagicMock()
        mock_chunk2 = MagicMock()

        class MockStream:
            def __init__(self, chunks):
                self.chunks = chunks
                self.index = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.index < len(self.chunks):
                    chunk = self.chunks[self.index]
                    self.index += 1
                    return chunk
                raise StopAsyncIteration

        mock_stream = MockStream([mock_chunk1, mock_chunk2])

        # Create extraction functions
        def extract_content(chunk):
            return f"content_{id(chunk)}"

        def extract_finish_reason(chunk):
            return "stop" if chunk == mock_chunk2 else None

        # Create the iterator
        iterator = ResponseIteratorFactory.create_iterator(
            stream=mock_stream,
            model_name="test_model",
            metadata={"test": "metadata"},
            extract_content_func=extract_content,
            extract_finish_reason_func=extract_finish_reason
        )

        # Test the iterator
        response1 = await iterator.__anext__()
        assert isinstance(response1, ModelResponse)
        assert response1.content == f"content_{id(mock_chunk1)}"
        assert response1.model_name == "test_model"
        assert response1.metadata == {"test": "metadata"}
        assert response1.finish_reason is None

        response2 = await iterator.__anext__()
        assert isinstance(response2, ModelResponse)
        assert response2.content == f"content_{id(mock_chunk2)}"
        assert response2.model_name == "test_model"
        assert response2.metadata == {"test": "metadata"}
        assert response2.finish_reason == "stop"

        # Test StopAsyncIteration
        with pytest.raises(StopAsyncIteration):
            await iterator.__anext__()


class TestCommonModelHelpers:
    """Tests for CommonModelHelpers class."""

    def test_prepare_error_response(self):
        """Test preparing an error response."""
        error = ValueError("Test error")
        model_name = "test_model"
        metadata = {"test": "metadata"}

        response = CommonModelHelpers.prepare_error_response(
            model_name=model_name,
            error=error,
            metadata=metadata
        )

        assert isinstance(response, ModelResponse)
        assert response.content == "Error: Test error"
        assert response.model_name == model_name
        assert response.finish_reason == "error"
        assert response.usage == {"error": 1}
        assert response.metadata["test"] == "metadata"
        assert response.metadata["error"] == "Test error"
        assert response.metadata["error_type"] == "ValueError"

    def test_prepare_error_response_without_metadata(self):
        """Test preparing an error response without metadata."""
        error = RuntimeError("Another test error")
        model_name = "test_model"

        response = CommonModelHelpers.prepare_error_response(
            model_name=model_name,
            error=error
        )

        assert isinstance(response, ModelResponse)
        assert response.content == "Error: Another test error"
        assert response.model_name == model_name
        assert response.finish_reason == "error"
        assert response.usage == {"error": 1}
        assert response.metadata["error"] == "Another test error"
        assert response.metadata["error_type"] == "RuntimeError"
