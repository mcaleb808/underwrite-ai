"""Application settings loaded from environment variables."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # llm (all models via openrouter)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENAI_API_KEY: str = ""  # for embeddings (text-embedding-3-small)
    STRONG_MODEL: str = "anthropic/claude-sonnet-4.5"
    FAST_MODEL: str = "openai/gpt-4o-mini"

    # database
    DATABASE_URL: str = "sqlite+aiosqlite:///./underwrite.db"
    CHROMA_DIR: str = "./chroma_data"

    # cors
    WEB_ORIGIN: str = "http://localhost:3000"

    # email
    EMAIL_PROVIDER: Literal["resend", "smtp", "console"] = "console"
    EMAIL_FROM: str = "UnderwriteAI <underwriting@underwriteai.rw>"
    EMAIL_REPLY_TO: str = "underwriting@underwriteai.rw"
    INSURER_NAME: str = "UnderwriteAI Demo Insurer"
    RESEND_API_KEY: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    # observability
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "underwrite-ai"
    LOG_LEVEL: str = "INFO"


settings = Settings()
