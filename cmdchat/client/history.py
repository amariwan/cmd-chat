"""Encrypted history storage for client.

This module provides local encrypted transcript storage using
AES encryption with a user-provided passphrase.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import TYPE_CHECKING

from .. import crypto

if TYPE_CHECKING:
    pass


class EncryptedHistory:
    """Local optional encrypted transcript storage.

    Uses AES-GCM encryption with a key derived from a user passphrase.
    """

    def __init__(self, path: Path, passphrase: str):
        """Initialize encrypted history.

        Args:
            path: Path to history file
            passphrase: User passphrase for encryption
        """
        self.path = path
        self.passphrase = passphrase
        self.salt: bytes | None = None
        self.messages: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Load and decrypt history from disk."""
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text())
            self.salt = base64.b64decode(raw["salt"])
            nonce = base64.b64decode(raw["nonce"])
            ciphertext = base64.b64decode(raw["ciphertext"])
            key = crypto.derive_key_from_passphrase(self.passphrase, self.salt)
            plaintext = crypto.decrypt_with_key(key, nonce, ciphertext)
            self.messages = json.loads(plaintext.decode("utf-8"))
        except Exception:
            # If history cannot be decoded we fall back to a blank history.
            self.salt = None
            self.messages = []

    def append(self, payload: dict) -> None:
        """Append a message to history.

        Args:
            payload: Message payload to append
        """
        self.messages.append(payload)
        self._persist()

    def _persist(self) -> None:
        """Encrypt and save history to disk."""
        if self.salt is None:
            self.salt = crypto.generate_salt()
        key = crypto.derive_key_from_passphrase(self.passphrase, self.salt)
        data = json.dumps(
            self.messages, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        nonce, ciphertext = crypto.encrypt_with_key(key, data)
        envelope = {
            "salt": base64.b64encode(self.salt).decode("ascii"),
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(envelope, indent=2))
