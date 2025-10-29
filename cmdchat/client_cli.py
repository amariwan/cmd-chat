"""CMD Chat Client CLI.

Command-line interface for connecting to a CMD Chat server.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from cmdchat.client import run_client
from cmdchat.types import ClientConfig

if TYPE_CHECKING:
    from typing import Optional


def parse_args(argv: Optional[list[str]] = None) -> ClientConfig:
    """Parse CLI arguments for the client.

    Args:
        argv: Command line arguments (None uses sys.argv)

    Returns:
        Client configuration
    """
    parser = argparse.ArgumentParser(description="Connect to a CMD Chat server.")
    parser.add_argument(
        "--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=5050, help="Server port (default: 5050)"
    )
    parser.add_argument(
        "--name",
        default="anonymous",
        help="Display name used in chat (default: anonymous)",
    )
    parser.add_argument(
        "--room", default="lobby", help="Room to join (default: lobby)"
    )
    parser.add_argument("--token", help="Invite or bearer token for authentication.")
    parser.add_argument(
        "--renderer",
        choices=["rich", "minimal", "json"],
        default="rich",
        help="Output renderer style.",
    )
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=200,
        help="Number of messages retained locally (default: 200).",
    )
    parser.add_argument(
        "--quiet-reconnect",
        action="store_true",
        help="Use quiet status messages while reconnecting.",
    )
    parser.add_argument(
        "--history-file", type=Path, help="Optional encrypted history file path."
    )
    parser.add_argument(
        "--history-passphrase", help="Passphrase for encrypting local history."
    )
    parser.add_argument(
        "--tls", action="store_true", help="Enable TLS for server connection."
    )
    parser.add_argument(
        "--tls-insecure",
        action="store_true",
        help="Disable certificate verification (insecure; for testing only).",
    )
    parser.add_argument("--ca-file", help="Custom CA bundle for TLS.")
    args = parser.parse_args(argv)

    history_file = args.history_file
    if history_file and not args.history_passphrase:
        parser.error("--history-file requires --history-passphrase.")

    return ClientConfig(
        host=args.host,
        port=args.port,
        name=args.name,
        room=args.room,
        token=args.token,
        renderer=args.renderer,
        buffer_size=max(10, min(args.buffer_size, 1000)),
        quiet_reconnect=args.quiet_reconnect,
        history_file=history_file,
        history_passphrase=args.history_passphrase,
        tls=args.tls,
        tls_insecure=args.tls_insecure,
        ca_file=args.ca_file,
    )


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point for client CLI.

    Args:
        argv: Command line arguments (None uses sys.argv)
    """
    config = parse_args(argv)
    try:
        asyncio.run(run_client(config))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
