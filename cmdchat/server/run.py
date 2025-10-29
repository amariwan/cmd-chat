"""Main server execution module.

This module provides the core server loop and client handling logic.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
from typing import TYPE_CHECKING

from .. import protocol
from .handlers import (
    handle_chat_message,
    handle_file_chunk,
    handle_file_init,
    handle_rename,
    handle_switch_room,
    handle_system_message,
)
from .heartbeat import heartbeat_loop
from .io import perform_handshake
from .metrics import metrics_loop
from .state import ServerState
from .tls import create_ssl_context

if TYPE_CHECKING:
    from typing import Optional

    from ..types import ClientSession

logger = logging.getLogger(__name__)


async def handle_client(
    state: ServerState,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    """Process lifecycle for a single client connection.

    Args:
        state: Server state with managers
        reader: Client input stream
        writer: Client output stream

    Handles message routing, file transfers, and room management.
    """
    peer = writer.get_extra_info("peername")
    session: ClientSession | None = None
    heartbeat_task: asyncio.Task | None = None

    try:
        session = await perform_handshake(state, reader, writer)
        heartbeat_task = asyncio.create_task(
            heartbeat_loop(session, state.message_handler)
        )

        while True:
            message = await protocol.read_message(reader)
            if message.get("type") != "encrypted":
                raise protocol.ProtocolError("Expected encrypted payload.")

            nonce = message.get("nonce")
            ciphertext = message.get("ciphertext")
            if not isinstance(nonce, str) or not isinstance(ciphertext, str):
                raise protocol.ProtocolError("Encrypted message missing fields.")

            # Decrypt payload
            payload = state.message_handler.decrypt_payload(
                session,
                nonce,
                ciphertext,
            )

            # Note: Message size validation happens during decryption
            payload_type = payload.get("type")

            now = asyncio.get_running_loop().time()
            session.last_seen = now

            if payload_type == "chat":
                await handle_chat_message(state, session, payload, now)
            elif payload_type == "system":
                await handle_system_message(state, session, payload)
            elif payload_type == "pong":
                # Heartbeat acknowledgement
                continue
            elif payload_type == "file_init":
                await handle_file_init(state, session, payload)
            elif payload_type == "file_chunk":
                await handle_file_chunk(state, session, payload)
            elif payload_type == "rename":
                await handle_rename(state, session, payload)
            elif payload_type == "switch_room":
                await handle_switch_room(state, session, payload)
            else:
                raise protocol.ProtocolError("Unsupported payload type.")

    except (asyncio.IncompleteReadError, ConnectionResetError):
        logger.debug("Connection dropped for %s", peer)
    except protocol.ProtocolError as exc:
        logger.warning("Protocol error with %s: %s", peer, exc)
    except Exception as exc:
        logger.error("Unhandled server error for %s: %s", peer, exc, exc_info=True)
        if session:
            disconnect_msg = state.message_handler.create_system_message(
                f"{session.name} disconnected unexpectedly.",
                session.room,
                session.client_id,
            )
            await state.broadcast(disconnect_msg, room=session.room, exclude=session.client_id)
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()
            with contextlib.suppress(Exception):
                await heartbeat_task

        if session:
            await state.session_mgr.remove_session(session.client_id)
            leave_msg = state.message_handler.create_system_message(
                f"{session.name} left the chat.",
                session.room,
                session.client_id,
            )
            await state.broadcast(leave_msg, room=session.room, exclude=session.client_id)

        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()


async def run_server(
    host: str,
    port: int,
    *,
    certfile: Optional[str] = None,
    keyfile: Optional[str] = None,
    metrics_interval: int = 0,
) -> None:
    """Start the server and serve until interrupted.

    Args:
        host: Host interface to bind to
        port: Port to listen on
        certfile: Optional TLS certificate file
        keyfile: Optional TLS private key file
        metrics_interval: Interval for metrics logging (0 to disable)
    """
    ssl_context = create_ssl_context(certfile, keyfile)

    state = ServerState()
    server = await asyncio.start_server(
        lambda r, w: handle_client(state, r, w),
        host,
        port,
        ssl=ssl_context,
    )

    sockets = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    scheme = "wss" if ssl_context else "tcp"
    print(f"CMD Chat server listening on {scheme}://{sockets}")

    stop_event = asyncio.Event()

    def stop_server() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_server)
        except NotImplementedError:
            # Signals are not supported on some platforms (e.g., Windows).
            pass

    metrics_task: Optional[asyncio.Task] = None
    if metrics_interval > 0:
        metrics_task = asyncio.create_task(metrics_loop(state, stop_event, metrics_interval))

    try:
        async with server:
            await stop_event.wait()
            print("Shutting down server...")
            server.close()
            await server.wait_closed()
    finally:
        if metrics_task:
            metrics_task.cancel()
            with contextlib.suppress(Exception):
                await metrics_task
