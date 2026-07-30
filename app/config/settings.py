"""
Centralized application configuration.

Why this file exists:
    Every other module needs config (DB URL, API keys, log level) but should
    never call os.getenv() directly — that scatters config-loading logic
    everywhere and makes missing variables fail silently deep inside some
    unrelated function. Instead, everything imports the single `settings`
    object below. If a required variable is missing, pydantic-settings
    raises at import time, so the app refuses to start rather than failing
    later mid-request.

Future files that depend on this:
    database/session.py (DATABASE_URL), llm/gemini_client.py (GEMINI_API_KEY),
    notifications/telegram (TELEGRAM_BOT_TOKEN) — none of that exists yet in
    V1, but the settings shape below already has placeholders for them so
    later versions don't need to restructure this file.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed application settings. Values are loaded from environment
    variables (or a local .env file in development). Field names map
    1:1 to env var names by default.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "VitaMind AI"
    env: str = Field(default="development")  # development | staging | production
    log_level: str = Field(default="INFO")

    # --- Database ---
    database_url: str = Field(default="sqlite:///./vitamind.db")

    # --- Future integrations (unused in V1, defined now so the shape is stable) ---
    gemini_api_key: str = Field(default="")
    telegram_bot_token: str = Field(default="")
    whatsapp_api_token: str = Field(default="")
    whatsapp_phone_number_id: str = Field(default="")
    vector_db_path: str = Field(default="./chroma_store")

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor. lru_cache means the .env file is parsed once
    per process, not on every import — cheap, and guarantees every part of
    the app sees the exact same settings instance.
    """
    return Settings()


settings = get_settings()
