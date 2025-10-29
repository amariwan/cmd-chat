"""I/O operations for client connections.

This module handles the encryption handshake and message
encryption/decryption for the client.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
from typing import TYPE_CHECKING

from .. import crypto, protocol

if TYPE_CHECKING:
    from typing import Optional

    from ..types import ClientConfig


async def perform_handshake(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    config: ClientConfig,
    current_name: str,
    current_room: str,
) -> tuple[crypto.SymmetricCipher, dict]:
    """Perform RSA/AES handshake with server.

    Args:
        reader: Server input stream
        writer: Server output stream
        config: Client configuration
        current_name: Current client name
        current_room: Current room

    Returns:
        Tuple of (cipher, handshake_response)

    Raises:
        RuntimeError: On handshake failure
    """
    rsa_pair = crypto.generate_rsa_keypair()

    handshake_payload = {
        "type": "handshake",
        "public_key": rsa_pair.public_key_pem.decode("ascii"),
        "name": current_name,
        "room": current_room,
        "token": config.token,
        "renderer": config.renderer,
        "buffer_size": config.buffer_size,
    }
    await protocol.write_message(writer, handshake_payload)

    response = await protocol.read_message(reader)
    if response.get("type") == "handshake_error":
        reason = response.get("reason", "unknown")
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()
        raise RuntimeError(f"Handshake rejected ({reason}).")
    if response.get("type") != "handshake_ok":
        raise RuntimeError("Unexpected handshake response from server.")

    encrypted_key = response.get("encrypted_key")
    if not isinstance(encrypted_key, str):
        raise RuntimeError("Handshake missing encrypted session key.")

    symmetric_key = crypto.decrypt_with_private_key(
        rsa_pair.private_key, base64.b64decode(encrypted_key)
    )
    cipher = crypto.SymmetricCipher(symmetric_key)

    return cipher, response


async def send_encrypted(
    writer: asyncio.StreamWriter,
    cipher: crypto.SymmetricCipher,
    payload: dict,
    send_lock: asyncio.Lock,
) -> None:
    """Encrypt payload and send to server.

    Args:
        writer: Server output stream
        cipher: Encryption cipher
        payload: Message payload to send
        send_lock: Lock to prevent concurrent writes

    Raises:
        RuntimeError: If not connected
    """
    if not cipher or not writer:
        raise RuntimeError("Client is not connected.")

    message_bytes = json.dumps(
        payload, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    nonce, ciphertext = cipher.encrypt(message_bytes)
    envelope = {
        "type": "encrypted",
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }
    async with send_lock:
        await protocol.write_message(writer, envelope)


def decrypt_message(
    cipher: crypto.SymmetricCipher,
    nonce: str,
    ciphertext: str,
) -> dict:
    """Decrypt an encrypted message.

    Args:
        cipher: Encryption cipher
        nonce: Base64-encoded nonce
        ciphertext: Base64-encoded ciphertext

    Returns:
        Decrypted payload

    Raises:
        Exception: On decryption failure
    """
    plaintext = cipher.decrypt(
        base64.b64decode(nonce),
        base64.b64decode(ciphertext),
    )
    return json.loads(plaintext.decode("utf-8"))
