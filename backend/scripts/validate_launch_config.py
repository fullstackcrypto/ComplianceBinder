from __future__ import annotations

import os
import sys
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


def require_url(name: str) -> str:
    value = require(name)
    parsed = urlparse(value)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise RuntimeError(f"{name} must be a valid URL")
    return value.rstrip("/")


def main() -> int:
    env = os.environ.get("ENV", "dev").strip().lower()
    if env not in {"staging", "prod", "production"}:
        print(f"Skipping strict launch config validation for ENV={env!r}.")
        return 0

    secret_key = require_not_default("SECRET_KEY", "CHANGE_ME_DEV_ONLY")
    if len(secret_key) < 32:
        raise RuntimeError("SECRET_KEY should be at least 32 characters for deployed environments")

    require("DATABASE_URL")
    require("UPLOAD_DIR")

    allowed_origins = require("ALLOWED_ORIGINS")
    if allowed_origins == "*":
        raise RuntimeError("ALLOWED_ORIGINS must not be '*' outside development")

    public_app_url = require_url("PUBLIC_APP_URL")
    if "localhost" in public_app_url or "127.0.0.1" in public_app_url:
        raise RuntimeError("PUBLIC_APP_URL must not point at localhost outside development")

    print("Launch config validation passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Launch config validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
