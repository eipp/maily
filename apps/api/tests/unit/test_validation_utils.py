"""
Unit tests for validation utilities.
"""
import pytest
from typing import Dict, Any

from apps.api.utils.validation import (
    validate_email,
    validate_api_key,
    validate_temperature,
    validate_max_tokens,
    validate_content_safety,
    validate_with_validator
)


class TestEmailValidation:
    """Tests for email validation functions."""

    @pytest.mark.parametrize("email,expected", [
        ("user@example.com", True),
        ("user.name@example.co.uk", True),
        ("user+tag@example.com", True),
        ("user-name@example.com", True),
        ("user123@example.com", True),
        ("user@subdomain.example.com", True),
        ("", False),
        ("user@", False),
        ("@example.com", False),
        ("user@example", False),
        ("user@.com", False),
        ("user@example..com", False),
        ("user name@example.com", False),
        ("user@example.c", False),  # TLD too short
    ])
    def test_validate_email(self, email, expected):
        """Test email validation with various inputs."""
        assert validate_email(email) == expected


class TestApiKeyValidation:
    """Tests for API key validation functions."""

    @pytest.mark.parametrize("api_key,min_length,expected", [
        ("abcdef1234567890abcdef1234567890", 32, True),
        ("abcdef1234567890abcdef1234567890", 16, True),
        ("abcdef1234567890", 32, False),  # Too short
        ("", 32, False),  # Empty
        (None, 32, False),  # None
        ("abcdef1234567890abcdef1234567890", 64, False),  # Min length too high
        ("abcdef!@#$%^&*()", 16, False),  # Invalid characters
        ("abcdef_-.", 8, True),  # Valid special chars
    ])
    def test_validate_api_key(self, api_key, min_length, expected):
        """Test API key validation with various inputs."""
        assert validate_api_key(api_key, min_length) == expected


class TestModelParameterValidation:
    """Tests for model parameter validation functions."""

    @pytest.mark.parametrize("temperature,expected", [
        (0.0, True),
        (0.5, True),
        (1.0, True),
        (-0.1, False),
        (1.1, False),
        (0, True),
        (1, True),
    ])
    def test_validate_temperature(self, temperature, expected):
        """Test temperature validation with various inputs."""
        assert validate_temperature(temperature) == expected

    @pytest.mark.parametrize("max_tokens,min_value,max_value,expected", [
        (100, 1, 8192, True),
        (1, 1, 8192, True),
        (8192, 1, 8192, True),
        (0, 1, 8192, False),
        (9000, 1, 8192, False),
        (500, 1000, 8192, False),
        (9000, 1, 10000, True),
    ])
    def test_validate_max_tokens(self, max_tokens, min_value, max_value, expected):
        """Test max_tokens validation with various inputs."""
        assert validate_max_tokens(max_tokens, min_value, max_value) == expected


class TestContentValidation:
    """Tests for content validation functions."""

    def test_validate_content_safety_empty(self):
        """Test content safety validation with empty content."""
        result = validate_content_safety("")
        assert result["valid"] is False
        assert "Content cannot be empty" in result["issues"]

    def test_validate_content_safety_whitespace(self):
        """Test content safety validation with whitespace content."""
        result = validate_content_safety("   ")
        assert result["valid"] is False
        assert "Content cannot be empty" in result["issues"]

    def test_validate_content_safety_valid(self):
        """Test content safety validation with valid content."""
        result = validate_content_safety("This is valid content.")
        assert result["valid"] is True
        assert len(result["issues"]) == 0

    def test_validate_content_safety_blocked_patterns(self):
        """Test content safety validation with blocked patterns."""
        blocked_patterns = [
            r"badword",
            r"sensitive\s+information",
            r"\b(?:password|credit\s*card)\b"
        ]

        # Valid content
        result = validate_content_safety("This is valid content.", blocked_patterns)
        assert result["valid"] is True
        assert len(result["issues"]) == 0

        # Content with blocked word
        result = validate_content_safety("This contains a badword in it.", blocked_patterns)
        assert result["valid"] is False
        assert len(result["issues"]) == 1

        # Content with multiple blocked patterns
        result = validate_content_safety(
            "This contains a badword and sensitive information about my password.",
            blocked_patterns
        )
        assert result["valid"] is False
        assert len(result["issues"]) == 3


class TestGenericValidation:
    """Tests for generic validation functions."""

    def test_validate_with_validator_success(self):
        """Test generic validation with successful validation."""
        def is_even(n):
            return n % 2 == 0

        result = validate_with_validator(4, is_even)
        assert result["valid"] is True
        assert "error" not in result

    def test_validate_with_validator_failure(self):
        """Test generic validation with failed validation."""
        def is_even(n):
            return n % 2 == 0

        result = validate_with_validator(3, is_even, "Number must be even")
        assert result["valid"] is False
        assert result["error"] == "Number must be even"

    def test_validate_with_validator_exception(self):
        """Test generic validation with exception in validator."""
        def validator_with_exception(value):
            raise ValueError("Validation error occurred")

        result = validate_with_validator("test", validator_with_exception)
        assert result["valid"] is False
        assert "Validation error: Validation error occurred" in result["error"]
