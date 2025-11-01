"""LLM response validation and processing utilities"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMResponseError(Exception):
    """Custom exception for LLM response validation errors"""
    pass


def validate_llm_response(
    response: Any, 
    require_content: bool = True,
    min_content_length: int = 1
) -> str:
    """Validate LLM response structure and extract content

    Args:
        response: LLM response object to validate
        require_content: Whether to require non-empty content
        min_content_length: Minimum required content length

    Returns:
        Response content as string

    Raises:
        LLMResponseError: If response validation fails
    """
    if not response:
        raise LLMResponseError("Response is None or empty")

    if not hasattr(response, 'choices'):
        raise LLMResponseError("Response missing 'choices' attribute")

    if not response.choices or len(response.choices) == 0:
        raise LLMResponseError("No choices returned in LLM response")

    first_choice = response.choices[0]
    if not hasattr(first_choice, 'message'):
        raise LLMResponseError("First choice missing 'message' attribute")

    message = first_choice.message
    if not hasattr(message, 'content'):
        raise LLMResponseError("Message missing 'content' attribute")

    content = message.content

    if require_content:
        if not content:
            raise LLMResponseError("Response content is empty")

        if len(content) < min_content_length:
            raise LLMResponseError(
                f"Response content too short: {len(content)} < {min_content_length}"
            )

    return content or ""