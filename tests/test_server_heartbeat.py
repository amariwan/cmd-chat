"""Tests for server.heartbeat module."""

import asyncio
import contextlib
from collections import deque
from unittest.mock import AsyncMock, MagicMock

import pytest

from cmdchat import crypto
from cmdchat.lib.message import MessageHandler
from cmdchat.server.heartbeat import HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT, heartbeat_loop
from cmdchat.types import ClientSession


@pytest.fixture
def message_handler():
    """Create a MessageHandler instance."""
    return MessageHandler()


@pytest.fixture
def mock_session():
    """Create a mock client session."""
    key = crypto.generate_symmetric_key()
    cipher = crypto.SymmetricCipher(key)

    writer = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.is_closing = MagicMock(return_value=False)
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()

    loop = asyncio.get_event_loop()

    return ClientSession(
        client_id="test-client-1",
        name="TestUser",
        room="lobby",
        writer=writer,
        cipher=cipher,
        renderer="rich",
        buffer_size=200,
        last_seen=loop.time(),
        rate_window=deque(),
    )


class TestHeartbeatLoop:
    """Test heartbeat loop functionality."""

    @pytest.mark.asyncio
    async def test_heartbeat_sends_ping(self, mock_session, message_handler):
        """Test that heartbeat loop sends ping messages."""
        # Run heartbeat for a short time
        task = asyncio.create_task(heartbeat_loop(mock_session, message_handler))

        # Wait for at least one heartbeat interval
        await asyncio.sleep(HEARTBEAT_INTERVAL + 0.5)

        # Cancel the task
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Verify at least one ping was sent
        assert mock_session.writer.write.called

    @pytest.mark.asyncio
    async def test_heartbeat_timeout(self, mock_session, message_handler):
        """Test heartbeat timeout detection."""
        # Set last_seen to old time
        loop = asyncio.get_event_loop()
        mock_session.last_seen = loop.time() - HEARTBEAT_TIMEOUT - 10.0

        # Run heartbeat - should timeout
        task = asyncio.create_task(heartbeat_loop(mock_session, message_handler))

        # Wait for heartbeat to detect timeout
        await asyncio.sleep(HEARTBEAT_INTERVAL + 0.5)

        # Task should have completed
        assert task.done()

        # Writer should be closed
        assert mock_session.writer.close.called

    @pytest.mark.asyncio
    async def test_heartbeat_closed_writer(self, mock_session, message_handler):
        """Test heartbeat exits when writer is closed."""
        # Set writer to closed
        mock_session.writer.is_closing = MagicMock(return_value=True)

        # Run heartbeat
        task = asyncio.create_task(heartbeat_loop(mock_session, message_handler))

        # Wait a bit
        await asyncio.sleep(HEARTBEAT_INTERVAL + 0.5)

        # Task should have completed
        assert task.done()

    @pytest.mark.asyncio
    async def test_heartbeat_send_failure(self, mock_session, message_handler):
        """Test heartbeat handles send failures."""
        # Make drain fail
        mock_session.writer.drain = AsyncMock(side_effect=Exception("Send failed"))

        # Run heartbeat
        task = asyncio.create_task(heartbeat_loop(mock_session, message_handler))

        # Wait for heartbeat interval
        await asyncio.sleep(HEARTBEAT_INTERVAL + 0.5)

        # Task should complete (error handled)
        assert task.done()

        # Writer should be closed
        assert mock_session.writer.close.called


class TestHeartbeatTiming:
    """Test heartbeat timing behavior."""

    @pytest.mark.asyncio
    async def test_heartbeat_interval(self, mock_session, message_handler):
        """Test heartbeat sends at correct interval."""
        call_count = 0
        original_drain = mock_session.writer.drain

        async def count_calls():
            nonlocal call_count
            call_count += 1
            await original_drain()

        mock_session.writer.drain = count_calls

        # Run heartbeat
        task = asyncio.create_task(heartbeat_loop(mock_session, message_handler))

        # Wait for multiple intervals
        await asyncio.sleep(HEARTBEAT_INTERVAL * 2.5)

        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Should have sent at least 2 pings
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_heartbeat_respects_last_seen(self, mock_session, message_handler):
        """Test heartbeat checks last_seen timestamp."""
        loop = asyncio.get_event_loop()

        # Update last_seen continuously
        async def update_last_seen():
            while True:
                mock_session.last_seen = loop.time()
                await asyncio.sleep(1.0)

        update_task = asyncio.create_task(update_last_seen())
        heartbeat_task = asyncio.create_task(heartbeat_loop(mock_session, message_handler))

        # Wait longer than timeout but keep updating last_seen
        await asyncio.sleep(HEARTBEAT_TIMEOUT + 5.0)

        # Heartbeat should still be running
        assert not heartbeat_task.done()

        # Cleanup
        heartbeat_task.cancel()
        update_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task
        with contextlib.suppress(asyncio.CancelledError):
            await update_task


class TestHeartbeatConstants:
    """Test heartbeat configuration constants."""

    def test_heartbeat_interval_value(self):
        """Test heartbeat interval is reasonable."""
        assert HEARTBEAT_INTERVAL > 0
        assert HEARTBEAT_INTERVAL < 60  # Less than a minute

    def test_heartbeat_timeout_value(self):
        """Test heartbeat timeout is reasonable."""
        assert HEARTBEAT_TIMEOUT > HEARTBEAT_INTERVAL
        assert HEARTBEAT_TIMEOUT < 300  # Less than 5 minutes

    def test_timeout_multiple_of_interval(self):
        """Test timeout is a reasonable multiple of interval."""
        multiple = HEARTBEAT_TIMEOUT / HEARTBEAT_INTERVAL
        assert multiple >= 2  # At least 2x interval
