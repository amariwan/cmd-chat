"""TLS/SSL context creation for secure client connections.

This module provides utilities for setting up SSL/TLS encryption
for the client.
"""

from __future__ import annotations

import ssl
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional


def create_ssl_context(
    tls_enabled: bool,
    ca_file: Optional[str] = None,
    tls_insecure: bool = False,
) -> Optional[ssl.SSLContext]:
    """Create SSL context for client if TLS is enabled.

    Args:
        tls_enabled: Whether TLS is enabled
        ca_file: Optional custom CA bundle file
        tls_insecure: Whether to disable certificate verification (insecure)

    Returns:
        SSL context if TLS enabled, None otherwise
    """
    if not tls_enabled:
        return None

    if ca_file:
        context = ssl.create_default_context(cafile=ca_file)
    else:
        context = ssl.create_default_context()

    if tls_insecure:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    return context
