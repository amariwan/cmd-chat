"""File transfer message handlers.

This module handles file transfer initialization and chunk transmission.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...types import ClientSession
    from ..state import ServerState

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def handle_file_init(
    state: ServerState,
    session: ClientSession,
    payload: dict,
) -> None:
    """Handle file transfer initialization.

    Args:
        state: Server state
        session: Client session
        payload: Message payload with file metadata
    """
    file_id = str(payload.get("file_id", ""))
    filename = str(payload.get("filename", "unknown"))[:256]
    filesize = int(payload.get("filesize", 0))
    total_chunks = int(payload.get("total_chunks", 0))

    if not file_id or filesize <= 0 or filesize > MAX_FILE_SIZE:
        error_msg = state.message_handler.create_system_message(
            f"File transfer rejected: invalid size (max {MAX_FILE_SIZE // 1024 // 1024}MB).",
            session.room,
            session.client_id,
        )
        await state.message_handler.encrypt_and_send(session, error_msg)
        return

    # Notify room about file transfer
    init_msg = state.message_handler.create_file_init_message(
        session.name,
        file_id,
        filename,
        filesize,
        total_chunks,
        session.room,
        session.client_id,
    )
    await state.broadcast(init_msg, room=session.room)


async def handle_file_chunk(
    state: ServerState,
    session: ClientSession,
    payload: dict,
) -> None:
    """Handle file chunk transmission.

    Args:
        state: Server state
        session: Client session
        payload: Message payload with file chunk data
    """
    file_id = str(payload.get("file_id", ""))
    chunk_index = int(payload.get("chunk_index", 0))
    chunk_data = str(payload.get("chunk_data", ""))
    is_final = bool(payload.get("is_final", False))

    if not file_id:
        return

    chunk_msg = state.message_handler.create_file_chunk_message(
        session.name,
        file_id,
        chunk_index,
        chunk_data,
        is_final,
        session.room,
        session.client_id,
    )
    await state.broadcast(chunk_msg, room=session.room, exclude=session.client_id)

    if is_final:
        complete_msg = state.message_handler.create_system_message(
            f"{session.name} completed file transfer.",
            session.room,
            session.client_id,
        )
        await state.broadcast(complete_msg, room=session.room)
