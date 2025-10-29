"""Tests for crypto module."""


import pytest

from cmdchat import crypto


class TestKeyGeneration:
    """Test cryptographic key generation."""

    def test_generate_symmetric_key(self):
        """Test symmetric key generation."""
        key = crypto.generate_symmetric_key()
        assert isinstance(key, bytes)
        assert len(key) == crypto.AES_KEY_SIZE

    def test_generate_salt(self):
        """Test salt generation."""
        salt = crypto.generate_salt()
        assert isinstance(salt, bytes)
        assert len(salt) == crypto.PBKDF_SALT_SIZE

    def test_generate_rsa_keypair(self):
        """Test RSA keypair generation."""
        pair = crypto.generate_rsa_keypair()
        assert pair.public_key is not None
        assert pair.private_key is not None
        assert pair.public_key_pem is not None
        assert isinstance(pair.public_key_pem, bytes)


class TestSymmetricEncryption:
    """Test symmetric encryption/decryption."""

    def test_symmetric_cipher_encrypt_decrypt(self):
        """Test symmetric encryption and decryption."""
        key = crypto.generate_symmetric_key()
        cipher = crypto.SymmetricCipher(key)

        plaintext = b"Hello, World!"
        nonce, ciphertext = cipher.encrypt(plaintext)

        assert isinstance(nonce, bytes)
        assert isinstance(ciphertext, bytes)
        assert len(nonce) == crypto.AES_NONCE_SIZE
        assert ciphertext != plaintext

        decrypted = cipher.decrypt(nonce, ciphertext)
        assert decrypted == plaintext

    def test_symmetric_cipher_different_nonces(self):
        """Test that encryption produces different nonces."""
        key = crypto.generate_symmetric_key()
        cipher = crypto.SymmetricCipher(key)

        plaintext = b"Same message"
        nonce1, ciphertext1 = cipher.encrypt(plaintext)
        nonce2, ciphertext2 = cipher.encrypt(plaintext)

        assert nonce1 != nonce2
        assert ciphertext1 != ciphertext2

    def test_symmetric_cipher_invalid_nonce(self):
        """Test decryption with invalid nonce."""
        key = crypto.generate_symmetric_key()
        cipher = crypto.SymmetricCipher(key)

        plaintext = b"Test"
        nonce, ciphertext = cipher.encrypt(plaintext)

        # Tamper with nonce
        bad_nonce = b"x" * len(nonce)
        with pytest.raises(Exception):
            cipher.decrypt(bad_nonce, ciphertext)

    def test_symmetric_cipher_invalid_ciphertext(self):
        """Test decryption with invalid ciphertext."""
        key = crypto.generate_symmetric_key()
        cipher = crypto.SymmetricCipher(key)

        plaintext = b"Test"
        nonce, ciphertext = cipher.encrypt(plaintext)

        # Tamper with ciphertext
        bad_ciphertext = b"tampered" + ciphertext
        with pytest.raises(Exception):
            cipher.decrypt(nonce, bad_ciphertext)


class TestAsymmetricEncryption:
    """Test RSA encryption/decryption."""

    def test_rsa_encrypt_decrypt(self):
        """Test RSA encryption and decryption."""
        pair = crypto.generate_rsa_keypair()
        message = b"Secret message"

        encrypted = crypto.encrypt_for_public_key(pair.public_key, message)
        assert isinstance(encrypted, bytes)
        assert encrypted != message

        decrypted = crypto.decrypt_with_private_key(pair.private_key, encrypted)
        assert decrypted == message

    def test_load_rsa_public_key(self):
        """Test loading RSA public key from PEM."""
        pair = crypto.generate_rsa_keypair()
        loaded_key = crypto.load_rsa_public_key(pair.public_key_pem)

        # Test that loaded key works
        message = b"Test"
        encrypted = crypto.encrypt_for_public_key(loaded_key, message)
        decrypted = crypto.decrypt_with_private_key(pair.private_key, encrypted)
        assert decrypted == message


class TestPasswordBasedEncryption:
    """Test password-based encryption."""

    def test_derive_key_from_passphrase(self):
        """Test key derivation from passphrase."""
        passphrase = "my-secret-password"
        salt = crypto.generate_salt()

        key = crypto.derive_key_from_passphrase(passphrase, salt)
        assert isinstance(key, bytes)
        assert len(key) == crypto.AES_KEY_SIZE

    def test_derive_key_consistent(self):
        """Test that same passphrase and salt produce same key."""
        passphrase = "my-secret-password"
        salt = crypto.generate_salt()

        key1 = crypto.derive_key_from_passphrase(passphrase, salt)
        key2 = crypto.derive_key_from_passphrase(passphrase, salt)
        assert key1 == key2

    def test_derive_key_different_salts(self):
        """Test that different salts produce different keys."""
        passphrase = "my-secret-password"
        salt1 = crypto.generate_salt()
        salt2 = crypto.generate_salt()

        key1 = crypto.derive_key_from_passphrase(passphrase, salt1)
        key2 = crypto.derive_key_from_passphrase(passphrase, salt2)
        assert key1 != key2

    def test_encrypt_decrypt_with_key(self):
        """Test encryption/decryption with derived key."""
        passphrase = "my-secret-password"
        salt = crypto.generate_salt()
        key = crypto.derive_key_from_passphrase(passphrase, salt)

        plaintext = b"Secret data"
        nonce, ciphertext = crypto.encrypt_with_key(key, plaintext)

        decrypted = crypto.decrypt_with_key(key, nonce, ciphertext)
        assert decrypted == plaintext
