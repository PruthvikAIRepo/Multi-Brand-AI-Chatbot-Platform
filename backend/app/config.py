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

    # reCAPTCHA
    RECAPTCHA_SECRET_KEY: str = ""

    # Rate limiting
    RATE_LIMIT_PER_IP: int = 60

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
    ENVIRONMENT: str = "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
