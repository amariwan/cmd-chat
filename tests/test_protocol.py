"""Tests for protocol module."""

import asyncio
import io
import json

import pytest

from cmdchat import protocol


class TestProtocolReadWrite:
    """Test protocol message reading and writing."""

    @pytest.mark.asyncio
    async def test_write_and_read_message(self):
        """Test writing and reading a message."""
        # Create in-memory streams
        reader_stream = io.BytesIO()
        writer_stream = io.BytesIO()

        # Create mock writer
        class MockWriter:
            def write(self, data):
                writer_stream.write(data)

            async def drain(self):
                pass

        writer = MockWriter()

        # Write message
        message = {"type": "test", "data": "hello"}
        await protocol.write_message(writer, message)

        # Prepare reader
        writer_stream.seek(0)
        reader = asyncio.StreamReader()
        reader.feed_data(writer_stream.read())
        reader.feed_eof()

        # Read message
        result = await protocol.read_message(reader)
        assert result == message

    @pytest.mark.asyncio
    async def test_write_message_with_special_characters(self):
        """Test writing message with special characters."""
        writer_stream = io.BytesIO()

        class MockWriter:
            def write(self, data):
                writer_stream.write(data)

            async def drain(self):
                pass

        writer = MockWriter()

        message = {"type": "test", "text": "Hello 🌍 世界"}
        await protocol.write_message(writer, message)

        # Verify it's valid JSON
        writer_stream.seek(0)
        size_bytes = writer_stream.read(4)
        size = int.from_bytes(size_bytes, "big")
        payload = writer_stream.read(size)
        decoded = json.loads(payload.decode("utf-8"))
        assert decoded == message

    @pytest.mark.asyncio
    async def test_read_message_incomplete(self):
        """Test reading incomplete message."""
        reader = asyncio.StreamReader()
        reader.feed_data(b"\x00\x00\x00\x10")  # Size header only
        reader.feed_eof()

        with pytest.raises(asyncio.IncompleteReadError):
            await protocol.read_message(reader)

    @pytest.mark.asyncio
    async def test_read_message_empty(self):
        """Test reading from empty stream."""
        reader = asyncio.StreamReader()
        reader.feed_eof()

        with pytest.raises(asyncio.IncompleteReadError):
            await protocol.read_message(reader)

    @pytest.mark.asyncio
    async def test_large_message(self):
        """Test handling of large messages."""
        writer_stream = io.BytesIO()

        class MockWriter:
            def write(self, data):
                writer_stream.write(data)

            async def drain(self):
                pass

        writer = MockWriter()

        # Create large message
        large_data = "x" * 10000
        message = {"type": "large", "data": large_data}
        await protocol.write_message(writer, message)

        # Read it back
        writer_stream.seek(0)
        reader = asyncio.StreamReader()
        reader.feed_data(writer_stream.read())
        reader.feed_eof()

        result = await protocol.read_message(reader)
        assert result == message

    @pytest.mark.asyncio
    async def test_multiple_messages(self):
        """Test reading multiple messages in sequence."""
        writer_stream = io.BytesIO()

        class MockWriter:
            def write(self, data):
                writer_stream.write(data)

            async def drain(self):
                pass

        writer = MockWriter()

        # Write multiple messages
        messages = [
            {"type": "msg1", "id": 1},
            {"type": "msg2", "id": 2},
            {"type": "msg3", "id": 3},
        ]

        for msg in messages:
            await protocol.write_message(writer, msg)

        # Read them back
        writer_stream.seek(0)
        reader = asyncio.StreamReader()
        reader.feed_data(writer_stream.read())
        reader.feed_eof()

        for expected in messages:
            result = await protocol.read_message(reader)
            assert result == expected


class TestProtocolError:
    """Test ProtocolError exception."""

    def test_protocol_error_creation(self):
        """Test creating ProtocolError."""
        error = protocol.ProtocolError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_protocol_error_raise(self):
        """Test raising ProtocolError."""
        with pytest.raises(protocol.ProtocolError) as exc_info:
            raise protocol.ProtocolError("Custom error")

        assert "Custom error" in str(exc_info.value)
