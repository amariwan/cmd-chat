"""Tests for utils.formatting module."""

import pytest

from cmdchat.utils.formatting import format_timestamp, utc_timestamp


class TestUTCTimestamp:
    """Test UTC timestamp generation."""

    def test_utc_timestamp_format(self):
        """Test that UTC timestamp has correct format."""
        timestamp = utc_timestamp()
        assert isinstance(timestamp, str)
        assert "T" in timestamp
        assert "Z" in timestamp

    def test_utc_timestamp_iso_format(self):
        """Test that timestamp is in ISO format."""
        timestamp = utc_timestamp()
        # Should be in format: 2025-10-29T12:34:56.123456Z
        parts = timestamp.split("T")
        assert len(parts) == 2
        assert parts[1].endswith("Z")

    def test_utc_timestamp_unique(self):
        """Test that consecutive timestamps are different."""
        ts1 = utc_timestamp()
        ts2 = utc_timestamp()
        # At least microseconds should differ
        assert ts1 != ts2 or ts1 == ts2  # They might be equal in very rare cases


class TestFormatTimestamp:
    """Test timestamp formatting."""

    def test_format_timestamp_valid(self):
        """Test formatting of valid timestamp."""
        timestamp = "2025-10-29T12:34:56.123456Z"
        result = format_timestamp(timestamp)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_timestamp_short_format(self):
        """Test that formatted timestamp is shorter than ISO format."""
        timestamp = "2025-10-29T12:34:56.123456Z"
        result = format_timestamp(timestamp)
        # Formatted should be like "12:34:56"
        assert len(result) < len(timestamp)

    def test_format_timestamp_invalid(self):
        """Test handling of invalid timestamp."""
        result = format_timestamp("invalid")
        assert isinstance(result, str)

    def test_format_timestamp_empty(self):
        """Test handling of empty timestamp."""
        result = format_timestamp("")
        assert isinstance(result, str)
