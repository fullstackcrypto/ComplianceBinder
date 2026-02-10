from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration.

    Values can be overridden via environment variables or a `.env` file.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Security
    secret_key: str = "CHANGE_ME"  # override in .env
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Storage
    database_url: str = "sqlite:///./compliancebinder.db"
    upload_dir: str = "./uploads"

    # CORS
    allowed_origins: str = "*"  # for MVP; lock down later


settings = Settings()
