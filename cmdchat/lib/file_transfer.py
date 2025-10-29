"""File transfer management.

This module handles file transfer operations following SOLID principles.
Separated from message handling for better modularity.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from ..crypto import FILE_CHUNK_SIZE
from ..types import FileTransferInfo, FileTransferState

if TYPE_CHECKING:
    from ..types import ClientSession


class FileTransferManager:
    """Manages file transfer operations.

    This class is responsible for:
    - Initiating file transfers
    - Chunking files for transmission
    - Reassembling received chunks
    - Progress tracking

    Example:
        >>> manager = FileTransferManager()
        >>> # Send file
        >>> await manager.send_file(session, Path("file.txt"))
        >>> # Receive chunk
        >>> manager.receive_chunk(file_id, chunk_index, chunk_data)
    """

    def __init__(self) -> None:
        """Initialize the file transfer manager."""
        self._active_transfers: dict[str, FileTransferState] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def generate_file_id(client_name: str, filename: str) -> str:
        """Generate a unique file transfer ID.

        Args:
            client_name: Name of the client sending the file
            filename: Name of the file

        Returns:
            16-character hex file ID
        """
        import os

        data = f"{client_name}{filename}{os.urandom(8).hex()}".encode()
        return hashlib.sha256(data).hexdigest()[:16]

    @staticmethod
    def calculate_chunks(filesize: int, chunk_size: int = FILE_CHUNK_SIZE) -> int:
        """Calculate number of chunks needed for a file.

        Args:
            filesize: Size of file in bytes
            chunk_size: Size of each chunk in bytes

        Returns:
            Number of chunks needed
        """
        return (filesize + chunk_size - 1) // chunk_size

    async def start_transfer(
        self,
        file_id: str,
        filename: str,
        filesize: int,
        total_chunks: int,
        sender: str,
        timestamp: str,
    ) -> None:
        """Start tracking a new file transfer.

        Args:
            file_id: Unique file identifier
            filename: Original filename
            filesize: File size in bytes
            total_chunks: Total number of chunks
            sender: Sender's display name
            timestamp: Transfer start timestamp

        Thread-safe: Yes
        """
        info = FileTransferInfo(
            file_id=file_id,
            filename=filename,
            filesize=filesize,
            total_chunks=total_chunks,
            sender=sender,
            timestamp=timestamp,
        )

        state = FileTransferState(
            info=info,
            chunks={},
            received_count=0,
        )

        async with self._lock:
            self._active_transfers[file_id] = state

    async def add_chunk(
        self,
        file_id: str,
        chunk_index: int,
        chunk_data: bytes,
    ) -> tuple[bool, int, int]:
        """Add a received chunk to a transfer.

        Args:
            file_id: Unique file identifier
            chunk_index: Index of this chunk
            chunk_data: Chunk data bytes

        Returns:
            Tuple of (is_complete, received_count, total_chunks)

        Raises:
            KeyError: If file_id not found

        Thread-safe: Yes
        """
        async with self._lock:
            transfer = self._active_transfers[file_id]

            # Store chunk
            if chunk_index not in transfer.chunks:
                transfer.chunks[chunk_index] = chunk_data
                transfer.received_count += 1

            return (
                transfer.is_complete,
                transfer.received_count,
                transfer.info.total_chunks,
            )

    async def complete_transfer(
        self,
        file_id: str,
        output_path: Path,
    ) -> Path:
        """Complete a file transfer and save to disk.

        Args:
            file_id: Unique file identifier
            output_path: Path to save the file

        Returns:
            Actual path where file was saved

        Raises:
            KeyError: If file_id not found
            ValueError: If transfer is incomplete

        Thread-safe: Yes
        """
        async with self._lock:
            transfer = self._active_transfers.pop(file_id)

            if not transfer.is_complete:
                raise ValueError(
                    f"Transfer incomplete: {transfer.received_count}/"
                    f"{transfer.info.total_chunks} chunks"
                )

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Handle filename conflicts
            final_path = output_path
            counter = 1
            while final_path.exists():
                stem = output_path.stem
                suffix = output_path.suffix
                final_path = output_path.parent / f"{stem}_{counter}{suffix}"
                counter += 1

            # Write chunks in order
            with open(final_path, "wb") as f:
                for i in range(transfer.info.total_chunks):
                    if i in transfer.chunks:
                        f.write(transfer.chunks[i])

            return final_path

    async def cancel_transfer(self, file_id: str) -> None:
        """Cancel an active file transfer.

        Args:
            file_id: Unique file identifier

        Thread-safe: Yes
        """
        async with self._lock:
            self._active_transfers.pop(file_id, None)

    async def get_transfer_info(self, file_id: str) -> FileTransferInfo | None:
        """Get information about an active transfer.

        Args:
            file_id: Unique file identifier

        Returns:
            Transfer info or None if not found

        Thread-safe: Yes
        """
        async with self._lock:
            transfer = self._active_transfers.get(file_id)
            return transfer.info if transfer else None

    async def get_progress(self, file_id: str) -> tuple[int, int] | None:
        """Get transfer progress.

        Args:
            file_id: Unique file identifier

        Returns:
            Tuple of (received_chunks, total_chunks) or None if not found

        Thread-safe: Yes
        """
        async with self._lock:
            transfer = self._active_transfers.get(file_id)
            if transfer:
                return (transfer.received_count, transfer.info.total_chunks)
            return None

    async def get_active_transfer_count(self) -> int:
        """Get number of active transfers.

        Returns:
            Number of active file transfers

        Thread-safe: Yes
        """
        async with self._lock:
            return len(self._active_transfers)
