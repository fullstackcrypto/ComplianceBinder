from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    base_url = require("PUBLIC_APP_URL").rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("PUBLIC_APP_URL must be an HTTPS URL")

    secret = require("REMINDER_CRON_SECRET")
    request = Request(
        f"{base_url}/reminders/run",
        method="POST",
        headers={
            "X-Cron-Secret": secret,
            "User-Agent": "ready-set-render-cron/1.0",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - URL is validated HTTPS config
            status = response.status
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Reminder endpoint returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("Reminder endpoint could not be reached") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Reminder endpoint returned invalid JSON") from exc

    if status != 200 or not payload.get("ok", False):
        raise RuntimeError(
            "Reminder run failed "
            f"(status={status}, tasks={payload.get('tasks_found', 'unknown')}, failures={payload.get('failures', 'unknown')})"
        )

    print(
        "Reminder run completed: "
        f"tasks={payload.get('tasks_found', 0)} sent={payload.get('sent', 0)} "
        f"skipped={payload.get('skipped', 0)} failures={payload.get('failures', 0)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Reminder cron failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
