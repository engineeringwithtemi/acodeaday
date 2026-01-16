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

    # Supabase Auth
    supabase_url: str = Field(
        "http://127.0.0.1:54321", description="Supabase project URL"
    )
    supabase_key: str = Field(
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
        description="Supabase anon/service role key for JWT validation"
    )

    # Default user credentials (created on startup)
    default_user_email: str = Field(
        "admin@acodeaday.local", description="Default user email"
    )
    default_user_password: str = Field(
        "changeme123", description="Default user password (min 6 chars)"
    )

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

    # LLM Settings
    llm_supported_models: str = Field(
        "gemini/gemini-2.5-flash,gemini/gemini-2.5-pro,gemini/gemini-2.0-flash,gpt-4o-mini,claude-3-5-sonnet-20241022",
        description="Comma-separated list of supported LLM models (first is default)"
    )
    llm_max_tokens: int = Field(2048, description="Maximum tokens for LLM responses")
    llm_temperature: float = Field(0.7, description="LLM temperature for response generation")
    llm_max_context_tokens: int = Field(8000, description="Maximum context tokens before truncation")

    # API Keys for LLM providers (optional - only needed if using those models)
    google_api_key: str | None = Field(None, description="Google API key for Gemini models")
    openai_api_key: str | None = Field(None, description="OpenAI API key")
    anthropic_api_key: str | None = Field(None, description="Anthropic API key")

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")


settings = Settings()
