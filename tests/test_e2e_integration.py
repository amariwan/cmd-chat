"""
End-to-End Integration Tests for CMD Chat.

Tests the complete workflow from server startup to client communication.
"""

import asyncio
import contextlib
from collections.abc import AsyncIterator
import socket

import pytest

from cmdchat.server.run import run_server


def get_free_port() -> int:
    """Get a free port number."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture
async def test_server() -> AsyncIterator[tuple[str, int]]:
    """Start a test server and return host, port."""
    host = "127.0.0.1"
    port = get_free_port()

    # Start server in background task
    server_task = asyncio.create_task(
        run_server(host=host, port=port, certfile=None, keyfile=None, metrics_interval=0)
    )

    # Give server time to start
    await asyncio.sleep(0.5)

    # Verify server is listening
    max_retries = 10
    for i in range(max_retries):
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            break
        except (ConnectionRefusedError, OSError):
            if i == max_retries - 1:
                raise
            await asyncio.sleep(0.1)

    yield host, port

    # Cleanup
    server_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await server_task


@pytest.mark.asyncio
async def test_e2e_server_starts_and_accepts_connections(test_server):
    """Test that server starts and accepts connections."""
    host, port = test_server

    # Verify we can connect
    reader, writer = await asyncio.open_connection(host, port)
    assert reader is not None
    assert writer is not None

    # Cleanup
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_e2e_multiple_clients_connect(test_server):
    """Test multiple clients can connect simultaneously."""
    host, port = test_server

    clients = []
    try:
        # Connect 3 clients
        for i in range(3):
            reader, writer = await asyncio.open_connection(host, port)
            clients.append((reader, writer))

        # Verify all connected
        assert len(clients) == 3
        for reader, writer in clients:
            assert reader is not None
            assert writer is not None

    finally:
        # Cleanup
        for reader, writer in clients:
            writer.close()
            await writer.wait_closed()


@pytest.mark.asyncio
async def test_e2e_client_disconnect_handling(test_server):
    """Test server handles client disconnection gracefully."""
    host, port = test_server

    # Connect and disconnect
    reader, writer = await asyncio.open_connection(host, port)
    writer.close()
    await writer.wait_closed()

    # Server should still be running and accept new connections
    reader2, writer2 = await asyncio.open_connection(host, port)
    writer2.close()
    await writer2.wait_closed()


@pytest.mark.asyncio
async def test_e2e_server_port_binding(test_server):
    """Test that server correctly binds to the specified port."""
    host, port = test_server

    # Verify port is actually in use
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # This should fail because the port is already in use
        with pytest.raises(OSError):
            s.bind((host, port))


@pytest.mark.asyncio
async def test_e2e_connection_lifecycle():
    """Test complete connection lifecycle without fixture."""
    host = "127.0.0.1"
    port = get_free_port()

    # Start server
    server_task = asyncio.create_task(
        run_server(host=host, port=port, certfile=None, keyfile=None, metrics_interval=0)
    )
    await asyncio.sleep(0.5)

    try:
        # Connect client
        reader, writer = await asyncio.open_connection(host, port)
        assert writer is not None
        writer.close()
        await writer.wait_closed()

        # Reconnect with new client
        reader2, writer2 = await asyncio.open_connection(host, port)
        writer2.close()
        await writer2.wait_closed()

    finally:
        # Cleanup server
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task


@pytest.mark.asyncio
async def test_e2e_rapid_connections(test_server):
    """Test server handles rapid connection attempts."""
    host, port = test_server

    # Rapidly connect and disconnect multiple clients
    for i in range(5):
        reader, writer = await asyncio.open_connection(host, port)
        writer.close()
        await writer.wait_closed()
        # Small delay to avoid overwhelming the server
        await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_e2e_concurrent_connections(test_server):
    """Test concurrent client connections."""
    host, port = test_server

    async def connect_and_disconnect():
        reader, writer = await asyncio.open_connection(host, port)
        try:
            return writer is not None
        finally:
            writer.close()
            await writer.wait_closed()

    # Connect 5 clients concurrently
    tasks = [connect_and_disconnect() for i in range(5)]
    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(results)


@pytest.mark.asyncio
async def test_e2e_server_availability():
    """Test server remains available under normal load."""
    host = "127.0.0.1"
    port = get_free_port()

    server_task = asyncio.create_task(
        run_server(host=host, port=port, certfile=None, keyfile=None, metrics_interval=0)
    )
    await asyncio.sleep(0.5)

    try:
        # Simulate 10 sequential connections
        for i in range(10):
            reader, writer = await asyncio.open_connection(host, port)
            assert writer is not None
            writer.close()
            await writer.wait_closed()

        # Verify server is still responsive
        reader, writer = await asyncio.open_connection(host, port)
        writer.close()
        await writer.wait_closed()

    finally:
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task


@pytest.mark.asyncio
async def test_e2e_full_workflow():
    """
    Complete E2E test simulating real-world usage.

    This test covers:
    1. Server startup
    2. Multiple client connections
    3. Client disconnections
    4. Server shutdown
    """
    host = "127.0.0.1"
    port = get_free_port()

    # Phase 1: Start server
    server_task = asyncio.create_task(
        run_server(host=host, port=port, certfile=None, keyfile=None, metrics_interval=0)
    )
    await asyncio.sleep(0.5)

    try:
        # Phase 2: Connect first wave of clients
        clients_wave1 = []
        for i in range(3):
            reader, writer = await asyncio.open_connection(host, port)
            clients_wave1.append((reader, writer))

        # Verify all connected
        assert all(w is not None for r, w in clients_wave1)

        # Phase 3: Disconnect first wave
        for reader, writer in clients_wave1:
            writer.close()
            await writer.wait_closed()

        # Phase 4: Connect second wave
        clients_wave2 = []
        for i in range(2):
            reader, writer = await asyncio.open_connection(host, port)
            clients_wave2.append((reader, writer))

        # Verify all connected
        assert all(w is not None for r, w in clients_wave2)

        # Phase 5: Disconnect second wave
        for reader, writer in clients_wave2:
            writer.close()
            await writer.wait_closed()

        # Phase 6: Final verification - server still responsive
        reader, writer = await asyncio.open_connection(host, port)
        assert writer is not None
        writer.close()
        await writer.wait_closed()

    finally:
        # Phase 7: Shutdown server
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task


def test_e2e_port_utility():
    """Test the port utility function."""
    port1 = get_free_port()
    port2 = get_free_port()

    # Ports should be valid
    assert 1024 <= port1 <= 65535
    assert 1024 <= port2 <= 65535


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "--tb=short"])
