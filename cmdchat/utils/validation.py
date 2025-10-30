"""Validation utilities.

This module provides functions for validating user input, message sizes,
rate limits, and other constraints.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import ClientSession


class ValidationError(ValueError):
    """Raised when validation fails."""



def validate_message_size(size: int, *, max_size: int = 4096) -> None:
    """Validate message size.

    Args:
        size: Message size in bytes to validate
        max_size: Maximum allowed size in bytes (default: 4096)

    Raises:
        ValidationError: If message exceeds max size

    Examples:
        >>> validate_message_size(100)
        >>> validate_message_size(5000)
        Traceback (most recent call last):
        ...
        cmdchat.utils.validation.ValidationError: Message too large: 5000 bytes (max 4096 bytes)
    """
    if size <= 0 or size > max_size:
        raise ValidationError(f"Message too large: {size} bytes (max {max_size} bytes)")


def validate_file_size(size: int, *, max_size: int) -> None:
    """Validate file size.

    Args:
        size: File size in bytes
        max_size: Maximum allowed size in bytes

    Raises:
        ValidationError: If file exceeds max size

    Examples:
        >>> validate_file_size(1024, max_size=2048)
        >>> validate_file_size(2048, max_size=1024)
        Traceback (most recent call last):
        ...
        cmdchat.utils.validation.ValidationError: File too large: 2048 bytes (max 1024 bytes)
    """
    if size <= 0:
        raise ValidationError("File size must be positive")

    if size > max_size:
        raise ValidationError(f"File too large: {size} bytes (max {max_size} bytes)")


def validate_room_name(room: str, *, min_length: int = 1, max_length: int = 32) -> None:
    """Validate room name.

    Args:
        room: Room name to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Raises:
        ValidationError: If room name is invalid
    """
    if not room or len(room) < min_length:
        raise ValidationError(f"Room name too short (min {min_length} chars)")

    if len(room) > max_length:
        raise ValidationError(f"Room name too long (max {max_length} chars)")

    # Allow alphanumeric, hyphens, and underscores
    if not all(c.isalnum() or c in "-_" for c in room):
        raise ValidationError("Room name contains invalid characters")


def validate_username(name: str, *, min_length: int = 1, max_length: int = 32) -> None:
    """Validate username.

    Args:
        name: Username to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Raises:
        ValidationError: If username is invalid
    """
    if not name or len(name) < min_length:
        raise ValidationError(f"Username too short (min {min_length} chars)")

    if len(name) > max_length:
        raise ValidationError(f"Username too long (max {max_length} chars)")


def check_rate_limit(
    session: ClientSession,
    now: float,
    *,
    window: float = 5.0,
    max_messages: int = 12,
) -> bool:
    """Check if client is within rate limits.

    Args:
        session: Client session to check
        now: Current timestamp
        window: Time window in seconds
        max_messages: Maximum messages allowed in window

    Returns:
        True if within limits, False if exceeded

    Examples:
        >>> from collections import deque
        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class MockSession:
        ...     rate_window: deque
        >>> session = MockSession(rate_window=deque())
        >>> check_rate_limit(session, 1.0)
        True
        >>> for i in range(15):
        ...     session.rate_window.append(1.0 + i * 0.1)
        >>> check_rate_limit(session, 2.0)
        False
    """
    if session.rate_window is None:
        session.rate_window = deque()

    rate_window = session.rate_window
    rate_window.append(now)

    # Remove timestamps outside the window
    while rate_window and now - rate_window[0] > window:
        rate_window.popleft()

    return len(rate_window) <= max_messages


def validate_token(token: str | None, *, allowed_tokens: set[str]) -> bool:
    """Validate authentication token.

    Args:
        token: Token to validate
        allowed_tokens: Set of valid tokens

    Returns:
        True if token is valid, False otherwise

    Examples:
        >>> validate_token("abc123", allowed_tokens={"abc123", "def456"})
        True
        >>> validate_token("xyz789", allowed_tokens={"abc123", "def456"})
        False
        >>> validate_token(None, allowed_tokens=set())
        True
        >>> validate_token(None, allowed_tokens={"abc123"})
        False
    """
    # If no tokens configured, allow all
    if not allowed_tokens:
        return True

    # If tokens required, check if provided token is valid
    return token in allowed_tokens if token else False


def validate_port(value) -> int:
    """Validate a port number.

    Accepts int or numeric string. Returns the port as int if valid.

    Raises:
        ValidationError: If the port is invalid or out of range (1-65535).
    """
    if isinstance(value, str):
        if not value.isdigit():
            raise ValidationError("Port must be an integer or numeric string")
        port = int(value)
    elif isinstance(value, int):
        port = value
    else:
        raise ValidationError("Port must be an integer or numeric string")

    if port < 1:
        raise ValidationError("Port must be >= 1")

    if port > 65535:
        raise ValidationError("Port must be <= 65535")

    return port


def validate_renderer(name: str) -> str:
    """Validate a renderer name.

    Args:
        name: Renderer name to validate

    Returns:
        Normalized (lowercase) renderer name

    Raises:
        ValidationError: If renderer name is invalid

    Examples:
        >>> validate_renderer("rich")
        'rich'
        >>> validate_renderer("MINIMAL")
        'minimal'
        >>> validate_renderer("invalid")
        Traceback (most recent call last):
        ...
        cmdchat.utils.validation.ValidationError: Invalid renderer: invalid
    """
    if not name:
        raise ValidationError("Renderer name cannot be empty")

    # Valid renderer types
    valid_renderers = {"rich", "minimal", "json", "plain", "markdown"}
    normalized = name.lower()

    if normalized not in valid_renderers:
        raise ValidationError(f"Invalid renderer: {name}")

    return normalized
