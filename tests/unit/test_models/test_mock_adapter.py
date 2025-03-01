import pytest

from ....models import MockAdapter, ModelGenerationError


def test_mock_adapter_initialization():
    """Test mock adapter initialization."""
    adapter = MockAdapter("test-api-key")
    assert adapter.api_key == "test-api-key"


def test_mock_adapter_email_content():
    """Test mock adapter email content generation."""
    adapter = MockAdapter("test-api-key")
    result = adapter.generate("Generate email content")
    assert "subject" in result
    assert "body" in result


def test_mock_adapter_design_theme():
    """Test mock adapter design theme generation."""
    adapter = MockAdapter("test-api-key")
    result = adapter.generate("Suggest design theme")
    assert "design" in result.lower()


def test_mock_adapter_error_handling():
    """Test mock adapter error handling."""
    adapter = MockAdapter("test-api-key")
    with pytest.raises(ModelGenerationError):
        adapter.generate(None)
