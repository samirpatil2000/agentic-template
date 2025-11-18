"""JSON parsing utilities with error handling and validation"""

import json
import logging
import re
from typing import Dict, Any, Optional, Union, List

logger = logging.getLogger(__name__)


class JSONParseError(Exception):
    """Custom exception for JSON parsing errors"""
    pass


def safe_json_parse(
    content: Union[str, bytes, None], 
    default: Optional[Dict[str, Any]] = None,
    raise_on_error: bool = False
) -> Dict[str, Any]:
    """Safely parse JSON content with comprehensive error handling

    Args:
        content: String or bytes content to parse as JSON
        default: Default value to return if parsing fails (defaults to empty dict)
        raise_on_error: Whether to raise exception on parsing failure

    Returns:
        Parsed JSON as dictionary or default value

    Raises:
        JSONParseError: If raise_on_error is True and parsing fails
    """
    if default is None:
        default = {}

    # Handle None or empty content
    if not content:
        if raise_on_error:
            raise JSONParseError("Content is None or empty")
        logger.warning("Empty or None content provided for JSON parsing")
        return default

    # Convert bytes to string if needed
    if isinstance(content, bytes):
        try:
            content = content.decode('utf-8')
        except UnicodeDecodeError as e:
            error_msg = f"Failed to decode bytes content: {e}"
            logger.error(error_msg)
            if raise_on_error:
                raise JSONParseError(error_msg)
            return default

    # Ensure content is string
    if not isinstance(content, str):
        error_msg = f"Content must be string or bytes, got {type(content)}"
        logger.error(error_msg)
        if raise_on_error:
            raise JSONParseError(error_msg)
        return default

    # Strip whitespace
    content = content.strip()
    if not content:
        if raise_on_error:
            raise JSONParseError("Content is empty after stripping whitespace")
        logger.warning("Empty content after stripping whitespace")
        return default

    # Handle markdown code-fenced JSON (```json\n{...}\n``` or ```\n{...}\n```)
    if content.startswith('```'):
        # Match ```json or ``` at start, capture content, match ``` at end
        code_fence_pattern = r'^```(?:json)?\s*\n(.*)\n```$'
        match = re.match(code_fence_pattern, content, re.DOTALL)
        if match:
            content = match.group(1).strip()
            logger.debug("Extracted JSON from markdown code fence")

    try:
        parsed_data = json.loads(content)

        # Ensure we return a dictionary
        if not isinstance(parsed_data, dict):
            logger.warning(f"Parsed JSON is not a dictionary, got {type(parsed_data)}")
            if raise_on_error:
                raise JSONParseError(f"Expected dictionary, got {type(parsed_data)}")
            return default

        return parsed_data

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        error_msg = f"Failed to parse JSON content: {e}"
        logger.error(error_msg)
        if raise_on_error:
            raise JSONParseError(error_msg)
        return default


def safe_json_dumps(
    data: Any, 
    default_on_error: str = "{}",
    raise_on_error: bool = False,
    **kwargs
) -> str:
    """Safely serialize data to JSON string with error handling

    Args:
        data: Data to serialize to JSON
        default_on_error: Default string to return on serialization failure
        raise_on_error: Whether to raise exception on serialization failure
        **kwargs: Additional arguments to pass to json.dumps

    Returns:
        JSON string or default value

    Raises:
        JSONParseError: If raise_on_error is True and serialization fails
    """
    try:
        # Set default arguments for json.dumps
        dump_kwargs = {
            'ensure_ascii': False,
            'separators': (',', ':'),
            **kwargs
        }

        return json.dumps(data, **dump_kwargs)

    except (TypeError, ValueError, OverflowError) as e:
        error_msg = f"Failed to serialize data to JSON: {e}"
        logger.error(error_msg)
        if raise_on_error:
            raise JSONParseError(error_msg)
        return default_on_error


def validate_json_structure(
    data: Dict[str, Any], 
    required_fields: List[str],
    optional_fields: Optional[List[str]] = None,
    strict: bool = False
) -> Dict[str, Any]:
    """Validate JSON data structure against required and optional fields

    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        optional_fields: List of optional field names
        strict: If True, only allow required and optional fields

    Returns:
        Validated dictionary

    Raises:
        JSONParseError: If validation fails
    """
    if not isinstance(data, dict):
        raise JSONParseError(f"Expected dictionary, got {type(data)}")

    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise JSONParseError(f"Missing required fields: {missing_fields}")

    # Check for extra fields in strict mode
    if strict:
        allowed_fields = set(required_fields)
        if optional_fields:
            allowed_fields.update(optional_fields)

        extra_fields = set(data.keys()) - allowed_fields
        if extra_fields:
            raise JSONParseError(f"Unexpected fields found: {list(extra_fields)}")

    return data
