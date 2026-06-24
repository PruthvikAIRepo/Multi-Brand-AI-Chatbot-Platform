"""Fail-closed config guard — issue #5.

BUG (before the fix): the app would boot in ENVIRONMENT='production' even with
the committed default SECRET_KEY / ENCRYPTION_KEY, meaning admin JWTs could be
forged and all stored secrets/PII decrypted. There was no validator.

These tests pass _env_file=None so the developer's real backend/.env is ignored
and we test the guard logic itself.
"""
import pytest
from pydantic import ValidationError

from app.config import Settings

DEFAULT_SECRET = "change-this-in-production"
DEFAULT_ENC = "change-this-32-byte-key-in-prod!"
STRONG_SECRET = "a-strong-secret-value-set-at-deploy"
STRONG_ENC = "a-strong-enough-encryption-key!!"


def test_development_allows_defaults():
    # Local dev must work out of the box with defaults.
    s = Settings(_env_file=None, ENVIRONMENT="development")
    assert s.ENVIRONMENT == "development"


def test_production_rejects_default_secret_key():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ENVIRONMENT="production",
                 SECRET_KEY=DEFAULT_SECRET, ENCRYPTION_KEY=STRONG_ENC)


def test_production_rejects_default_encryption_key():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ENVIRONMENT="production",
                 SECRET_KEY=STRONG_SECRET, ENCRYPTION_KEY=DEFAULT_ENC)


def test_production_rejects_empty_secret():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ENVIRONMENT="production",
                 SECRET_KEY="", ENCRYPTION_KEY=STRONG_ENC)


def test_production_with_real_secrets_boots():
    s = Settings(_env_file=None, ENVIRONMENT="production",
                 SECRET_KEY=STRONG_SECRET, ENCRYPTION_KEY=STRONG_ENC)
    assert s.ENVIRONMENT == "production"
