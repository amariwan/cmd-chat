"""Asynchronous message framing and serialization for CMD Chat."""

from __future__ import annotations

import asyncio
import json
from typing import Any

MESSAGE_LENGTH_PREFIX = 4  # Number of bytes for a big-endian length prefix
MAX_FRAME_SIZE = 65536


class ProtocolError(RuntimeError):
    """Raised when the protocol encounters an invalid message."""


async def read_message(reader: asyncio.StreamReader) -> dict[str, Any]:
    """Read a single JSON message with a length prefix."""

    length_prefix = await reader.readexactly(MESSAGE_LENGTH_PREFIX)
    message_length = int.from_bytes(length_prefix, byteorder="big")
    if message_length <= 0 or message_length > MAX_FRAME_SIZE:
        raise ProtocolError("Invalid message length.")
    payload = await reader.readexactly(message_length)
    try:
        parsed: dict[str, Any] = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ProtocolError("Received malformed JSON message.") from exc
    return parsed


async def write_message(writer: asyncio.StreamWriter, message: dict[str, Any]) -> None:
    """Serialize and write a length-prefixed JSON message."""

    payload = json.dumps(message, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    if len(payload) > MAX_FRAME_SIZE:
        raise ProtocolError("Message too large to send.")
    writer.write(len(payload).to_bytes(MESSAGE_LENGTH_PREFIX, byteorder="big"))
    writer.write(payload)
    await writer.drain()
