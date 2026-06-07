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

    # Claude API
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Embeddings
    EMBEDDINGS_API_KEY: str = ""
    EMBEDDINGS_PROVIDER: str = "voyage"
    EMBEDDINGS_MODEL: str = "voyage-3"

    # S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = "skincare-chatbot"
    AWS_REGION: str = "us-east-1"

    # Encryption key for AES-256 (secrets, lead PII)
    ENCRYPTION_KEY: str = "change-this-32-byte-key-in-prod!"

    # reCAPTCHA
    RECAPTCHA_SECRET_KEY: str = ""

    # Rate limiting
    RATE_LIMIT_PER_IP: int = 60

    # Server
    CORS_ORIGINS: str = "http://localhost:3000"
    ENVIRONMENT: str = "production"  # Explicit "development" in .env for dev mode

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
