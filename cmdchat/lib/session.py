"""Session management.

This module implements the SessionManager following SOLID principles:
- Single Responsibility: Only manages session lifecycle
- Open/Closed: Extensible through composition
- Liskov Substitution: Implements SessionStore protocol
- Interface Segregation: Focused interface
- Dependency Inversion: Depends on abstractions (Protocol)
"""

from __future__ import annotations

import asyncio
from collections import defaultdict

from ..types import ClientID, ClientSession, RoomID


class SessionManager:
    """Manages client sessions with thread-safe operations.

    This class is responsible for:
    - Adding and removing client sessions
    - Room membership tracking
    - Session lookup and retrieval
    - Broadcasting messages to room members

    Example:
        >>> manager = SessionManager()
        >>> # Add session
        >>> await manager.add_session(session)
        >>> # Get room members
        >>> sessions = await manager.get_room_sessions("lobby")
        >>> # Remove session
        >>> removed = await manager.remove_session(client_id)
    """

    def __init__(self) -> None:
        """Initialize the session manager."""
        self._sessions: dict[ClientID, ClientSession] = {}
        self._rooms: dict[RoomID, set[ClientID]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._id_sequence = 0

    async def next_client_id(self) -> ClientID:
        """Generate next unique client ID.

        Returns:
            Unique client identifier

        Thread-safe: Yes
        """
        async with self._lock:
            self._id_sequence += 1
            return self._id_sequence

    async def add_session(self, session: ClientSession) -> None:
        """Add a new client session.

        Args:
            session: Client session to add

        Thread-safe: Yes
        """
        async with self._lock:
            self._sessions[session.client_id] = session
            self._rooms[session.room].add(session.client_id)

    async def remove_session(self, client_id: ClientID) -> ClientSession | None:
        """Remove a client session.

        Args:
            client_id: ID of client to remove

        Returns:
            Removed session or None if not found

        Thread-safe: Yes
        """
        async with self._lock:
            session = self._sessions.pop(client_id, None)
            if session:
                room_clients = self._rooms.get(session.room)
                if room_clients:
                    room_clients.discard(client_id)
                    if not room_clients:
                        del self._rooms[session.room]
            return session

    async def get_session(self, client_id: ClientID) -> ClientSession | None:
        """Get a session by client ID.

        Args:
            client_id: ID of client to retrieve

        Returns:
            Client session or None if not found

        Thread-safe: Yes
        """
        async with self._lock:
            return self._sessions.get(client_id)

    async def get_room_sessions(self, room: RoomID) -> list[ClientSession]:
        """Get all sessions in a room.

        Args:
            room: Room identifier

        Returns:
            List of client sessions in the room

        Thread-safe: Yes
        """
        async with self._lock:
            client_ids = list(self._rooms.get(room, set()))
            return [
                self._sessions[cid]
                for cid in client_ids
                if cid in self._sessions
            ]

    async def move_session(
        self,
        session: ClientSession,
        new_room: RoomID,
    ) -> RoomID:
        """Move a client session to a different room.

        Args:
            session: Client session to move
            new_room: Target room identifier

        Returns:
            Previous room identifier

        Thread-safe: Yes
        """
        async with self._lock:
            old_room = session.room

            if old_room == new_room:
                return old_room

            # Remove from old room
            old_room_clients = self._rooms.get(old_room)
            if old_room_clients:
                old_room_clients.discard(session.client_id)
                if not old_room_clients:
                    del self._rooms[old_room]

            # Add to new room
            self._rooms[new_room].add(session.client_id)
            session.room = new_room

            return old_room

    async def get_all_sessions(self) -> list[ClientSession]:
        """Get all active sessions.

        Returns:
            List of all client sessions

        Thread-safe: Yes
        """
        async with self._lock:
            return list(self._sessions.values())

    async def get_session_count(self) -> int:
        """Get total number of active sessions.

        Returns:
            Number of active sessions

        Thread-safe: Yes
        """
        async with self._lock:
            return len(self._sessions)

    async def get_room_count(self) -> int:
        """Get total number of active rooms.

        Returns:
            Number of rooms with at least one client

        Thread-safe: Yes
        """
        async with self._lock:
            return len(self._rooms)

    async def get_room_names(self) -> list[RoomID]:
        """Get list of all active room names.

        Returns:
            List of room identifiers

        Thread-safe: Yes
        """
        async with self._lock:
            return list(self._rooms.keys())
