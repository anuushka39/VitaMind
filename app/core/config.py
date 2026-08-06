"""
Central application configuration.

Every setting the app needs comes through this one Settings object instead of
scattered os.getenv() calls. Pydantic validates types (e.g. DB_PORT really is
an int) and fails fast at startup if something required is missing, rather
than failing later with a confusing runtime error.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "VitaMind"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # --- Database ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "vitamind_user"
    DB_PASSWORD: str = "changeme"
    DB_NAME: str = "vitamind_db"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # --- Gemini (Vision + Text) ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # --- Telegram Bot API ---
    TELEGRAM_BOT_TOKEN: str = ""

    # # --- WhatsApp Business Cloud API ---
    # WHATSAPP_TOKEN: str = ""
    # WHATSAPP_PHONE_NUMBER_ID: str = ""
    # WHATSAPP_VERIFY_TOKEN: str = "vitamind_verify_token"

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60

    # --- Alternate LLM (for the simple latency/quality comparison script only) ---
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def DATABASE_URL(self) -> str:
        """
        Assembles the SQLAlchemy connection string from the individual DB_*
        fields. Kept as a computed property (not a stored field) so there is
        a single source of truth — you never have to keep DB_HOST and
        DATABASE_URL in sync by hand.
        """
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    """
    Cached so the .env file is parsed once per process, not on every
    request. FastAPI's Depends() plays nicely with plain functions like this.
    """
    return Settings()


settings = get_settings()
