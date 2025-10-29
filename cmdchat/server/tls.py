"""TLS/SSL context creation for secure server connections.

This module provides utilities for setting up SSL/TLS encryption
for the server.
"""

from __future__ import annotations

import ssl
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def create_ssl_context(
    certfile: str | None = None,
    keyfile: str | None = None,
) -> ssl.SSLContext | None:
    """Create SSL context for server if certificates are provided.

    Args:
        certfile: Path to TLS certificate file (PEM)
        keyfile: Path to TLS private key file (PEM)

    Returns:
        SSL context if both certfile and keyfile provided, None otherwise
    """
    if not certfile or not keyfile:
        return None

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    return ssl_context
