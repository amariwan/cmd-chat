"""Server state container with dependency injection.

This module provides the central ServerState class that coordinates
between different managers following SOLID principles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..lib import MessageHandler, SessionManager

if TYPE_CHECKING:
    from ..types import ClientID, RoomID


@dataclass
class ServerState:
    """Server state container with dependency injection.

    This class coordinates between different managers:
    - SessionManager: Client session lifecycle
    - MessageHandler: Message encryption/routing
    - Metrics: Server statistics

    Follows SOLID principles with focused responsibilities.
    """

    session_mgr: SessionManager = field(default_factory=SessionManager)
    message_handler: MessageHandler = field(default_factory=MessageHandler)
    metrics: dict[str, float] = field(default_factory=lambda: {"messages": 0})
    shutdown: bool = field(default=False)

    async def set_shutdown(self) -> None:
        """Set the shutdown flag."""
        object.__setattr__(self, 'shutdown', True)

    def increment_messages(self) -> None:
        """Increment message counter."""
        self.metrics["messages"] = self.metrics.get("messages", 0) + 1

    async def connected_users(self) -> int:
        """Get number of connected users."""
        return await self.session_mgr.get_session_count()

    async def broadcast(
        self,
        payload: dict,
        *,
        room: RoomID,
        exclude: ClientID | None = None,
    ) -> None:
        """Broadcast message to all room members.

        Args:
            payload: Message payload to send
            room: Target room
            exclude: Optional client ID to exclude

        Handles stale connections gracefully.
        """
        stale_clients: list[ClientID] = []
        recipients = await self.session_mgr.get_room_sessions(room)

        for session in recipients:
            if exclude is not None and session.client_id == exclude:
                continue

            try:
                await self.message_handler.encrypt_and_send(session, payload)
            except Exception:
                stale_clients.append(session.client_id)

        # Clean up stale connections
        for client_id in stale_clients:
            await self.session_mgr.remove_session(client_id)
