"""Tests for lib.message module."""

import pytest

from cmdchat import crypto
from cmdchat.lib.message import MessageHandler
from cmdchat.types import ClientSession


@pytest.fixture
def message_handler():
    """Create a MessageHandler instance."""
    return MessageHandler()


@pytest.fixture
def mock_session():
    """Create a mock client session."""
    from collections import deque
    from unittest.mock import AsyncMock, MagicMock

    key = crypto.generate_symmetric_key()
    cipher = crypto.SymmetricCipher(key)

    writer = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()  # Use AsyncMock for async method
    writer.is_closing = MagicMock(return_value=False)

    session = ClientSession(
        client_id="test-client-1",
        name="TestUser",
        room="lobby",
        writer=writer,
        cipher=cipher,
        renderer="rich",
        buffer_size=200,
        last_seen=0.0,
        rate_window=deque(),
    )
    return session


class TestMessageHandlerCreation:
    """Test MessageHandler creation and message types."""

    def test_create_chat_message(self, message_handler):
        """Test creating a chat message."""
        msg = message_handler.create_chat_message(
            sender="Alice",
            message="Hello",
            room="lobby",
            client_id="client-1",
            sequence=1,
        )

        assert msg["type"] == "chat"
        assert msg["sender"] == "Alice"
        assert msg["message"] == "Hello"
        assert msg["room"] == "lobby"
        assert msg["client_id"] == "client-1"
        assert msg["sequence"] == 1
        assert "timestamp" in msg

    def test_create_system_message(self, message_handler):
        """Test creating a system message."""
        msg = message_handler.create_system_message(
            message="User joined",
            room="lobby",
            client_id="client-1",
        )

        assert msg["type"] == "system"
        assert msg["message"] == "User joined"
        assert msg["room"] == "lobby"
        assert msg["client_id"] == "client-1"
        assert "timestamp" in msg

    def test_create_ping_message(self, message_handler):
        """Test creating a ping message."""
        msg = message_handler.create_ping_message()

        assert msg["type"] == "ping"
        assert "timestamp" in msg

    def test_create_file_init_message(self, message_handler):
        """Test creating a file init message."""
        msg = message_handler.create_file_init_message(
            sender="Alice",
            file_id="file-123",
            filename="test.txt",
            filesize=1024,
            total_chunks=10,
            room="lobby",
            client_id="client-1",
        )

        assert msg["type"] == "file_init"
        assert msg["sender"] == "Alice"
        assert msg["file_id"] == "file-123"
        assert msg["filename"] == "test.txt"
        assert msg["filesize"] == 1024
        assert msg["total_chunks"] == 10
        assert msg["room"] == "lobby"

    def test_create_file_chunk_message(self, message_handler):
        """Test creating a file chunk message."""
        msg = message_handler.create_file_chunk_message(
            sender="Alice",
            file_id="file-123",
            chunk_index=5,
            chunk_data="base64data",
            is_final=False,
            room="lobby",
            client_id="client-1",
        )

        assert msg["type"] == "file_chunk"
        assert msg["file_id"] == "file-123"
        assert msg["chunk_index"] == 5
        assert msg["chunk_data"] == "base64data"
        assert msg["is_final"] is False


class TestMessageHandlerEncryption:
    """Test MessageHandler encryption/decryption."""

    @pytest.mark.asyncio
    async def test_encrypt_and_send(self, message_handler, mock_session):
        """Test encrypting and sending a message."""
        payload = {"type": "test", "data": "hello"}

        await message_handler.encrypt_and_send(mock_session, payload)

        # Verify writer was called
        assert mock_session.writer.write.called
        assert mock_session.writer.drain.called

    def test_decrypt_payload(self, message_handler, mock_session):
        """Test decrypting a payload."""
        import base64
        import json

        # Create encrypted payload
        original = {"type": "test", "data": "secret"}
        plaintext = json.dumps(original, separators=(",", ":")).encode("utf-8")
        nonce, ciphertext = mock_session.cipher.encrypt(plaintext)

        nonce_b64 = base64.b64encode(nonce).decode("ascii")
        ciphertext_b64 = base64.b64encode(ciphertext).decode("ascii")

        # Decrypt
        result = message_handler.decrypt_payload(
            mock_session,
            nonce_b64,
            ciphertext_b64,
        )

        assert result == original


class TestMessageHandlerSequence:
    """Test message sequence tracking."""

    @pytest.mark.asyncio
    async def test_next_sequence(self, message_handler):
        """Test sequence number generation."""
        seq1 = await message_handler.next_sequence("lobby")
        seq2 = await message_handler.next_sequence("lobby")
        seq3 = await message_handler.next_sequence("general")

        assert seq2 == seq1 + 1
        assert seq3 == 1  # Different room starts at 1
