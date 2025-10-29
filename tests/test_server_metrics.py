"""Tests for server.metrics module."""

import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest

from cmdchat.server.metrics import MetricsCollector, metrics_loop


@pytest.fixture
def metrics_collector():
    """Create a MetricsCollector instance."""
    return MetricsCollector()


class TestMetricsCollector:
    """Test MetricsCollector class."""

    def test_metrics_creation(self, metrics_collector):
        """Test metrics collector is created with defaults."""
        assert metrics_collector.total_clients == 0
        assert metrics_collector.total_messages == 0

    def test_update_client_count(self, metrics_collector):
        """Test updating client count."""
        metrics_collector.update_client_count(5)
        assert metrics_collector.total_clients == 5

        metrics_collector.update_client_count(10)
        assert metrics_collector.total_clients == 10

    def test_increment_messages(self, metrics_collector):
        """Test incrementing message count."""
        metrics_collector.increment_messages()
        assert metrics_collector.total_messages == 1

        metrics_collector.increment_messages()
        metrics_collector.increment_messages()
        assert metrics_collector.total_messages == 3

    def test_increment_messages_by_amount(self, metrics_collector):
        """Test incrementing messages by specific amount."""
        metrics_collector.increment_messages(10)
        assert metrics_collector.total_messages == 10

        metrics_collector.increment_messages(5)
        assert metrics_collector.total_messages == 15

    def test_get_metrics(self, metrics_collector):
        """Test getting all metrics."""
        metrics_collector.update_client_count(7)
        metrics_collector.increment_messages(25)

        metrics = metrics_collector.get_metrics()

        assert metrics["clients"] == 7
        assert metrics["messages"] == 25

    def test_reset_metrics(self, metrics_collector):
        """Test resetting metrics."""
        metrics_collector.update_client_count(10)
        metrics_collector.increment_messages(50)

        metrics_collector.reset()

        assert metrics_collector.total_clients == 0
        assert metrics_collector.total_messages == 0


class TestMetricsLoop:
    """Test metrics logging loop."""

    @pytest.mark.asyncio
    async def test_metrics_loop_logs_periodically(self):
        """Test that metrics loop logs at interval."""
        from cmdchat.lib.message import MessageHandler
        from cmdchat.lib.session import SessionManager
        from cmdchat.server.state import ServerState

        session_manager = SessionManager()
        message_handler = MessageHandler()
        metrics = MetricsCollector()

        state = ServerState(
            session_manager=session_manager,
            message_handler=message_handler,
            metrics=metrics,
        )

        stop_event = asyncio.Event()

        # Run metrics loop with short interval
        task = asyncio.create_task(metrics_loop(state, stop_event, interval=1))

        # Wait for a couple intervals
        await asyncio.sleep(2.5)

        # Stop the loop
        stop_event.set()
        await task

    @pytest.mark.asyncio
    async def test_metrics_loop_respects_stop_event(self):
        """Test that metrics loop stops on event."""
        from cmdchat.lib.message import MessageHandler
        from cmdchat.lib.session import SessionManager
        from cmdchat.server.state import ServerState

        session_manager = SessionManager()
        message_handler = MessageHandler()
        metrics = MetricsCollector()

        state = ServerState(
            session_manager=session_manager,
            message_handler=message_handler,
            metrics=metrics,
        )

        stop_event = asyncio.Event()

        # Start metrics loop
        task = asyncio.create_task(metrics_loop(state, stop_event, interval=10))

        # Immediately stop
        await asyncio.sleep(0.1)
        stop_event.set()

        # Should complete quickly
        await asyncio.wait_for(task, timeout=1.0)
        assert task.done()

    @pytest.mark.asyncio
    async def test_metrics_loop_disabled(self):
        """Test metrics loop when disabled via env var."""
        from cmdchat.lib.message import MessageHandler
        from cmdchat.lib.session import SessionManager
        from cmdchat.server.state import ServerState

        session_manager = SessionManager()
        message_handler = MessageHandler()
        metrics = MetricsCollector()

        state = ServerState(
            session_manager=session_manager,
            message_handler=message_handler,
            metrics=metrics,
        )

        stop_event = asyncio.Event()

        # Disable metrics
        with patch.dict(os.environ, {"CMDCHAT_METRICS": "0"}):
            task = asyncio.create_task(metrics_loop(state, stop_event, interval=1))

            # Should return immediately
            await asyncio.sleep(0.1)

            assert task.done()

    @pytest.mark.asyncio
    async def test_metrics_loop_calculates_rate(self):
        """Test that metrics loop calculates message rate."""
        from cmdchat.lib.message import MessageHandler
        from cmdchat.lib.session import SessionManager
        from cmdchat.server.state import ServerState

        session_manager = SessionManager()
        message_handler = MessageHandler()
        metrics = MetricsCollector()

        state = ServerState(
            session_manager=session_manager,
            message_handler=message_handler,
            metrics=metrics,
        )

        stop_event = asyncio.Event()

        # Add some messages
        metrics.increment_messages(10)

        # Run metrics loop
        task = asyncio.create_task(metrics_loop(state, stop_event, interval=1))

        await asyncio.sleep(1.5)

        # Add more messages
        metrics.increment_messages(20)

        await asyncio.sleep(1.5)

        # Stop
        stop_event.set()
        await task


class TestMetricsIntegration:
    """Test metrics integration with server state."""

    @pytest.mark.asyncio
    async def test_metrics_track_active_sessions(self):
        """Test metrics tracking active client sessions."""
        from collections import deque

        from cmdchat import crypto
        from cmdchat.lib.message import MessageHandler
        from cmdchat.lib.session import SessionManager
        from cmdchat.server.state import ServerState
        from cmdchat.types import ClientSession

        session_manager = SessionManager()
        message_handler = MessageHandler()
        metrics = MetricsCollector()

        state = ServerState(
            session_manager=session_manager,
            message_handler=message_handler,
            metrics=metrics,
        )

        # Add sessions
        for i in range(3):
            key = crypto.generate_symmetric_key()
            cipher = crypto.SymmetricCipher(key)
            writer = MagicMock()

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
            await state.session_manager.add_session(session)

        # Update metrics
        client_count = len(state.session_manager.get_all_client_ids())
        metrics.update_client_count(client_count)

        assert metrics.total_clients == 3

    @pytest.mark.asyncio
    async def test_metrics_track_broadcast_messages(self):
        """Test metrics tracking broadcast messages."""
        from collections import deque
        from unittest.mock import AsyncMock

        from cmdchat import crypto
        from cmdchat.lib.message import MessageHandler
        from cmdchat.lib.session import SessionManager
        from cmdchat.server.state import ServerState
        from cmdchat.types import ClientSession

        session_manager = SessionManager()
        message_handler = MessageHandler()
        metrics = MetricsCollector()

        state = ServerState(
            session_manager=session_manager,
            message_handler=message_handler,
            metrics=metrics,
        )

        # Add a session
        key = crypto.generate_symmetric_key()
        cipher = crypto.SymmetricCipher(key)
        writer = MagicMock()
        writer.write = MagicMock()
        writer.drain = AsyncMock()
        writer.is_closing = MagicMock(return_value=False)

        session = ClientSession(
            client_id="test-client",
            name="TestUser",
            room="lobby",
            writer=writer,
            cipher=cipher,
            renderer="rich",
            buffer_size=200,
            last_seen=0.0,
            rate_window=deque(),
        )
        await state.session_manager.add_session(session)

        # Broadcast messages
        for i in range(5):
            payload = {"type": "chat", "message": f"Message {i}"}
            await state.broadcast_to_room("lobby", payload)
            metrics.increment_messages()

        assert metrics.total_messages == 5
