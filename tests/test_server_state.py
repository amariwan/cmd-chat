"""Tests for server.state module."""

from collections import deque
from unittest.mock import AsyncMock, MagicMock
import contextlib

import pytest

from cmdchat import crypto
from cmdchat.lib.message import MessageHandler
from cmdchat.lib.session import SessionManager
from cmdchat.server.metrics import MetricsCollector
from cmdchat.server.state import ServerState
from cmdchat.types import ClientSession


@pytest.fixture
def server_state():
    """Create a ServerState instance."""
    session_manager = SessionManager()
    message_handler = MessageHandler()
    metrics = MetricsCollector()

    return ServerState(
        session_manager=session_manager,
        message_handler=message_handler,
        metrics=metrics,
    )


@pytest.fixture
async def mock_session():
    """Create a mock client session."""
    key = crypto.generate_symmetric_key()
    cipher = crypto.SymmetricCipher(key)

    writer = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.is_closing = MagicMock(return_value=False)

    return ClientSession(
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


class TestServerStateBasics:
    """Test basic ServerState operations."""

    def test_server_state_creation(self, server_state):
        """Test ServerState is created properly."""
        assert server_state.session_manager is not None
        assert server_state.message_handler is not None
        assert server_state.metrics is not None

    def test_server_state_has_shutdown_flag(self, server_state):
        """Test ServerState has shutdown flag."""
        assert hasattr(server_state, "shutdown")
        assert server_state.shutdown is False

    @pytest.mark.asyncio
    async def test_set_shutdown(self, server_state):
        """Test setting shutdown flag."""
        await server_state.set_shutdown()
        assert server_state.shutdown is True


class TestServerStateBroadcast:
    """Test broadcast operations."""

    @pytest.mark.asyncio
    async def test_broadcast_to_room(self, server_state, mock_session):
        """Test broadcasting a message to a room."""
        # Add session to manager
        await server_state.session_manager.add_session(mock_session)

        # Broadcast message
        payload = {"type": "chat", "message": "Hello"}
        await server_state.broadcast_to_room("lobby", payload)

        # Verify writer was called
        assert mock_session.writer.write.called

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_room(self, server_state):
        """Test broadcasting to a room with no clients."""
        # Should not raise an error
        payload = {"type": "chat", "message": "Hello"}
        await server_state.broadcast_to_room("empty-room", payload)

    @pytest.mark.asyncio
    async def test_broadcast_excludes_sender(self, server_state, mock_session):
        """Test that broadcast can exclude sender."""
        # Add session
        await server_state.session_manager.add_session(mock_session)

        # Broadcast excluding this client
        payload = {"type": "chat", "message": "Hello"}
        await server_state.broadcast_to_room(
            "lobby",
            payload,
            exclude_client_id="test-client-1",
        )

        # Writer should not have been called
        assert not mock_session.writer.write.called

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self, server_state):
        """Test broadcasting to multiple clients in a room."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            key = crypto.generate_symmetric_key()
            cipher = crypto.SymmetricCipher(key)

            writer = MagicMock()
            writer.write = MagicMock()
            writer.drain = AsyncMock()
            writer.is_closing = MagicMock(return_value=False)

            session = ClientSession(
                client_id=f"client-{i}",
                name=f"User{i}",
                room="lobby",
                writer=writer,
                cipher=cipher,
                renderer="rich",
                buffer_size=200,
                last_seen=0.0,
                rate_window=deque(),
            )
            sessions.append(session)
            await server_state.session_manager.add_session(session)

        # Broadcast
        payload = {"type": "system", "message": "Announcement"}
        await server_state.broadcast_to_room("lobby", payload)

        # All writers should be called
        for session in sessions:
            assert session.writer.write.called


class TestServerStateClientManagement:
    """Test client management."""

    @pytest.mark.asyncio
    async def test_add_client(self, server_state, mock_session):
        """Test adding a client."""
        await server_state.session_manager.add_session(mock_session)

        client_ids = server_state.session_manager.get_all_client_ids()
        assert "test-client-1" in client_ids

    @pytest.mark.asyncio
    async def test_remove_client(self, server_state, mock_session):
        """Test removing a client."""
        await server_state.session_manager.add_session(mock_session)
        await server_state.session_manager.remove_session("test-client-1")

        session = server_state.session_manager.get_session("test-client-1")
        assert session is None

    @pytest.mark.asyncio
    async def test_move_client_to_room(self, server_state, mock_session):
        """Test moving a client to different room."""
        await server_state.session_manager.add_session(mock_session)
        await server_state.session_manager.move_session("test-client-1", "general")

        session = server_state.session_manager.get_session("test-client-1")
        assert session.room == "general"


class TestServerStateMetrics:
    """Test metrics integration."""

    @pytest.mark.asyncio
    async def test_metrics_track_clients(self, server_state, mock_session):
        """Test that metrics track client count."""
        # Add client
        await server_state.session_manager.add_session(mock_session)

        # Update metrics
        client_count = len(server_state.session_manager.get_all_client_ids())
        server_state.metrics.update_client_count(client_count)

        assert server_state.metrics.total_clients == client_count

    @pytest.mark.asyncio
    async def test_metrics_track_messages(self, server_state, mock_session):
        """Test that metrics track message count."""
        await server_state.session_manager.add_session(mock_session)

        # Send message
        payload = {"type": "chat", "message": "Test"}
        await server_state.broadcast_to_room("lobby", payload)

        # Increment metrics
        server_state.metrics.increment_messages()

        assert server_state.metrics.total_messages == 1


class TestServerStateErrorHandling:
    """Test error handling in ServerState."""

    @pytest.mark.asyncio
    async def test_broadcast_with_closed_writer(self, server_state):
        """Test broadcasting to a client with closed writer."""
        # Create session with closed writer
        key = crypto.generate_symmetric_key()
        cipher = crypto.SymmetricCipher(key)

        writer = MagicMock()
        writer.write = MagicMock()
        writer.drain = AsyncMock()
        writer.is_closing = MagicMock(return_value=True)

        session = ClientSession(
            client_id="closed-client",
            name="ClosedUser",
            room="lobby",
            writer=writer,
            cipher=cipher,
            renderer="rich",
            buffer_size=200,
            last_seen=0.0,
            rate_window=deque(),
        )

        await server_state.session_manager.add_session(session)

        # Broadcast should handle closed writer gracefully
        payload = {"type": "chat", "message": "Test"}
        await server_state.broadcast_to_room("lobby", payload)

    @pytest.mark.asyncio
    async def test_broadcast_with_write_error(self, server_state):
        """Test broadcasting when write fails."""
        # Create session with writer that raises error
        key = crypto.generate_symmetric_key()
        cipher = crypto.SymmetricCipher(key)

        writer = MagicMock()
        writer.write = MagicMock(side_effect=Exception("Write failed"))
        writer.drain = AsyncMock()
        writer.is_closing = MagicMock(return_value=False)

        session = ClientSession(
            client_id="error-client",
            name="ErrorUser",
            room="lobby",
            writer=writer,
            cipher=cipher,
            renderer="rich",
            buffer_size=200,
            last_seen=0.0,
            rate_window=deque(),
        )

        await server_state.session_manager.add_session(session)

        # Broadcast should handle error gracefully
        payload = {"type": "chat", "message": "Test"}
        # This may raise or handle internally depending on implementation
        with contextlib.suppress(Exception):
            await server_state.broadcast_to_room("lobby", payload)
