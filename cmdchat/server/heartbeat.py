"""Heartbeat monitoring for client connections.

This module provides heartbeat functionality to detect and handle
disconnected or unresponsive clients.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..lib import MessageHandler
    from ..types import ClientSession

logger = logging.getLogger(__name__)

# Configuration
HEARTBEAT_INTERVAL = 15.0
HEARTBEAT_TIMEOUT = 45.0


async def heartbeat_loop(
    session: ClientSession,
    message_handler: MessageHandler,
) -> None:
    """Periodically send pings and enforce heartbeat timeout.

    Args:
        session: Client session to monitor
        message_handler: Handler for sending ping messages

    Automatically closes connection on timeout.
    """
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            if session.writer.is_closing():
                return

            now = asyncio.get_running_loop().time()
            if now - session.last_seen > HEARTBEAT_TIMEOUT:
                raise ConnectionError("Heartbeat timeout")

            try:
                ping = message_handler.create_ping_message()
                await message_handler.encrypt_and_send(session, ping)
            except Exception:
                raise ConnectionError("Failed to send heartbeat") from None
    except Exception as exc:
        logger.debug("Heartbeat terminating for client %s: %s", session.client_id, exc)
        try:
            session.writer.close()
            await session.writer.wait_closed()
        except Exception:
            pass
