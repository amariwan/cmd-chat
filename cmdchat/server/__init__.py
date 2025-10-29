"""Server package for CMD Chat.

Provides a clean modular server architecture following SOLID principles.
"""

from .run import run_server
from .state import ServerState

__all__ = ["run_server", "ServerState"]
