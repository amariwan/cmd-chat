"""Send and receive loops for client.

This module provides the main send and receive loops that handle
user input and server messages.
"""

from __future__ import annotations

import asyncio
import contextlib
import sys
from typing import TYPE_CHECKING

from .. import protocol
from .io import decrypt_message, send_encrypted

if TYPE_CHECKING:
    from collections.abc import Callable

    from .. import crypto


async def send_loop(
    stop_event: asyncio.Event,
    command_handler: Callable[[str], bool],
    chat_sender: Callable[[str], None],
) -> None:
    """Read user input, handle commands, and send chat messages.

    Args:
        stop_event: Event to signal shutdown
        command_handler: Async function to handle commands, returns True to quit
        chat_sender: Async function to send chat messages
    """
    while not stop_event.is_set():
        try:
            line = await asyncio.to_thread(sys.stdin.readline)
        except Exception:
            stop_event.set()
            break
        if not line:
            stop_event.set()
            break
        message = line.rstrip("\n")
        if not message:
            continue
        if message.startswith("/"):
            should_quit = await command_handler(message)
            if should_quit:
                stop_event.set()
                break
            continue
        await chat_sender(message)


async def receive_loop(
    reader: asyncio.StreamReader,
    cipher: crypto.SymmetricCipher,
    stop_event: asyncio.Event,
    message_recorder: Callable[[dict], None],
    file_init_handler: Callable[[dict], None],
    file_chunk_handler: Callable[[dict], None],
    pong_sender: Callable[[], None],
) -> None:
    """Receive encrypted payloads and process messages.

    Args:
        reader: Server input stream
        cipher: Encryption cipher
        stop_event: Event to signal shutdown
        message_recorder: Async function to record chat/system messages
        file_init_handler: Async function to handle file init messages
        file_chunk_handler: Async function to handle file chunk messages
        pong_sender: Async function to send pong responses
    """
    while not stop_event.is_set():
        try:
            message = await protocol.read_message(reader)
        except asyncio.IncompleteReadError:
            if not stop_event.is_set():
                print("Connection closed by server.")
            break
        except Exception as exc:
            print(f"Receive failed: {exc}")
            break

        if message.get("type") != "encrypted":
            print("Received unexpected message from server.")
            continue

        nonce = message.get("nonce")
        ciphertext = message.get("ciphertext")
        if not isinstance(nonce, str) or not isinstance(ciphertext, str):
            print("Malformed encrypted message.")
            continue

        try:
            payload = decrypt_message(cipher, nonce, ciphertext)
        except Exception as exc:
            print(f"Failed to decrypt message: {exc}")
            continue

        ptype = payload.get("type")
        if ptype == "chat":
            await message_recorder(payload)
        elif ptype == "system":
            await message_recorder(payload)
        elif ptype == "file_init":
            await file_init_handler(payload)
        elif ptype == "file_chunk":
            await file_chunk_handler(payload)
        elif ptype == "ping":
            with contextlib.suppress(Exception):
                await pong_sender()
        else:
            print("Unknown payload received.")
