"""Tests for utils.sanitization module."""

import pytest

from cmdchat.utils.sanitization import sanitize_log_data, sanitize_name, sanitize_room, sanitize_token


class TestSanitizeName:
    """Test name sanitization."""

    def test_sanitize_name_valid(self):
        """Test sanitization of valid names."""
        assert sanitize_name("Alice") == "Alice"
        assert sanitize_name("Bob123") == "Bob123"
        assert sanitize_name("user_name") == "user_name"

    def test_sanitize_name_strip_whitespace(self):
        """Test stripping whitespace from names."""
        assert sanitize_name("  Alice  ") == "Alice"
        assert sanitize_name("\tBob\n") == "Bob"

    def test_sanitize_name_empty(self):
        """Test handling of empty names."""
        assert sanitize_name("") == "anonymous"
        assert sanitize_name("   ") == "anonymous"

    def test_sanitize_name_too_long(self):
        """Test truncation of long names."""
        long_name = "a" * 100
        result = sanitize_name(long_name)
        assert len(result) <= 32

    def test_sanitize_name_special_characters(self):
        """Test removal of special characters."""
        result = sanitize_name("User@123!")
        assert "@" not in result or result == "anonymous"

    def test_sanitize_name_unicode(self):
        """Test handling of unicode names."""
        result = sanitize_name("Alice世界")
        assert isinstance(result, str)
        assert len(result) > 0


class TestSanitizeRoom:
    """Test room name sanitization."""

    def test_sanitize_room_valid(self):
        """Test sanitization of valid room names."""
        assert sanitize_room("lobby") == "lobby"
        assert sanitize_room("general") == "general"
        assert sanitize_room("room-123") == "room-123"

    def test_sanitize_room_strip_whitespace(self):
        """Test stripping whitespace from room names."""
        assert sanitize_room("  lobby  ") == "lobby"
        assert sanitize_room("\tgeneral\n") == "general"

    def test_sanitize_room_empty(self):
        """Test handling of empty room names."""
        assert sanitize_room("") == "lobby"
        assert sanitize_room("   ") == "lobby"

    def test_sanitize_room_too_long(self):
        """Test truncation of long room names."""
        long_room = "r" * 100
        result = sanitize_room(long_room)
        assert len(result) <= 32

    def test_sanitize_room_lowercase(self):
        """Test conversion to lowercase."""
        assert sanitize_room("LOBBY") == "lobby"
        assert sanitize_room("General") == "general"


class TestSanitizeToken:
    """Test token sanitization for logging."""

    def test_sanitize_token_none(self):
        """Test sanitization of None token."""
        assert sanitize_token(None) == "None"

    def test_sanitize_token_empty(self):
        """Test sanitization of empty token."""
        assert sanitize_token("") == ""

    def test_sanitize_token_short(self):
        """Test sanitization of short tokens."""
        result = sanitize_token("abc")
        assert "***" in result

    def test_sanitize_token_long(self):
        """Test sanitization of long tokens."""
        token = "secret-token-12345"
        result = sanitize_token(token)
        assert "***" in result
        assert "secret" not in result or result.startswith("sec")

    def test_sanitize_token_preserves_prefix(self):
        """Test that sanitization preserves some prefix."""
        token = "mytoken123456"
        result = sanitize_token(token)
        assert len(result) > 3
        assert "***" in result


class TestSanitizeLogData:
    """Test general log data sanitization."""

    def test_sanitize_log_data_string(self):
        """Test sanitization of string data."""
        result = sanitize_log_data("Hello World")
        assert isinstance(result, str)

    def test_sanitize_log_data_long_string(self):
        """Test truncation of long strings."""
        long_str = "x" * 1000
        result = sanitize_log_data(long_str)
        assert len(result) < len(long_str)

    def test_sanitize_log_data_special_chars(self):
        """Test handling of special characters."""
        result = sanitize_log_data("Test\nNew\tLine")
        assert isinstance(result, str)

    def test_sanitize_log_data_none(self):
        """Test handling of None."""
        result = sanitize_log_data(None)
        assert result is not None

    def test_sanitize_log_data_numbers(self):
        """Test handling of numbers."""
        result = sanitize_log_data(12345)
        assert isinstance(result, str)
