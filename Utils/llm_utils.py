"""LLM response validation and processing utilities"""

import logging
from typing import Any, Dict, Optional
import litellm

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


def _is_transient_error(exc: Exception) -> bool:
    """Best-effort check if exception is likely transient/retryable."""
    transient_names = (
        'RateLimitError', 'APITimeoutError', 'Timeout', 'ServiceUnavailableError',
        'APIConnectionError', 'InternalServerError', 'GatewayTimeout', 'TooManyRequests'
    )
    name = exc.__class__.__name__
    if any(n in name for n in transient_names):
        return True
    msg = str(exc).lower()
    hints = (
        'rate limit', 'retry', 'timeout', 'timed out', 'unavailable', 'temporarily',
        'overloaded', 'connection reset', 'connection aborted', '502', '503', '504'
    )
    return any(h in msg for h in hints)


def call_litellm_with_retry(
    *,
    model: str,
    api_key: Optional[str],
    messages: Any,
    temperature: Optional[float] = None,
    extra_body: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    **kwargs: Any,
):
    """Wrapper around litellm.completion with retry.

    Args mirror litellm.completion. Pass through any extra kwargs as-needed.
    """
    attempt = 0
    while True:
        try:
            return litellm.completion(
                model=model,
                api_key=api_key,
                messages=messages,
                temperature=temperature,
                extra_body=extra_body,
                **kwargs,
            )
        except Exception as e:
            attempt += 1
            retryable = _is_transient_error(e)
            last_attempt = attempt > max_retries
            logger.warning(
                "LiteLLM call failed (attempt %s/%s, retryable=%s): %s",
                attempt, max_retries, retryable, e,
                exc_info=False,
            )
            if last_attempt or not retryable:
                raise