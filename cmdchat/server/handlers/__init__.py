"""Message handlers for different message types.

This package provides specialized handlers for different message types
following the Single Responsibility Principle.
"""

from .chat import handle_chat_message
from .files import handle_file_chunk, handle_file_init
from .system import handle_rename, handle_switch_room, handle_system_message

__all__ = [
    "handle_chat_message",
    "handle_file_chunk",
    "handle_file_init",
    "handle_rename",
    "handle_switch_room",
    "handle_system_message",
]
