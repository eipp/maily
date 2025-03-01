"""
Token Counter Utility

This module provides utilities for counting tokens in text for different AI models,
which is useful for cost estimation and request validation.
"""

import re
import tiktoken
from typing import Dict, List, Optional, Union, Any

# Default tokenizer for fallback
DEFAULT_TOKENIZER = "cl100k_base"  # GPT-4 tokenizer

# Mapping of model names to tokenizer names
MODEL_TO_TOKENIZER = {
    # OpenAI models
    "gpt-4": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-3.5-turbo": "cl100k_base",
    "text-embedding-3-small": "cl100k_base",
    "text-embedding-3-large": "cl100k_base",

    # Anthropic models (using OpenAI tokenizer as approximation)
    "claude-3-opus": "cl100k_base",
    "claude-3-sonnet": "cl100k_base",
    "claude-3-haiku": "cl100k_base",

    # Google models (using OpenAI tokenizer as approximation)
    "gemini-1.5-pro": "cl100k_base",
    "gemini-1.5-flash": "cl100k_base",
}

# Cache for tokenizers to avoid reloading
_TOKENIZER_CACHE = {}


def get_tokenizer(model_name: str):
    """
    Get the appropriate tokenizer for a model.

    Args:
        model_name: The name of the model.

    Returns:
        A tokenizer instance.
    """
    # Get tokenizer name for this model
    tokenizer_name = MODEL_TO_TOKENIZER.get(model_name, DEFAULT_TOKENIZER)

    # Check cache
    if tokenizer_name in _TOKENIZER_CACHE:
        return _TOKENIZER_CACHE[tokenizer_name]

    # Load tokenizer
    try:
        tokenizer = tiktoken.get_encoding(tokenizer_name)
        _TOKENIZER_CACHE[tokenizer_name] = tokenizer
        return tokenizer
    except Exception as e:
        # Fallback to simple approximation if tiktoken fails
        return None


def count_tokens(text: str, model_name: Optional[str] = None) -> int:
    """
    Count the number of tokens in a text string.

    Args:
        text: The text to count tokens for.
        model_name: Optional model name to use specific tokenizer.

    Returns:
        The number of tokens.
    """
    if not text:
        return 0

    # Try to use tiktoken if available
    if model_name:
        tokenizer = get_tokenizer(model_name)
        if tokenizer:
            return len(tokenizer.encode(text))

    # Fallback to approximation if no tokenizer available
    # This is a rough approximation: ~4 characters per token for English text
    return len(text) // 4


def count_tokens_in_messages(messages: List[Dict[str, str]], model_name: Optional[str] = None) -> int:
    """
    Count tokens in a list of chat messages.

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys.
        model_name: Optional model name to use specific tokenizer.

    Returns:
        The number of tokens.
    """
    if not messages:
        return 0

    # Count tokens in each message
    total_tokens = 0
    for message in messages:
        # Add tokens for message content
        content = message.get('content', '')
        if isinstance(content, str):
            total_tokens += count_tokens(content, model_name)

        # Add tokens for role (approximation)
        role = message.get('role', '')
        total_tokens += count_tokens(role, model_name)

        # Add overhead tokens (approximation)
        # Each message has some overhead tokens for formatting
        total_tokens += 4

    # Add tokens for overall formatting (approximation)
    total_tokens += 2

    return total_tokens


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model_name: str
) -> float:
    """
    Estimate the cost of a request based on token counts.

    Args:
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        model_name: The name of the model.

    Returns:
        The estimated cost in USD.
    """
    # Cost per 1K tokens (input, output) for different models
    cost_map = {
        # OpenAI models
        "gpt-4": (0.03, 0.06),
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-3.5-turbo": (0.0015, 0.002),
        "text-embedding-3-small": (0.0001, 0.0),
        "text-embedding-3-large": (0.00013, 0.0),

        # Anthropic models
        "claude-3-opus": (0.015, 0.075),
        "claude-3-sonnet": (0.003, 0.015),
        "claude-3-haiku": (0.00025, 0.00125),

        # Google models
        "gemini-1.5-pro": (0.00125, 0.00375),
        "gemini-1.5-flash": (0.0005, 0.0015),
    }

    # Get cost rates for this model, defaulting to GPT-3.5-Turbo rates
    input_cost, output_cost = cost_map.get(model_name, (0.0015, 0.002))

    # Calculate cost
    prompt_cost = (prompt_tokens / 1000) * input_cost
    completion_cost = (completion_tokens / 1000) * output_cost

    return prompt_cost + completion_cost


def truncate_text_to_token_limit(text: str, max_tokens: int, model_name: Optional[str] = None) -> str:
    """
    Truncate text to fit within a token limit.

    Args:
        text: The text to truncate.
        max_tokens: The maximum number of tokens allowed.
        model_name: Optional model name to use specific tokenizer.

    Returns:
        The truncated text.
    """
    if not text:
        return ""

    # Get tokenizer
    tokenizer = get_tokenizer(model_name) if model_name else None

    if tokenizer:
        # Use tiktoken for accurate truncation
        tokens = tokenizer.encode(text)
        if len(tokens) <= max_tokens:
            return text

        # Truncate tokens and decode
        truncated_tokens = tokens[:max_tokens]
        return tokenizer.decode(truncated_tokens)
    else:
        # Fallback to character-based approximation
        # Assuming ~4 characters per token for English text
        char_limit = max_tokens * 4
        if len(text) <= char_limit:
            return text

        # Truncate to character limit and try to end at a sentence
        truncated = text[:char_limit]

        # Try to end at a sentence boundary
        last_period = truncated.rfind('.')
        if last_period > char_limit * 0.8:  # Only if period is reasonably close to the end
            return truncated[:last_period + 1]

        return truncated
