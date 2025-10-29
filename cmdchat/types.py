"""Type definitions for CMD Chat.

This module contains all type hints, protocols, and type aliases
to ensure type safety throughout the application.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypedDict, Union

if TYPE_CHECKING:
    import asyncio
    from collections import deque

    from .crypto import SymmetricCipher


# ============================================================================
# Enums
# ============================================================================


class MessageType(str, Enum):
    """Types of messages in the protocol."""

    HANDSHAKE = "handshake"
    HANDSHAKE_OK = "handshake_ok"
    HANDSHAKE_ERROR = "handshake_error"
    ENCRYPTED = "encrypted"
    CHAT = "chat"
    SYSTEM = "system"
    PING = "ping"
    PONG = "pong"
    RENAME = "rename"
    SWITCH_ROOM = "switch_room"
    FILE_INIT = "file_init"
    FILE_CHUNK = "file_chunk"


class RendererType(str, Enum):
    """Supported message renderers."""

    RICH = "rich"
    MINIMAL = "minimal"
    JSON = "json"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ============================================================================
# TypedDicts for JSON payloads
# ============================================================================


class HandshakePayload(TypedDict, total=False):
    """Client handshake message."""

    type: Literal["handshake"]
    public_key: str
    name: str
    room: str
    token: str | None
    renderer: str
    buffer_size: int


class HandshakeOkPayload(TypedDict):
    """Server handshake response."""

    type: Literal["handshake_ok"]
    client_id: int
    room: str
    renderer: str
    buffer_size: int
    heartbeat_interval: float
    nonce_size: int
    encrypted_key: str


class HandshakeErrorPayload(TypedDict):
    """Server handshake error."""

    type: Literal["handshake_error"]
    reason: str


class EncryptedEnvelope(TypedDict):
    """Wrapper for encrypted messages."""

    type: Literal["encrypted"]
    nonce: str
    ciphertext: str


class ChatPayload(TypedDict, total=False):
    """Chat message payload."""

    type: Literal["chat"]
    sender: str
    message: str
    client_id: int
    room: str
    timestamp: str
    sequence: int


class SystemPayload(TypedDict, total=False):
    """System message payload."""

    type: Literal["system"]
    message: str
    client_id: int
    room: str
    timestamp: str


class PingPayload(TypedDict):
    """Heartbeat ping."""

    type: Literal["ping"]
    timestamp: str


class PongPayload(TypedDict):
    """Heartbeat pong."""

    type: Literal["pong"]


class RenamePayload(TypedDict):
    """Rename request."""

    type: Literal["rename"]
    name: str


class SwitchRoomPayload(TypedDict):
    """Room switch request."""

    type: Literal["switch_room"]
    room: str


class FileInitPayload(TypedDict):
    """File transfer initialization."""

    type: Literal["file_init"]
    sender: str
    file_id: str
    filename: str
    filesize: int
    total_chunks: int
    client_id: int
    room: str
    timestamp: str


class FileChunkPayload(TypedDict):
    """File transfer chunk."""

    type: Literal["file_chunk"]
    sender: str
    file_id: str
    chunk_index: int
    chunk_data: str
    is_final: bool
    client_id: int
    room: str
    timestamp: str


# Union of all payload types
Payload = Union[
    ChatPayload,
    SystemPayload,
    PingPayload,
    PongPayload,
    RenamePayload,
    SwitchRoomPayload,
    FileInitPayload,
    FileChunkPayload,
]

Message = Union[
    HandshakePayload,
    HandshakeOkPayload,
    HandshakeErrorPayload,
    EncryptedEnvelope,
]


# ============================================================================
# Protocols (Interfaces)
# ============================================================================


class Cipher(Protocol):
    """Interface for symmetric encryption."""

    def encrypt(self, plaintext: bytes) -> tuple[bytes, bytes]:
        """Encrypt plaintext, returning (nonce, ciphertext)."""
        ...

    def decrypt(self, nonce: bytes, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext using nonce."""
        ...


class MessageRenderer(Protocol):
    """Interface for message rendering."""

    def render_chat(self, payload: ChatPayload) -> str:
        """Render a chat message."""
        ...

    def render_system(self, payload: SystemPayload) -> str:
        """Render a system message."""
        ...


class SessionStore(Protocol):
    """Interface for session storage."""

    async def add_session(self, session: ClientSession) -> None:
        """Add a new client session."""
        ...

    async def remove_session(self, client_id: int) -> ClientSession | None:
        """Remove and return a session."""
        ...

    async def get_session(self, client_id: int) -> ClientSession | None:
        """Get a session by ID."""
        ...

    async def get_room_sessions(self, room: str) -> list[ClientSession]:
        """Get all sessions in a room."""
        ...


# ============================================================================
# Dataclasses
# ============================================================================


@dataclass(frozen=True, slots=True)
class ServerConfig:
    """Server configuration."""

    host: str
    port: int
    certfile: str | None
    keyfile: str | None
    metrics_interval: int
    max_message_bytes: int = 4096
    max_file_size: int = 10 * 1024 * 1024
    rate_limit_window: float = 5.0
    rate_limit_max: int = 12
    heartbeat_interval: float = 15.0
    heartbeat_timeout: float = 45.0


@dataclass(frozen=True, slots=True)
class ClientConfig:
    """Client configuration."""

    host: str
    port: int
    name: str
    room: str
    token: str | None
    renderer: RendererType
    buffer_size: int
    quiet_reconnect: bool
    history_file: str | None
    history_passphrase: str | None
    tls: bool
    tls_insecure: bool
    ca_file: str | None


@dataclass(slots=True)
class ClientSession:
    """Active client connection session."""

    client_id: int
    name: str
    room: str
    writer: asyncio.StreamWriter
    cipher: SymmetricCipher
    renderer: str
    buffer_size: int
    seq: int = 0
    last_seen: float = 0.0
    last_sequence: int = 0
    rate_window: deque[float] | None = None
    file_transfers: dict[str, dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        """Initialize mutable fields."""
        if self.rate_window is None:
            from collections import deque
            object.__setattr__(self, 'rate_window', deque())
        if self.file_transfers is None:
            object.__setattr__(self, 'file_transfers', {})


@dataclass(frozen=True, slots=True)
class FileTransferInfo:
    """File transfer metadata."""

    file_id: str
    filename: str
    filesize: int
    total_chunks: int
    sender: str
    timestamp: str


@dataclass(slots=True)
class FileTransferState:
    """State of an active file transfer."""

    info: FileTransferInfo
    chunks: dict[int, bytes]
    received_count: int = 0

    @property
    def is_complete(self) -> bool:
        """Check if all chunks have been received."""
        return self.received_count == self.info.total_chunks


# ============================================================================
# Type Aliases
# ============================================================================

# Network types
HostAddress = str
Port = int

# Identifiers
ClientID = int
RoomID = str
FileID = str
TokenValue = str

# Crypto types
RSAKeySize = Literal[2048, 4096]
AESKeyBytes = bytes
Nonce = bytes
Ciphertext = bytes

# Time
Timestamp = str  # ISO 8601 format
Seconds = float | int
