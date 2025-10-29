"""Chat message handler.

This module handles regular chat messages with rate limiting.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...types import ClientSession
    from ..state import ServerState

# Configuration
RATE_LIMIT_WINDOW = 5.0
RATE_LIMIT_MAX = 12


async def handle_chat_message(
    state: ServerState,
    session: ClientSession,
    payload: dict,
    now: float,
) -> None:
    """Handle chat message.

    Args:
        state: Server state
        session: Client session
        payload: Message payload
        now: Current timestamp

    Enforces rate limiting per client.
    """
    message_text = str(payload.get("message", ""))[:1024]

    # Rate limiting
    window = session.rate_window
    window.append(now)
    while window and now - window[0] > RATE_LIMIT_WINDOW:
        window.popleft()

    if len(window) > RATE_LIMIT_MAX:
        error_msg = state.message_handler.create_system_message(
            "Slow down – message rate limit reached.",
            session.room,
            session.client_id,
        )
        await state.message_handler.encrypt_and_send(session, error_msg)
        return

    sequence = await state.message_handler.next_sequence(session.room)
    chat_msg = state.message_handler.create_chat_message(
        session.name,
        message_text,
        session.room,
        session.client_id,
        sequence=sequence,
    )
    await state.broadcast(chat_msg, room=session.room)
    state.increment_messages()
