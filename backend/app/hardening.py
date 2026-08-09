"""Security middleware and lightweight abuse controls."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque
from hmac import compare_digest
from typing import Callable

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        if "Content-Security-Policy" not in response.headers:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data:; "
                "connect-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "frame-ancestors 'none'; "
                "form-action 'self'"
            )

        if settings.restricted_environment:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # During the launch phase the app mixes login, customer state, and
        # operational content on one origin. Prefer confidentiality and a
        # deterministic security posture over browser/proxy caching. Static
        # asset versioning can later re-enable immutable caching safely.
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


class AuthRateLimiter:
    """Bounded in-process brake for credential stuffing on one application instance."""

    def __init__(self) -> None:
        self._events: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    def check(self, request: Request, bucket: str) -> None:
        now = time.monotonic()
        window = max(30, settings.auth_rate_limit_window_seconds)
        max_attempts = max(5, settings.auth_rate_limit_attempts)
        max_clients = max(128, settings.auth_rate_limit_max_clients)
        client = request.client.host if request.client else "unknown"
        key = f"{bucket}:{client}"

        with self._lock:
            events = self._events.get(key)
            if events is None:
                if len(self._events) >= max_clients:
                    self._events.popitem(last=False)
                events = deque()
                self._events[key] = events
            else:
                self._events.move_to_end(key)

            while events and now - events[0] > window:
                events.popleft()
            if len(events) >= max_attempts:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many authentication attempts. Try again later.",
                    headers={"Retry-After": str(window)},
                )
            events.append(now)


auth_rate_limiter = AuthRateLimiter()


def require_monitoring_secret(request: Request) -> None:
    configured = settings.monitoring_secret
    supplied = request.headers.get("X-Monitoring-Secret", "")
    if not configured:
        raise HTTPException(status_code=503, detail="Monitoring access is not configured")
    if not supplied or not compare_digest(supplied, configured):
        raise HTTPException(status_code=401, detail="Unauthorized")
