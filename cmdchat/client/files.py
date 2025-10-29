"""File transfer functionality for client.

This module handles sending and receiving files via encrypted chunks.
"""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import TYPE_CHECKING

from .. import crypto
from ..lib import FileTransferManager

if TYPE_CHECKING:
    from collections.abc import Callable


async def send_file(
    filepath: str,
    current_name: str,
    send_encrypted_func: Callable[[dict], None],
) -> None:
    """Send a file via encrypted chunks.

    Args:
        filepath: Path to file to send
        current_name: Current client name
        send_encrypted_func: Async function to send encrypted messages
    """
    path = Path(filepath).expanduser()
    if not path.is_file():
        print(f"[error] File not found: {filepath}")
        return

    filesize = path.stat().st_size
    if filesize > 10 * 1024 * 1024:  # 10MB limit
        print("[error] File too large (max 10MB)")
        return

    file_manager = FileTransferManager()

    # Generate file ID
    file_id = file_manager.generate_file_id(current_name, path.name)
    total_chunks = file_manager.calculate_chunks(filesize)

    print(f"[file] Sending {path.name} ({filesize} bytes, {total_chunks} chunks)...")

    # Send file init
    await send_encrypted_func(
        {
            "type": "file_init",
            "file_id": file_id,
            "filename": path.name,
            "filesize": filesize,
            "total_chunks": total_chunks,
        }
    )

    # Send chunks
    try:
        with open(path, "rb") as f:
            for chunk_index in range(total_chunks):
                chunk_data = f.read(crypto.FILE_CHUNK_SIZE)
                is_final = chunk_index == total_chunks - 1

                await send_encrypted_func(
                    {
                        "type": "file_chunk",
                        "file_id": file_id,
                        "chunk_index": chunk_index,
                        "chunk_data": base64.b64encode(chunk_data).decode("ascii"),
                        "is_final": is_final,
                    }
                )

                if (chunk_index + 1) % 10 == 0 or is_final:
                    progress = ((chunk_index + 1) / total_chunks) * 100
                    print(
                        f"[file] Progress: {progress:.1f}% ({chunk_index + 1}/{total_chunks} chunks)"
                    )

                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.01)

        print(f"[file] Transfer complete: {path.name}")
    except Exception as exc:
        print(f"[error] File transfer failed: {exc}")


async def handle_file_init(
    payload: dict,
    file_manager: FileTransferManager,
) -> None:
    """Handle incoming file transfer initialization.

    Args:
        payload: File init message payload
        file_manager: File transfer manager instance
    """
    sender = payload.get("sender", "?")
    file_id = payload.get("file_id", "")
    filename = payload.get("filename", "unknown")
    filesize = payload.get("filesize", 0)
    total_chunks = payload.get("total_chunks", 0)
    timestamp = payload.get("timestamp", "")

    if not file_id:
        return

    # Start tracking transfer
    await file_manager.start_transfer(
        file_id,
        filename,
        filesize,
        total_chunks,
        sender,
        timestamp,
    )

    print(
        f"[file] {sender} is sending {filename} ({filesize} bytes, {total_chunks} chunks)"
    )


async def handle_file_chunk(
    payload: dict,
    file_manager: FileTransferManager,
) -> None:
    """Handle incoming file chunk.

    Args:
        payload: File chunk message payload
        file_manager: File transfer manager instance
    """
    file_id = payload.get("file_id", "")
    chunk_index = payload.get("chunk_index", 0)
    chunk_data_b64 = payload.get("chunk_data", "")
    is_final = payload.get("is_final", False)

    # Get transfer info
    transfer_info = await file_manager.get_transfer_info(file_id)
    if not transfer_info:
        return

    try:
        chunk_data = base64.b64decode(chunk_data_b64)

        # Add chunk to transfer
        is_complete, received, total = await file_manager.add_chunk(
            file_id,
            chunk_index,
            chunk_data,
        )

        # Show progress
        if received % 10 == 0 or is_final:
            progress = (received / total) * 100
            print(
                f"[file] Receiving {transfer_info.filename}: {progress:.1f}% ({received}/{total} chunks)"
            )

        # Save file when complete
        if is_complete:
            downloads_dir = Path.home() / "Downloads" / "cmdchat"
            output_path = downloads_dir / transfer_info.filename

            final_path = await file_manager.complete_transfer(file_id, output_path)
            print(f"[file] Saved to: {final_path}")

    except Exception as exc:
        print(f"[error] File chunk processing failed: {exc}")
        await file_manager.cancel_transfer(file_id)
