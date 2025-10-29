"""Formatting utilities.

This module provides functions for formatting timestamps, messages,
and other display elements.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utc_timestamp() -> str:
    """Generate an ISO 8601 UTC timestamp.

    Returns:
        Current time in ISO 8601 format with timezone

    Examples:
        >>> ts = utc_timestamp()
        >>> 'T' in ts and '+' in ts or 'Z' in ts
        True
    """
    return datetime.now(UTC).isoformat()


def format_timestamp(timestamp: str | None) -> str:
    """Format ISO 8601 timestamp for display.

    Converts UTC timestamps to local time in HH:MM:SS format.

    Args:
        timestamp: ISO 8601 timestamp string

    Returns:
        Formatted time string or placeholder

    Examples:
        >>> format_timestamp("2025-10-29T10:30:00+00:00")
        '10:30:00'  # May vary by timezone
        >>> format_timestamp(None)
        '--:--:--'
        >>> format_timestamp("invalid")
        '--:--:--'
    """
    if not timestamp:
        return "--:--:--"

    try:
        dt = datetime.fromisoformat(timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone().strftime("%H:%M:%S")
    except (ValueError, AttributeError):
        return "--:--:--"


def format_filesize(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string

    Examples:
        >>> format_filesize(1024)
        '1.00 KB'
        >>> format_filesize(1536)
        '1.50 KB'
        >>> format_filesize(1048576)
        '1.00 MB'
    """
    # Work with a float locally to avoid mutating the caller's integer
    sb = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if sb < 1024.0:
            return f"{sb:.2f} {unit}"
        sb /= 1024.0
    return f"{sb:.2f} TB"


def format_progress(current: int, total: int, *, width: int = 20) -> str:
    """Format a progress bar.

    Args:
        current: Current progress
        total: Total items
        width: Width of the progress bar

    Returns:
        Progress bar string

    Examples:
        >>> format_progress(50, 100)
        '[##########          ] 50%'
        >>> format_progress(100, 100)
        '[####################] 100%'
    """
    if total <= 0:
        return f"[{' ' * width}] 0%"

    percentage = min(100, int((current / total) * 100))
    filled = int((current / total) * width)
    bar = "#" * filled + " " * (width - filled)

    return f"[{bar}] {percentage}%"
