"""Cryptographic utilities for CMD Chat."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

AES_KEY_SIZE = 32  # 256-bit AES key
AES_NONCE_SIZE = 12  # Recommended nonce size for AES-GCM
PBKDF_SALT_SIZE = 16
PBKDF_ITERATIONS = 200_000


@dataclass(slots=True)
class RSAKeyPair:
    """Container for an RSA private key and its PEM-encoded public key."""

    private_key: rsa.RSAPrivateKey
    public_key_pem: bytes

    @property
    def public_key(self) -> rsa.RSAPublicKey:
        return self.private_key.public_key()


def generate_rsa_keypair(key_size: int = 2048) -> RSAKeyPair:
    """Generate a new RSA keypair for asymmetric operations."""

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return RSAKeyPair(private_key=private_key, public_key_pem=public_pem)


def load_rsa_public_key(public_key_pem: bytes) -> Any:
    """Deserialize a PEM-encoded public key.

    Note: cryptography may return different public key types depending on the
    input (RSA, DSA, EC, X25519, etc.). We annotate as Any to reflect that and
    leave higher-level callers responsible for validating the key type.
    """

    return serialization.load_pem_public_key(public_key_pem)


def encrypt_for_public_key(public_key: rsa.RSAPublicKey, payload: bytes) -> bytes:
    """Encrypt payload bytes with the provided RSA public key."""

    return public_key.encrypt(
        payload,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def decrypt_with_private_key(private_key: rsa.RSAPrivateKey, ciphertext: bytes) -> bytes:
    """Decrypt ciphertext that was encrypted against the private key's public key."""

    return private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def generate_symmetric_key() -> bytes:
    """Create a fresh symmetric key for AES-GCM."""

    return os.urandom(AES_KEY_SIZE)


def generate_salt(size: int = PBKDF_SALT_SIZE) -> bytes:
    """Generate a random salt for key derivation."""

    return os.urandom(size)


def derive_key_from_passphrase(passphrase: str, salt: bytes, *, iterations: int = PBKDF_ITERATIONS) -> bytes:
    """Derive a symmetric key from a user passphrase."""

    if not isinstance(salt, (bytes, bytearray)):
        raise TypeError("Salt must be bytes.")
    if len(salt) < 8:
        raise ValueError("Salt must be at least 8 bytes.")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_SIZE,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt_with_key(key: bytes, plaintext: bytes, *, associated_data: bytes | None = None) -> tuple[bytes, bytes]:
    """Encrypt plaintext using an externally provided symmetric key."""

    cipher = AESGCM(key)
    nonce = os.urandom(AES_NONCE_SIZE)
    ciphertext = cipher.encrypt(nonce, plaintext, associated_data)
    return nonce, ciphertext


def decrypt_with_key(key: bytes, nonce: bytes, ciphertext: bytes, *, associated_data: bytes | None = None) -> bytes:
    """Decrypt ciphertext with a provided symmetric key."""

    cipher = AESGCM(key)
    return cipher.decrypt(nonce, ciphertext, associated_data)


class SymmetricCipher:
    """Helper wrapper around AES-GCM."""

    def __init__(self, key: bytes):
        self._key = key
        self._cipher = AESGCM(key)

    @property
    def key(self) -> bytes:
        return self._key

    def encrypt(self, plaintext: bytes, *, associated_data: bytes | None = None) -> tuple[bytes, bytes]:
        """Encrypt plaintext and return a (nonce, ciphertext) pair."""

        nonce = os.urandom(AES_NONCE_SIZE)
        ciphertext = self._cipher.encrypt(nonce, plaintext, associated_data)
        return nonce, ciphertext

    def decrypt(self, nonce: bytes, ciphertext: bytes, *, associated_data: bytes | None = None) -> bytes:
        """Decrypt ciphertext using the provided nonce."""

        return self._cipher.decrypt(nonce, ciphertext, associated_data)


# File transfer constants
FILE_CHUNK_SIZE = 32768  # 32KB chunks for file transfer
