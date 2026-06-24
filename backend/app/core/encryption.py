"""At-rest encryption for secrets (API keys) and lead PII.

Scheme: **AES-256-GCM** (authenticated encryption — tamper is detected, unlike the
previous unauthenticated AES-CBC). Keys are derived from the configured key strings
with **HKDF-SHA256** (replaces the old raw single-pass SHA-256).

Key rotation: `ENCRYPTION_KEY` is the primary (used for all new encryption). Any keys
listed in `ENCRYPTION_KEYS_RETIRED` are also tried on decrypt, so data written under an
old key keeps working while you rotate. Procedure:
    1. set ENCRYPTION_KEYS_RETIRED = <old primary>, set ENCRYPTION_KEY = <new key>;
    2. let data get re-encrypted over time (any update re-encrypts with the new primary);
    3. once nothing references the old key, drop it from ENCRYPTION_KEYS_RETIRED.

Backward compatibility: blobs written by the previous AES-CBC scheme (no magic prefix)
are transparently decrypted via the legacy path, so no existing data is orphaned.

Public API is unchanged: `encrypt(str) -> bytes`, `decrypt(bytes) -> str`.
"""
import hashlib
import os

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config import get_settings

# Marks the AES-256-GCM format. Legacy AES-CBC blobs start with a random 16-byte IV,
# so the chance one collides with this 4-byte marker is ~1/2^32 (negligible).
_MAGIC = b"GCM1"
_NONCE_LEN = 12
# Fixed, non-secret HKDF parameters — derivation must be deterministic (we store no
# per-record salt). Security rests on the secret key, HKDF just yields a uniform 32-byte key.
_HKDF_SALT = b"skincare-chatbot|at-rest|v2"
_HKDF_INFO = b"aes-256-gcm-data-key"


def _key_strings() -> list[str]:
    """Configured key strings: primary first, then any retired keys (for rotation)."""
    s = get_settings()
    keys = [s.ENCRYPTION_KEY]
    retired = (s.ENCRYPTION_KEYS_RETIRED or "").strip()
    if retired:
        keys += [k.strip() for k in retired.split(",") if k.strip()]
    return keys


def _derive_key(secret: str) -> bytes:
    """Derive a 32-byte AES-256 key from a key string via HKDF-SHA256."""
    return HKDF(
        algorithm=hashes.SHA256(), length=32, salt=_HKDF_SALT, info=_HKDF_INFO
    ).derive(secret.encode("utf-8"))


def _aes_keys() -> list[bytes]:
    return [_derive_key(k) for k in _key_strings()]


def encrypt(plaintext: str) -> bytes:
    """Encrypt a string with AES-256-GCM under the primary key.

    Returns: MAGIC || nonce(12) || ciphertext+tag."""
    key = _aes_keys()[0]
    nonce = os.urandom(_NONCE_LEN)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    return _MAGIC + nonce + ct


def decrypt(encrypted: bytes) -> str:
    """Decrypt bytes produced by encrypt(). Tries each configured key (rotation),
    and falls back to the legacy AES-CBC scheme for pre-migration data.

    Raises if no key authenticates the ciphertext (tamper or wrong key)."""
    if encrypted[:4] == _MAGIC:
        nonce = encrypted[4:4 + _NONCE_LEN]
        ct = encrypted[4 + _NONCE_LEN:]
        last_err: Exception | None = None
        for key in _aes_keys():
            try:
                return AESGCM(key).decrypt(nonce, ct, None).decode("utf-8")
            except Exception as e:  # InvalidTag for a non-matching key
                last_err = e
        raise last_err or ValueError("Decryption failed: no key authenticated the ciphertext")
    return _legacy_decrypt(encrypted)


def _legacy_decrypt(encrypted: bytes) -> str:
    """Decrypt data written by the previous AES-256-CBC scheme (IV(16) || ciphertext,
    key = SHA-256(key_string)). Tried only when the GCM magic is absent."""
    iv, ciphertext = encrypted[:16], encrypted[16:]
    last_err: Exception | None = None
    for secret in _key_strings():
        key = hashlib.sha256(secret.encode("utf-8")).digest()
        try:
            decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
            padded = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            return (unpadder.update(padded) + unpadder.finalize()).decode("utf-8")
        except Exception as e:
            last_err = e
    raise last_err or ValueError("Legacy decryption failed")


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
