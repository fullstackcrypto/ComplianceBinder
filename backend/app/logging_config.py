"""Privacy-preserving logging and request tracing for ComplianceBinder."""

import hashlib
import hmac
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Callable, List, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .config import settings


request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def _identity_fingerprint(value: str) -> str:
    """Return a keyed pseudonymous identifier for audit correlation."""
    if not value:
        return "-"
    normalized = value.strip().lower().encode("utf-8")
    key = settings.secret_key.encode("utf-8")
    return hmac.new(key, normalized, hashlib.sha256).hexdigest()[:12]


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


def configure_logging(log_level: str = "INFO") -> logging.Logger:
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    logger = logging.getLogger("compliancebinder")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers = [handler]
    logger.propagate = False

    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.handlers = [handler]
    return logger


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())[:12]
        request_id_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/status"]
        self.logger = logging.getLogger("compliancebinder.requests")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        start_time = time.monotonic()
        self.logger.info("Request: %s %s", request.method, request.url.path)
        response = await call_next(request)
        duration_ms = (time.monotonic() - start_time) * 1000
        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
        self.logger.log(
            log_level,
            "Response: %s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


def log_auth_event(event_type: str, email: str, success: bool, details: str = "") -> None:
    logger = logging.getLogger("compliancebinder.auth")
    status_text = "success" if success else "failed"
    message = (
        f"Auth event: {event_type} | user_ref={_identity_fingerprint(email)} | "
        f"status={status_text}"
    )
    if details:
        message += f" | details={details[:120]}"
    logger.log(logging.INFO if success else logging.WARNING, message)


def log_crud_event(
    operation: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    user_email: str = "",
    details: str = "",
) -> None:
    logger = logging.getLogger("compliancebinder.audit")
    message = f"CRUD: {operation.upper()} {resource_type}"
    if resource_id:
        message += f" id={resource_id}"
    if user_email:
        message += f" | user_ref={_identity_fingerprint(user_email)}"
    if details:
        message += f" | {details[:160]}"
    logger.info(message)
