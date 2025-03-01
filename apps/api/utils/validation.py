"""
Common validation utilities for the Maily API.
This module provides reusable validation functions to ensure consistent validation
across the application.
"""
import re
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from pydantic import ValidationError

logger = logging.getLogger(__name__)

# Email validation
def validate_email(email: str) -> bool:
    """
    Validate an email address format.

    Args:
        email: The email address to validate

    Returns:
        True if the email is valid, False otherwise
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

# API key validation
def validate_api_key(api_key: str, min_length: int = 32) -> bool:
    """
    Validate an API key format.

    Args:
        api_key: The API key to validate
        min_length: Minimum required length for the API key

    Returns:
        True if the API key is valid, False otherwise
    """
    if not api_key or len(api_key) < min_length:
        return False

    # Check for valid characters (alphanumeric and some special chars)
    valid_pattern = r'^[a-zA-Z0-9_\-\.]+$'
    return bool(re.match(valid_pattern, api_key))

# Model parameter validation
def validate_temperature(temperature: float) -> bool:
    """
    Validate temperature parameter for AI models.

    Args:
        temperature: The temperature value to validate

    Returns:
        True if the temperature is valid, False otherwise
    """
    return 0.0 <= temperature <= 1.0

def validate_max_tokens(max_tokens: int, min_value: int = 1, max_value: int = 8192) -> bool:
    """
    Validate max_tokens parameter for AI models.

    Args:
        max_tokens: The max_tokens value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        True if the max_tokens is valid, False otherwise
    """
    return min_value <= max_tokens <= max_value

# Content validation
def validate_content_safety(content: str,
                           blocked_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate content for safety/compliance issues.

    Args:
        content: The content to validate
        blocked_patterns: Optional list of regex patterns to block

    Returns:
        Dict with 'valid' boolean and optional 'issues' list
    """
    result = {"valid": True, "issues": []}

    # Check for empty content
    if not content or not content.strip():
        result["valid"] = False
        result["issues"].append("Content cannot be empty")
        return result

    # Check against blocked patterns
    if blocked_patterns:
        for pattern in blocked_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                result["valid"] = False
                result["issues"].append(f"Content contains blocked pattern: {pattern}")

    return result

# Generic validation with custom validator
def validate_with_validator(value: Any,
                           validator: Callable[[Any], bool],
                           error_message: str = "Validation failed") -> Dict[str, Any]:
    """
    Validate a value using a custom validator function.

    Args:
        value: The value to validate
        validator: A function that takes the value and returns a boolean
        error_message: Custom error message for failed validation

    Returns:
        Dict with 'valid' boolean and optional 'error' message
    """
    result = {"valid": True}

    try:
        is_valid = validator(value)
        if not is_valid:
            result["valid"] = False
            result["error"] = error_message
    except Exception as e:
        result["valid"] = False
        result["error"] = f"Validation error: {str(e)}"

    return result
