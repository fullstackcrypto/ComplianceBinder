"""
Logging and middleware configuration for ComplianceBinder.

This module provides:
- Structured logging configuration
- Request ID middleware for traceability
- Request/response logging
"""

from __future__ import annotations

import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# Context variable to store request ID for the current request
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    """Logging filter that adds request_id to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


def configure_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Sets up a logger with:
    - Request ID tracking
    - Timestamp, level, and module information
    - JSON-friendly format for log aggregation
    """
    # Create a custom formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())
    
    # Set up the application logger
    logger = logging.getLogger("compliancebinder")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers = [handler]
    
    # Also configure uvicorn access logger
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.handlers = [handler]
    
    return logger


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request.
    
    The request ID is:
    - Generated as a UUID4 for each request
    - Added to the response headers as X-Request-ID
    - Available in log records via the request_id_var context variable
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        
        # Set the context variable for logging
        request_id_var.set(request_id)
        
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs request and response information.
    
    Logs include:
    - Request method and path
    - Response status code
    - Request duration in milliseconds
    """
    
    def __init__(self, app, exclude_paths: list[str] | None = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/status"]
        self.logger = logging.getLogger("compliancebinder.requests")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths (health checks, etc.)
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        start_time = time.time()
        
        # Log request
        self.logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
        self.logger.log(
            log_level,
            f"Response: {request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)"
        )
        
        return response


def log_auth_event(event_type: str, email: str, success: bool, details: str = "") -> None:
    """
    Log authentication events for audit purposes.
    
    Args:
        event_type: Type of auth event (login, register, logout)
        email: User email address
        success: Whether the operation succeeded
        details: Additional details about the event
    """
    logger = logging.getLogger("compliancebinder.auth")
    status = "success" if success else "failed"
    message = f"Auth event: {event_type} | email={email} | status={status}"
    if details:
        message += f" | details={details}"
    
    if success:
        logger.info(message)
    else:
        logger.warning(message)


def log_crud_event(
    operation: str,
    resource_type: str,
    resource_id: int | None = None,
    user_email: str = "",
    details: str = ""
) -> None:
    """
    Log CRUD operations for audit purposes.
    
    Args:
        operation: Type of operation (create, read, update, delete)
        resource_type: Type of resource (binder, task, document)
        resource_id: ID of the resource
        user_email: Email of the user performing the operation
        details: Additional details about the operation
    """
    logger = logging.getLogger("compliancebinder.audit")
    message = f"CRUD: {operation.upper()} {resource_type}"
    if resource_id:
        message += f" id={resource_id}"
    if user_email:
        message += f" | user={user_email}"
    if details:
        message += f" | {details}"
    
    logger.info(message)
