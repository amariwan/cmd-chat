"""Tests for utils.validation module."""

import pytest

from cmdchat.utils.validation import (
    validate_message_size,
    validate_port,
    validate_renderer,
)


class TestValidatePort:
    """Test port validation."""

    def test_validate_port_valid(self):
        """Test validation of valid ports."""
        assert validate_port(5050) == 5050
        assert validate_port(80) == 80
        assert validate_port(8080) == 8080
        assert validate_port(65535) == 65535

    def test_validate_port_too_low(self):
        """Test validation of port number too low."""
        with pytest.raises(ValueError, match=r"Port must be >= 1"):
            validate_port(0)
        with pytest.raises(ValueError, match=r"Port must be >= 1"):
            validate_port(-1)

    def test_validate_port_too_high(self):
        """Test validation of port number too high."""
        with pytest.raises(ValueError, match=r"Port must be <= 65535"):
            validate_port(65536)
        with pytest.raises(ValueError, match=r"Port must be <= 65535"):
            validate_port(100000)

    def test_validate_port_string(self):
        """Test validation of port as string."""
        # Should accept string and convert
        result = validate_port("5050")
        assert result == 5050

    def test_validate_port_invalid_string(self):
        """Test validation of invalid string."""
        with pytest.raises(ValueError, match=r"Port must be an integer or numeric string"):
            validate_port("invalid")


class TestValidateRenderer:
    """Test renderer validation."""

    def test_validate_renderer_valid(self):
        """Test validation of valid renderers."""
        assert validate_renderer("rich") == "rich"
        assert validate_renderer("minimal") == "minimal"
        assert validate_renderer("json") == "json"

    def test_validate_renderer_case_insensitive(self):
        """Test case-insensitive validation."""
        assert validate_renderer("RICH") == "rich"
        assert validate_renderer("Minimal") == "minimal"
        assert validate_renderer("JSON") == "json"

    def test_validate_renderer_invalid(self):
        """Test validation of invalid renderer."""
        with pytest.raises(ValueError, match=r"Invalid renderer: invalid"):
            validate_renderer("invalid")
        with pytest.raises(ValueError, match=r"Invalid renderer: unknown"):
            validate_renderer("unknown")

    def test_validate_renderer_empty(self):
        """Test validation of empty renderer."""
        with pytest.raises(ValueError, match=r"Renderer name cannot be empty"):
            validate_renderer("")


class TestValidateMessageSize:
    """Test message size validation."""

    def test_validate_message_size_valid(self):
        """Test validation of valid message sizes."""
        validate_message_size(100)
        validate_message_size(1000)
        validate_message_size(4096)

    def test_validate_message_size_too_large(self):
        """Test validation of message too large."""
        with pytest.raises(ValueError, match=r"Message too large"):
            validate_message_size(5000)
        with pytest.raises(ValueError, match=r"Message too large"):
            validate_message_size(100000)

    def test_validate_message_size_zero(self):
        """Test validation of zero size."""
        with pytest.raises(ValueError, match=r"Message too large"):
            validate_message_size(0)

    def test_validate_message_size_negative(self):
        """Test validation of negative size."""
        with pytest.raises(ValueError, match=r"Message too large"):
            validate_message_size(-1)

    def test_validate_message_size_max(self):
        """Test validation at maximum size."""
        # Assuming MAX_MESSAGE_BYTES is 4096
        validate_message_size(4096)
        with pytest.raises(ValueError, match=r"Message too large"):
            validate_message_size(4097)
