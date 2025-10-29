"""Client package for CMD Chat.

Provides a clean modular client architecture following SOLID principles.
"""

from .core import CmdChatClient
from .run import run_client

__all__ = ["CmdChatClient", "run_client"]
