"""System message handlers.

This module handles system messages, renames, and room switches.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils import sanitize_name, sanitize_room

if TYPE_CHECKING:
    from ...types import ClientSession
    from ..state import ServerState


async def handle_system_message(
    state: ServerState,
    session: ClientSession,
    payload: dict,
) -> None:
    """Handle system message.

    Args:
        state: Server state
        session: Client session
        payload: Message payload
    """
    note = str(payload.get("message", ""))
    system_msg = state.message_handler.create_system_message(
        note,
        session.room,
        session.client_id,
    )
    await state.broadcast(system_msg, room=session.room)


async def handle_rename(
    state: ServerState,
    session: ClientSession,
    payload: dict,
) -> None:
    """Handle client rename request.

    Args:
        state: Server state
        session: Client session
        payload: Message payload with new name
    """
    new_name = sanitize_name(str(payload.get("name", "")))
    if new_name and new_name != session.name:
        old_name = session.name
        session.name = new_name
        rename_msg = state.message_handler.create_system_message(
            f"{old_name} is now known as {new_name}.",
            session.room,
            session.client_id,
        )
        await state.broadcast(rename_msg, room=session.room)


async def handle_switch_room(
    state: ServerState,
    session: ClientSession,
    payload: dict,
) -> None:
    """Handle room switch request.

    Args:
        state: Server state
        session: Client session
        payload: Message payload with new room
    """
    new_room = sanitize_room(str(payload.get("room", "")))
    if not new_room or new_room == session.room:
        return

    old_room = session.room

    # Notify old room
    leave_msg = state.message_handler.create_system_message(
        f"{session.name} left the room.",
        old_room,
        session.client_id,
    )
    await state.broadcast(leave_msg, room=old_room, exclude=session.client_id)

    # Move client
    await state.session_mgr.move_session(session, new_room)

    # Notify client
    joined_msg = state.message_handler.create_system_message(
        f"Joined room {new_room}.",
        new_room,
        session.client_id,
    )
    await state.message_handler.encrypt_and_send(session, joined_msg)

    # Notify new room
    announce_msg = state.message_handler.create_system_message(
        f"{session.name} joined the room.",
        new_room,
        session.client_id,
    )
    await state.broadcast(announce_msg, room=new_room, exclude=session.client_id)
