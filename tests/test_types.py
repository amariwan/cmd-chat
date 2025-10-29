"""Tests for types module."""

from pathlib import Path

import pytest

from cmdchat.types import ClientConfig, ClientSession, RoomID


class TestClientConfig:
    """Test ClientConfig dataclass."""

    def test_client_config_defaults(self):
        """Test ClientConfig with default values."""
        config = ClientConfig(
            host="localhost",
            port=5050,
            name="test",
            room="lobby",
        )

        assert config.host == "localhost"
        assert config.port == 5050
        assert config.name == "test"
        assert config.room == "lobby"
        assert config.token is None
        assert config.renderer == "rich"
        assert config.buffer_size == 200
        assert config.quiet_reconnect is False
        assert config.history_file is None
        assert config.history_passphrase is None
        assert config.tls is False
        assert config.tls_insecure is False
        assert config.ca_file is None

    def test_client_config_all_fields(self):
        """Test ClientConfig with all fields specified."""
        history_file = Path("/tmp/history.enc")
        config = ClientConfig(
            host="example.com",
            port=8080,
            name="alice",
            room="general",
            token="secret-token",
            renderer="minimal",
            buffer_size=100,
            quiet_reconnect=True,
            history_file=history_file,
            history_passphrase="password",
            tls=True,
            tls_insecure=True,
            ca_file="/etc/ssl/ca.pem",
        )

        assert config.host == "example.com"
        assert config.port == 8080
        assert config.name == "alice"
        assert config.room == "general"
        assert config.token == "secret-token"
        assert config.renderer == "minimal"
        assert config.buffer_size == 100
        assert config.quiet_reconnect is True
        assert config.history_file == history_file
        assert config.history_passphrase == "password"
        assert config.tls is True
        assert config.tls_insecure is True
        assert config.ca_file == "/etc/ssl/ca.pem"


class TestRoomID:
    """Test RoomID type alias."""

    def test_room_id_type(self):
        """Test RoomID is a string."""
        room: RoomID = "lobby"
        assert isinstance(room, str)
        assert room == "lobby"


class TestClientSession:
    """Test ClientSession would be tested with actual session creation."""

    def test_client_session_type_exists(self):
        """Test that ClientSession type is importable."""
        # This ensures the type is properly defined
        from cmdchat.types import ClientSession
        assert ClientSession is not None
