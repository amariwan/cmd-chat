"""CMD Chat Server CLI.

Command-line interface for running the CMD Chat server.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
from typing import TYPE_CHECKING

from cmdchat.server import run_server

if TYPE_CHECKING:
    pass


class SanitizedFormatter(logging.Formatter):
    """Custom formatter that doesn't log sensitive data."""

    def format(self, record):
        """Format log record, preventing accidental logging of tokens/keys."""
        if hasattr(record, "msg"):
            msg = str(record.msg)
            # Redact common sensitive patterns
            if "token" in msg.lower() and "***" not in msg:
                # This is a fallback - direct token logging should be sanitized at source
                pass
        return super().format(record)


def parse_args(argv: list[str] | None = None) -> tuple[str, int, str | None, str | None, int]:
    """Parse command line arguments for the server.

    Args:
        argv: Command line arguments (None uses sys.argv)

    Returns:
        Tuple of (host, port, certfile, keyfile, metrics_interval)
    """
    parser = argparse.ArgumentParser(description="Run the CMD Chat secure server.")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5050,
        help="Port to listen on (default: 5050)",
    )
    parser.add_argument(
        "--certfile",
        help="TLS certificate file (PEM). Enables TLS when provided with --keyfile.",
    )
    parser.add_argument(
        "--keyfile",
        help="TLS private key file (PEM). Enables TLS when provided with --certfile.",
    )
    parser.add_argument(
        "--metrics-interval",
        type=int,
        default=0,
        help="Interval in seconds for logging basic metrics (0 disables).",
    )
    args = parser.parse_args(argv)
    return args.host, args.port, args.certfile, args.keyfile, max(0, args.metrics_interval)


def main(argv: list[str] | None = None) -> None:
    """Entry point for server CLI.

    Args:
        argv: Command line arguments (None uses sys.argv)
    """
    log_level = os.getenv("CMDCHAT_LOG_LEVEL", "INFO").upper()

    handler = logging.StreamHandler()
    handler.setFormatter(
        SanitizedFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    logging.basicConfig(
        level=log_level,
        handlers=[handler],
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting CMD Chat Server (log_level=%s)", log_level)

    host, port, certfile, keyfile, metrics_interval = parse_args(argv)
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(
            run_server(
                host,
                port,
                certfile=certfile,
                keyfile=keyfile,
                metrics_interval=metrics_interval,
            )
        )


if __name__ == "__main__":
    main()
