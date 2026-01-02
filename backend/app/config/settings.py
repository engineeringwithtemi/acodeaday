"""Application settings using Pydantic."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database (Supabase PostgreSQL)
    database_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres",
        description="PostgreSQL connection URL (asyncpg driver required)",
    )

    # HTTP Basic Auth (simple username/password)
    auth_username: str = Field("admin", description="Basic auth username")
    auth_password: str = Field("changeme", description="Basic auth password")

    # Judge0
    judge0_url: str = Field("http://localhost:2358", description="Judge0 API URL")

    # App config
    environment: str = Field("development")
    debug: bool = Field(False)
    project_name: str = Field("acodeaday")
    version: str = Field("0.1.0")
    log_level: str = Field("INFO")
    log_to_file: bool = Field(True)
    log_file_path: str = Field("logs/acodeaday.log")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
