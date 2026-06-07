import hashlib
import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from app.config import get_settings


def _get_key() -> bytes:
    """Get the 32-byte AES-256 key from config."""
    key = get_settings().ENCRYPTION_KEY.encode("utf-8")
    # Ensure exactly 32 bytes via SHA-256 hash of the key
    return hashlib.sha256(key).digest()


def encrypt(plaintext: str) -> bytes:
    """Encrypt a string using AES-256-CBC. Returns IV + ciphertext as bytes."""
    key = _get_key()
    iv = os.urandom(16)

    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    return iv + ciphertext  # Store IV prepended to ciphertext


def decrypt(encrypted: bytes) -> str:
    """Decrypt AES-256-CBC encrypted bytes. Expects IV + ciphertext."""
    key = _get_key()
    iv = encrypted[:16]
    ciphertext = encrypted[16:]

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded) + unpadder.finalize()

    return plaintext.decode("utf-8")


def hash_value(value: str) -> str:
    """SHA-256 hash for lookup (e.g., email dedup without decrypting)."""
    return hashlib.sha256(value.lower().strip().encode("utf-8")).hexdigest()


def mask_email(email: str) -> str:
    """Mask email for display: pr***@example.com"""
    parts = email.split("@")
    if len(parts) != 2:
        return "***"
    local = parts[0]
    show = local[:2] if len(local) > 2 else local[:1]
    return f"{show}***@{parts[1]}"


def mask_phone(phone: str) -> str:
    """Mask phone for display: ***-***-1234"""
    if len(phone) >= 4:
        return f"***-***-{phone[-4:]}"
    return "***"
