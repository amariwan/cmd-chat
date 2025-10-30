"""Sanitization utilities.

This module provides functions for sanitizing user input and sensitive data.
All sanitization follows the principle: be strict on input, safe on output.
"""

from __future__ import annotations


def sanitize_name(raw_name: str, *, max_length: int = 32) -> str:
    """Normalize and sanitize a display name.

    Args:
        raw_name: Raw user-provided name
        max_length: Maximum allowed length

    Returns:
        Sanitized name, defaults to "anonymous" if invalid

    Examples:
        >>> sanitize_name("  Alice  ")
        'Alice'
        >>> sanitize_name("")
        'anonymous'
        >>> sanitize_name("a" * 50)
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    """
    cleaned = raw_name.strip()
    if not cleaned:
        return "anonymous"

    # Remove special characters, keep only alphanumeric, spaces, hyphens, underscores
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9\s\-_]', '', cleaned)

    # If all characters were removed, return default
    if not sanitized.strip():
        return "anonymous"

    return sanitized[:max_length]


def sanitize_room(raw_room: str, *, max_length: int = 32, default: str = "lobby") -> str:
    """Normalize and sanitize a room identifier.

    Args:
        raw_room: Raw user-provided room name
        max_length: Maximum allowed length
        default: Default room name if invalid

    Returns:
        Sanitized room name in lowercase

    Examples:
        >>> sanitize_room("  DevTeam  ")
        'devteam'
        >>> sanitize_room("")
        'lobby'
        >>> sanitize_room("General-Chat")
        'general-chat'
    """
    cleaned = raw_room.strip().lower()
    if not cleaned:
        return default
    return cleaned[:max_length]


def sanitize_log_data(data: str, *, max_length: int = 64) -> str:
    """Sanitize data for safe logging.

    Truncates long strings and marks empty values clearly.

    Args:
        data: Data to sanitize
        max_length: Maximum length before truncation

    Returns:
        Sanitized string safe for logging

    Examples:
        >>> sanitize_log_data("")
        '<empty>'
        >>> sanitize_log_data("a" * 100)
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...<100 chars total>'
    """
    # Convert non-string types to string
    if not isinstance(data, str):
        data = str(data)

    if not data:
        return "<empty>"

    if len(data) > max_length:
        return f"{data[:max_length]}...<{len(data)} chars total>"

    return data


def sanitize_token(token: str | None, *, show_chars: int = 4) -> str:
    """Mask authentication tokens for safe logging.

    Args:
        token: Authentication token to mask
        show_chars: Number of characters to show at start and end

    Returns:
        Masked token string

    Examples:
        >>> sanitize_token(None)
        'None'
        >>> sanitize_token("abc")
        '***'
        >>> sanitize_token("abcdefghijklmnop")
        'abcd***mnop'
    """
    if token is None:
        return "None"
    
    if token == "":
        return ""

    if len(token) <= show_chars * 2:
        return "***"

    return f"{token[:show_chars]}***{token[-show_chars:]}"


def sanitize_filepath(filepath: str, *, max_length: int = 256) -> str:
    """Sanitize file paths for display and logging.

    Args:
        filepath: File path to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized file path

    Examples:
        >>> sanitize_filepath("../../etc/passwd")
        'etc/passwd'
        >>> sanitize_filepath("/home/user/file.txt")
        'file.txt'
    """
    import os

    # Get basename to prevent path traversal attacks
    basename = os.path.basename(filepath)

    # Remove any remaining path separators
    cleaned = basename.replace(os.sep, "_").replace("/", "_").replace("\\", "_")

    return cleaned[:max_length] if cleaned else "unnamed_file"
