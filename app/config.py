"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Amadeus API
    amadeus_api_key: str = ""
    amadeus_api_secret: str = ""
    amadeus_base_url: str = "https://test.api.amadeus.com"

    # Kiwi/Tequila API
    kiwi_api_key: str = ""
    kiwi_base_url: str = "https://api.tequila.kiwi.com"

    # Duffel API
    duffel_api_token: str = ""
    duffel_base_url: str = "https://api.duffel.com"

    # Skyscanner API (optional)
    skyscanner_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/flight_agent"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # App settings
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"


def get_settings() -> Settings:
    """Return application settings instance."""
    return Settings()
