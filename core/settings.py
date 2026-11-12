"""Application settings loaded from the environment."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://localhost:5432/reflection_db"


class Settings(BaseSettings):
    """Runtime configuration. Argon2id parameters can change without code edits."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    argon2_time_cost: int = 2
    argon2_memory_cost: int = 65536
    argon2_parallelism: int = 1

    jwt_secret_key: SecretStr
    jwt_issuer: str = "ai-psychologist-backend"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = Field(default=30, gt=0)
    revoked_refresh_token_retention_days: int = Field(default=30, gt=0)

    dummy_password_hash: str


def get_settings() -> Settings:
    """Build settings from environment variables and optional .env file."""
    return Settings()  # type: ignore[call-arg]
