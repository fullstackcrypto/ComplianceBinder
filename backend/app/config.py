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

    def parsed_allowed_origins(self) -> List[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def parsed_allowed_content_types(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_content_types.split(",") if item.strip()}


settings = Settings()

if settings.env.lower() in {"prod", "production", "staging"} and settings.secret_key == "CHANGE_ME_DEV_ONLY":
    raise RuntimeError("Set a strong signing key before running outside development.")
