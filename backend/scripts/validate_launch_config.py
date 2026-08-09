from __future__ import annotations

import os
import sys
from email.utils import parseaddr
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


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean value")


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
    parsed_origins = [item.strip().rstrip("/") for item in allowed_origins.split(",") if item.strip()]
    for origin in parsed_origins:
        if urlparse(origin).scheme != "https":
            raise RuntimeError("Every ALLOWED_ORIGINS entry must use HTTPS outside development")

    public_app_url = require_https_url("PUBLIC_APP_URL")
    if "localhost" in public_app_url or "127.0.0.1" in public_app_url:
        raise RuntimeError("PUBLIC_APP_URL must not point at localhost outside development")
    if public_app_url not in parsed_origins:
        raise RuntimeError("PUBLIC_APP_URL must be included in ALLOWED_ORIGINS")

    require_min_length("MONITORING_SECRET", 32)
    require_min_length("REMINDER_CRON_SECRET", 32)

    stripe_secret = require("STRIPE_SECRET_KEY")
    if not stripe_secret.startswith(("sk_test_", "sk_live_")):
        raise RuntimeError("STRIPE_SECRET_KEY must be a Stripe secret key")
    webhook_secret = require("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret.startswith("whsec_"):
        raise RuntimeError("STRIPE_WEBHOOK_SECRET must be a Stripe webhook signing secret")
    for price_name in ("STRIPE_PRICE_STARTER", "STRIPE_PRICE_PRO", "STRIPE_PRICE_SETUP"):
        if not require(price_name).startswith("price_"):
            raise RuntimeError(f"{price_name} must be a Stripe Price ID")

    if env in {"prod", "production"}:
        sender = require("REMINDER_FROM_EMAIL")
        _, sender_address = parseaddr(sender)
        if "@" not in sender_address:
            raise RuntimeError("REMINDER_FROM_EMAIL must contain a valid sender email address")

        require("MAIL_HOST")
        mail_user = require("MAIL_USER")
        if "@" not in mail_user:
            raise RuntimeError("MAIL_USER must be an email-style SMTP username")
        require_min_length("MAIL_KEY", 8)

        try:
            mail_port = int(require("MAIL_PORT"))
        except ValueError as exc:
            raise RuntimeError("MAIL_PORT must be an integer") from exc
        if not 1 <= mail_port <= 65535:
            raise RuntimeError("MAIL_PORT must be between 1 and 65535")

        use_tls = env_bool("MAIL_USE_TLS", default=True)
        use_ssl = env_bool("MAIL_USE_SSL", default=False)
        if use_tls == use_ssl:
            raise RuntimeError("Exactly one of MAIL_USE_TLS or MAIL_USE_SSL must be enabled in production")

    print("Launch config validation passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Launch config validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
