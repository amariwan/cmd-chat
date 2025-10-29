"""Client execution module.

This module provides the entry point for running the client.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .core import CmdChatClient

if TYPE_CHECKING:
    from ..types import ClientConfig


async def run_client(config: ClientConfig) -> None:
    """Entry point for asynchronous client execution.

    Args:
        config: Client configuration
    """
    client = CmdChatClient(config)
    await client.run()
