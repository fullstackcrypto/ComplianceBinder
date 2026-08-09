from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse


def require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def require_not_default(name: str, default: str) -> str:
    value = require(name)
    if value == default:
        raise RuntimeError(f"{name} is still set to the unsafe default value")
    return value


def require_https_url(name: str) -> str:
    value = require(name)
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError(f"{name} must be a valid HTTPS URL")
    return value.rstrip("/")


def require_min_length(name: str, minimum: int) -> str:
    value = require(name)
    if len(value) < minimum:
        raise RuntimeError(f"{name} must be at least {minimum} characters")
    return value


def main() -> int:
    env = os.environ.get("ENV", "dev").strip().lower()
    if env not in {"staging", "prod", "production"}:
        print(f"Skipping strict launch config validation for ENV={env!r}.")
        return 0

    secret_key = require_not_default("SECRET_KEY", "CHANGE_ME_DEV_ONLY")
    if len(secret_key) < 32:
        raise RuntimeError("SECRET_KEY must be at least 32 characters in deployed environments")
    database_url = require("DATABASE_URL")
    if database_url.lower().startswith("sqlite"):
        raise RuntimeError("DATABASE_URL must use a managed database outside development")
    upload_dir = require("UPLOAD_DIR")
    if not Path(upload_dir).is_absolute():
        raise RuntimeError("UPLOAD_DIR must be an absolute persistent-storage path outside development")
    allowed_origins = require("ALLOWED_ORIGINS")
    if allowed_origins == "*":
        raise RuntimeError("ALLOWED_ORIGINS must not be '*' outside development")
    for origin in [item.strip() for item in allowed_origins.split(",") if item.strip()]:
        if urlparse(origin).scheme != "https":
            raise RuntimeError("Every ALLOWED_ORIGINS entry must use HTTPS outside development")
    public_app_url = require_https_url("PUBLIC_APP_URL")
    if "localhost" in public_app_url or "127.0.0.1" in public_app_url:
        raise RuntimeError("PUBLIC_APP_URL must not point at localhost outside development")
    require_min_length("MONITORING_SECRET", 32)
    require_min_length("REMINDER_CRON_SECRET", 32)
    require("STRIPE_SECRET_KEY")
    require("STRIPE_WEBHOOK_SECRET")
    require("STRIPE_PRICE_STARTER")
    require("STRIPE_PRICE_PRO")
    require("STRIPE_PRICE_SETUP")
    if env in {"prod", "production"}:
        require("REMINDER_FROM_EMAIL")
        require("MAIL_HOST")
        require("MAIL_USER")
        require("MAIL_KEY")
    print("Launch config validation passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Launch config validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
