"""At-rest encryption — issue #7 (authenticated encryption + key rotation).

BUG (before): AES-CBC with no authentication tag (malleable / no tamper detection),
unsalted single-pass SHA-256 key derivation, and no way to rotate keys without
orphaning all existing data. Now: AES-256-GCM + HKDF + multi-key rotation, with a
legacy-CBC fallback so old data still decrypts.
"""
import hashlib
import os
from unittest.mock import patch

import pytest

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.core import encryption as enc


def test_round_trip():
    blob = enc.encrypt("sk-secret-api-key-123")
    assert enc.decrypt(blob) == "sk-secret-api-key-123"


def test_output_is_gcm_format_and_not_plaintext():
    blob = enc.encrypt("hello@example.com")
    assert blob[:4] == b"GCM1"           # versioned, authenticated scheme
    assert b"hello@example.com" not in blob


def test_nonce_is_random_so_ciphertexts_differ():
    a = enc.encrypt("same-value")
    b = enc.encrypt("same-value")
    assert a != b                         # random nonce per encryption
    assert enc.decrypt(a) == enc.decrypt(b) == "same-value"


def test_tampering_is_detected():
    blob = bytearray(enc.encrypt("important"))
    blob[-1] ^= 0x01                      # flip a bit in the tag/ciphertext
    with pytest.raises(Exception):
        enc.decrypt(bytes(blob))


def test_wrong_key_cannot_decrypt():
    with patch.object(enc, "_key_strings", return_value=["key-A-original"]):
        blob = enc.encrypt("secret")
    with patch.object(enc, "_key_strings", return_value=["totally-different-key"]):
        with pytest.raises(Exception):
            enc.decrypt(blob)


def test_key_rotation():
    # Encrypted under key A...
    with patch.object(enc, "_key_strings", return_value=["KEY-A"]):
        blob = enc.encrypt("rotate-me")
    # ...after rotation primary is KEY-B but KEY-A is retired -> still decrypts.
    with patch.object(enc, "_key_strings", return_value=["KEY-B", "KEY-A"]):
        assert enc.decrypt(blob) == "rotate-me"
        # and new writes use the new primary (KEY-B)
        new_blob = enc.encrypt("fresh")
    # Once KEY-A is fully dropped, the old blob can no longer be read (expected).
    with patch.object(enc, "_key_strings", return_value=["KEY-B"]):
        assert enc.decrypt(new_blob) == "fresh"
        with pytest.raises(Exception):
            enc.decrypt(blob)


def test_legacy_cbc_blob_still_decrypts():
    """Data written by the OLD scheme (SHA-256 key + AES-CBC, IV-prepended) must
    still decrypt via the legacy fallback."""
    key_string = "legacy-master-key"
    plaintext = "old-stored-secret"

    # Reproduce the legacy format exactly.
    key = hashlib.sha256(key_string.encode()).digest()
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode()) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    legacy_blob = iv + encryptor.update(padded) + encryptor.finalize()

    with patch.object(enc, "_key_strings", return_value=[key_string]):
        assert enc.decrypt(legacy_blob) == plaintext


def test_hash_value_is_stable_and_normalized():
    assert enc.hash_value(" Foo@Bar.com ") == enc.hash_value("foo@bar.com")
    assert len(enc.hash_value("x")) == 64
