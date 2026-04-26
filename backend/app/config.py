from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for ComplianceBinder."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    env: str = "dev"
    secret_key: str = "CHANGE_ME_DEV_ONLY"
    access_token_expire_minutes: int = 60 * 24 * 7

    database_url: str = "sqlite:///./compliancebinder.db"
    upload_dir: str = "./uploads"

    allowed_origins: str = "*"
    max_upload_size_bytes: int = 10 * 1024 * 1024
    allowed_content_types: str = "application/pdf,image/png,image/jpeg"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_starter: str = ""
    stripe_price_pro: str = ""
    stripe_price_setup: str = ""

    public_app_url: str = "http://localhost:8000"

    reminder_cron_secret: str = ""
    reminder_window_days: int = 7
    reminder_from_email: str = "InspectionBinder <no-reply@inspectionbinder.local>"
    mail_host: str = ""
    mail_port: int = 587
    mail_user: str = ""
    mail_key: str = ""
    mail_use_tls: bool = True

    def parsed_allowed_origins(self) -> List[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def parsed_allowed_content_types(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_content_types.split(",") if item.strip()}


settings = Settings()

if settings.env.lower() in {"prod", "production", "staging"} and settings.secret_key == "CHANGE_ME_DEV_ONLY":
    raise RuntimeError("Set a strong signing key before running outside development.")
