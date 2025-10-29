"""Message handling logic.

This module implements message processing and routing following SOLID principles.
Separated from transport layer for better testability and maintainability.
"""

from __future__ import annotations

import asyncio
import base64
import json
from typing import TYPE_CHECKING, Any

from ..utils import utc_timestamp

if TYPE_CHECKING:
    from ..types import ClientSession, Payload


class MessageHandler:
    """Handles message creation, serialization, and encryption.

    This class is responsible for:
    - Creating properly formatted messages
    - Encrypting messages for transmission
    - Decrypting received messages
    - Message validation

    Example:
        >>> handler = MessageHandler()
        >>> payload = handler.create_chat_message("alice", "Hello!", "lobby")
        >>> encrypted = await handler.encrypt_payload(session, payload)
    """

    def __init__(self) -> None:
        """Initialize the message handler."""
        self._sequence_counters: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def next_sequence(self, room: str) -> int:
        """Get next sequence number for a room.

        Args:
            room: Room identifier

        Returns:
            Next sequence number

        Thread-safe: Yes
        """
        async with self._lock:
            self._sequence_counters[room] = self._sequence_counters.get(room, 0) + 1
            return self._sequence_counters[room]

    def create_chat_message(
        self,
        sender: str,
        message: str,
        room: str,
        client_id: int,
        *,
        sequence: int | None = None,
    ) -> dict[str, Any]:
        """Create a chat message payload.

        Args:
            sender: Sender's display name
            message: Message content
            room: Room identifier
            client_id: Sender's client ID
            sequence: Optional message sequence number

        Returns:
            Chat message payload
        """
        payload = {
            "type": "chat",
            "sender": sender,
            "message": message,
            "client_id": client_id,
            "room": room,
            "timestamp": utc_timestamp(),
        }

        if sequence is not None:
            payload["sequence"] = sequence

        return payload

    def create_system_message(
        self,
        message: str,
        room: str,
        client_id: int,
    ) -> dict[str, Any]:
        """Create a system message payload.

        Args:
            message: System message content
            room: Room identifier
            client_id: Related client ID

        Returns:
            System message payload
        """
        return {
            "type": "system",
            "message": message,
            "client_id": client_id,
            "room": room,
            "timestamp": utc_timestamp(),
        }

    def create_ping_message(self) -> dict[str, Any]:
        """Create a heartbeat ping message.

        Returns:
            Ping message payload
        """
        return {
            "type": "ping",
            "timestamp": utc_timestamp(),
        }

    def create_file_init_message(
        self,
        sender: str,
        file_id: str,
        filename: str,
        filesize: int,
        total_chunks: int,
        room: str,
        client_id: int,
    ) -> dict[str, Any]:
        """Create a file transfer initialization message.

        Args:
            sender: Sender's display name
            file_id: Unique file identifier
            filename: Original filename
            filesize: File size in bytes
            total_chunks: Total number of chunks
            room: Room identifier
            client_id: Sender's client ID

        Returns:
            File init message payload
        """
        return {
            "type": "file_init",
            "sender": sender,
            "file_id": file_id,
            "filename": filename,
            "filesize": filesize,
            "total_chunks": total_chunks,
            "client_id": client_id,
            "room": room,
            "timestamp": utc_timestamp(),
        }

    def create_file_chunk_message(
        self,
        sender: str,
        file_id: str,
        chunk_index: int,
        chunk_data: str,
        is_final: bool,
        room: str,
        client_id: int,
    ) -> dict[str, Any]:
        """Create a file chunk message.

        Args:
            sender: Sender's display name
            file_id: Unique file identifier
            chunk_index: Index of this chunk
            chunk_data: Base64-encoded chunk data
            is_final: Whether this is the last chunk
            room: Room identifier
            client_id: Sender's client ID

        Returns:
            File chunk message payload
        """
        return {
            "type": "file_chunk",
            "sender": sender,
            "file_id": file_id,
            "chunk_index": chunk_index,
            "chunk_data": chunk_data,
            "is_final": is_final,
            "client_id": client_id,
            "room": room,
            "timestamp": utc_timestamp(),
        }

    async def encrypt_and_send(
        self,
        session: ClientSession,
        payload: dict[str, Any],
    ) -> None:
        """Encrypt a payload and send to client.

        Args:
            session: Target client session
            payload: Unencrypted payload

        Raises:
            Exception: If encryption or sending fails
        """
        from ..protocol import write_message

        # Serialize payload
        message_bytes = json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")

        # Encrypt
        nonce, ciphertext = session.cipher.encrypt(message_bytes)

        # Create envelope
        envelope = {
            "type": "encrypted",
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        }

        # Send
        await write_message(session.writer, envelope)

    def decrypt_payload(
        self,
        session: ClientSession,
        nonce_b64: str,
        ciphertext_b64: str,
    ) -> dict[str, Any]:
        """Decrypt an encrypted payload.

        Args:
            session: Client session with cipher
            nonce_b64: Base64-encoded nonce
            ciphertext_b64: Base64-encoded ciphertext

        Returns:
            Decrypted payload

        Raises:
            Exception: If decryption or parsing fails
        """
        # Decode
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ciphertext_b64)

        # Decrypt
        plaintext = session.cipher.decrypt(nonce, ciphertext)

        # Parse
        return json.loads(plaintext.decode("utf-8"))
