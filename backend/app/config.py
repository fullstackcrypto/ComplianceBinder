from __future__ import annotations

import secrets
from typing import List
from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Ready Set Solutions ComplianceBinder."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    env: str = "dev"
    # Development receives an ephemeral cryptographically random key. Deployed
    # environments must supply SECRET_KEY explicitly and pass validation below.
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    access_token_expire_minutes: int = 60 * 12

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

    monitoring_secret: str = ""
    auth_rate_limit_attempts: int = 20
    auth_rate_limit_window_seconds: int = 300

    reminder_cron_secret: str = ""
    reminder_window_days: int = 7
    reminder_from_email: str = "Ready Set Solutions <no-reply@charleysllc.com>"
    mail_host: str = ""
    mail_port: int = 587
    mail_user: str = ""
    mail_key: str = ""
    mail_use_tls: bool = True
    mail_use_ssl: bool = False

    def parsed_allowed_origins(self) -> List[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def parsed_allowed_content_types(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_content_types.split(",") if item.strip()}

    @property
    def restricted_environment(self) -> bool:
        return self.env.lower() in {"prod", "production", "staging"}

    @property
    def production_environment(self) -> bool:
        return self.env.lower() in {"prod", "production"}

    @property
    def public_app_scheme(self) -> str:
        return urlparse(self.public_app_url).scheme.lower()


settings = Settings()

if settings.restricted_environment:
    if "SECRET_KEY" not in settings.model_fields_set or len(settings.secret_key) < 32:
        raise RuntimeError("Set a strong explicit signing key before running outside development.")
    if settings.allowed_origins.strip() == "*":
        raise RuntimeError("Set ALLOWED_ORIGINS to the deployed app origin outside development.")
    if settings.public_app_scheme != "https":
        raise RuntimeError("PUBLIC_APP_URL must use HTTPS outside development.")
    if "localhost" in settings.public_app_url or "127.0.0.1" in settings.public_app_url:
        raise RuntimeError("Set PUBLIC_APP_URL to the deployed app URL outside development.")
    if not settings.monitoring_secret or len(settings.monitoring_secret) < 32:
        raise RuntimeError("Set a strong MONITORING_SECRET outside development.")
    if settings.mail_use_tls and settings.mail_use_ssl:
        raise RuntimeError("Configure either SMTP STARTTLS or implicit SSL, not both.")
