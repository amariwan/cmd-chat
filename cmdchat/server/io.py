"""I/O operations for client connections.

This module handles the encryption handshake and initial client setup.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from collections import deque
from typing import TYPE_CHECKING

from .. import crypto, protocol
from ..types import ClientSession
from ..utils import (
    sanitize_log_data,
    sanitize_name,
    sanitize_room,
    sanitize_token,
)

if TYPE_CHECKING:
    from typing import Optional

    from .state import ServerState

logger = logging.getLogger(__name__)

# Server configuration
DEFAULT_ROOM = "lobby"
ALLOWED_RENDERERS = {"rich", "minimal", "json"}
HEARTBEAT_INTERVAL = 15.0

AUTH_TOKENS = {
    token.strip()
    for token in os.getenv("CMDCHAT_TOKENS", "").split(",")
    if token.strip()
}


async def perform_handshake(
    state: ServerState,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> ClientSession:
    """Perform RSA/AES handshake with connecting client.

    Args:
        state: Server state for client registration
        reader: Client input stream
        writer: Client output stream

    Returns:
        Initialized client session

    Raises:
        protocol.ProtocolError: On handshake failure
    """
    handshake = await protocol.read_message(reader)
    if handshake.get("type") != "handshake":
        await protocol.write_message(
            writer,
            {"type": "handshake_error", "reason": "expected_handshake"},
        )
        raise protocol.ProtocolError("Expected handshake message.")

    encoded_public_key = handshake.get("public_key")
    if not isinstance(encoded_public_key, str):
        await protocol.write_message(
            writer,
            {"type": "handshake_error", "reason": "missing_public_key"},
        )
        raise protocol.ProtocolError("Handshake missing public key.")

    # Verify authentication token
    token = handshake.get("token")
    if AUTH_TOKENS and token not in AUTH_TOKENS:
        logger.warning(
            "Unauthorized connection attempt with token: %s from %s",
            sanitize_token(token),
            writer.get_extra_info("peername"),
        )
        await protocol.write_message(
            writer,
            {"type": "handshake_error", "reason": "unauthorized"},
        )
        raise protocol.ProtocolError("Unauthorized token.")

    # Sanitize client parameters
    client_name = sanitize_name(str(handshake.get("name") or "anonymous"))
    room = sanitize_room(str(handshake.get("room") or DEFAULT_ROOM))
    renderer = str(handshake.get("renderer") or "rich").lower()
    if renderer not in ALLOWED_RENDERERS:
        renderer = "rich"

    try:
        buffer_size = int(handshake.get("buffer_size", 200))
    except (TypeError, ValueError):
        buffer_size = 200
    buffer_size = max(10, min(buffer_size, 1000))

    # Setup encryption
    public_key = crypto.load_rsa_public_key(encoded_public_key.encode("ascii"))
    symmetric_key = crypto.generate_symmetric_key()
    cipher = crypto.SymmetricCipher(symmetric_key)
    encrypted_key = crypto.encrypt_for_public_key(public_key, symmetric_key)

    # Create session
    client_id = await state.session_mgr.next_client_id()
    loop_time = asyncio.get_running_loop().time()
    session = ClientSession(
        client_id=client_id,
        name=client_name,
        room=room,
        writer=writer,
        cipher=cipher,
        renderer=renderer,
        buffer_size=buffer_size,
        last_seen=loop_time,
        rate_window=deque(),
    )
    await state.session_mgr.add_session(session)

    # Send handshake response
    response = {
        "type": "handshake_ok",
        "client_id": client_id,
        "room": room,
        "renderer": renderer,
        "buffer_size": buffer_size,
        "heartbeat_interval": HEARTBEAT_INTERVAL,
        "nonce_size": crypto.AES_NONCE_SIZE,
        "encrypted_key": base64.b64encode(encrypted_key).decode("ascii"),
    }
    await protocol.write_message(writer, response)

    # Notify room
    system_msg = state.message_handler.create_system_message(
        f"{session.name} joined the chat.",
        room,
        client_id,
    )
    await state.broadcast(system_msg, room=room, exclude=client_id)

    connected = await state.connected_users()
    logger.info(
        "Client %s connected as '%s' in room '%s' (total=%s)",
        client_id,
        sanitize_log_data(client_name),
        sanitize_log_data(room),
        connected,
    )
    return session
