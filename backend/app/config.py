from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:12345@localhost:5432/chatbot_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # First Super Admin bootstrap (read by app.seed; never hardcode credentials)
    SUPERADMIN_EMAIL: str = ""
    SUPERADMIN_PASSWORD: str = ""

    # LLM Provider (openai or anthropic)
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: int = 8
    LLM_RETRIES: int = 1
    LLM_TEMPERATURE: float = 0.7

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Anthropic (Claude) — swap when client provides key
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Embeddings
    EMBEDDINGS_PROVIDER: str = "openai"  # openai or voyage
    EMBEDDINGS_API_KEY: str = ""
    EMBEDDINGS_MODEL: str = "text-embedding-3-small"

    # S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = "skincare-chatbot"
    AWS_REGION: str = "us-east-1"

    # Encryption key for AES-256 (secrets, lead PII)
    ENCRYPTION_KEY: str = "change-this-32-byte-key-in-prod!"

    # Meta (WhatsApp + Instagram)
    META_WEBHOOK_VERIFY_TOKEN: str = "chatbot_webhook_verify_2026"
    META_APP_SECRET: str = ""  # For webhook signature verification

    # reCAPTCHA
    RECAPTCHA_SECRET_KEY: str = ""

    # Rate limiting
    RATE_LIMIT_PER_IP: int = 60
    AUTH_RATE_LIMIT_PER_IP: int = 10          # login/forgot/reset attempts per IP
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 300  # ...within this window (5 min)

    # Email (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@chatbot.com"
    SMTP_USE_TLS: bool = True
    FRONTEND_URL: str = "http://localhost:3000"

    # Server
    CORS_ORIGINS: str = "http://localhost:3000"
    # Default to development so local runs work out of the box; production
    # deploys MUST set ENVIRONMENT=production (which activates the fail-closed
    # secret check below and disables verbose error output).
    ENVIRONMENT: str = "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @model_validator(mode="after")
    def _fail_closed_on_default_secrets(self) -> "Settings":
        """Refuse to boot outside development if security-critical secrets are
        still the committed defaults or empty. Prevents shipping a deploy where
        admin JWTs can be forged or stored secrets/PII can be trivially decrypted."""
        if self.ENVIRONMENT == "development":
            return self

        insecure = {
            "SECRET_KEY": ("change-this-in-production", ""),
            "ENCRYPTION_KEY": ("change-this-32-byte-key-in-prod!", ""),
        }
        offenders = [name for name, bad in insecure.items() if getattr(self, name) in bad]
        if offenders:
            raise ValueError(
                f"Refusing to start in ENVIRONMENT='{self.ENVIRONMENT}': "
                f"{', '.join(offenders)} must be set to a strong, non-default value. "
                "Set them via environment variables before deploying."
            )
        return self

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
