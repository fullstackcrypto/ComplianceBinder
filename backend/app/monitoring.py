"""
Monitoring and observability endpoints for ComplianceBinder.

This module provides:
- Health check endpoint for service availability monitoring
- Metrics endpoint for system statistics
- System status dashboard endpoint
"""

from __future__ import annotations

import logging
import platform
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, func, select

from .config import settings
from .db import engine, get_session
from .models import Binder, Document, Task, User


logger = logging.getLogger("compliancebinder.monitoring")

router = APIRouter(tags=["monitoring"])


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    database: str
    storage: str


class MetricsResponse(BaseModel):
    """System metrics response."""
    timestamp: str
    users_total: int
    binders_total: int
    tasks_total: int
    tasks_open: int
    tasks_done: int
    tasks_overdue: int
    documents_total: int
    storage_bytes: int


class SystemStatusResponse(BaseModel):
    """Comprehensive system status response."""
    timestamp: str
    version: str
    python_version: str
    uptime_seconds: float
    database_status: str
    storage_status: str
    storage_path: str
    storage_bytes: int


# Track application start time for uptime calculation
_start_time: float = time.time()


def _check_database_health() -> str:
    """Check if database is accessible."""
    try:
        with Session(engine) as session:
            session.exec(select(func.count()).select_from(User)).first()
        return "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return "unhealthy"


def _check_storage_health() -> str:
    """Check if upload directory is accessible and writable."""
    try:
        upload_path = Path(settings.upload_dir)
        if not upload_path.exists():
            return "not_configured"
        # Check if writable by attempting to create a temp file
        test_file = upload_path / ".health_check"
        test_file.touch()
        test_file.unlink()
        return "healthy"
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return "unhealthy"


def _get_storage_size() -> int:
    """Get total size of uploaded files in bytes."""
    try:
        upload_path = Path(settings.upload_dir)
        if not upload_path.exists():
            return 0
        return sum(f.stat().st_size for f in upload_path.iterdir() if f.is_file())
    except Exception as e:
        logger.error(f"Storage size calculation failed: {e}")
        return 0


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Health check endpoint for monitoring service availability.
    
    Returns the current health status of the application, including:
    - Database connectivity
    - Storage accessibility
    - Application version
    """
    db_status = _check_database_health()
    storage_status = _check_storage_health()
    
    # Overall status is healthy only if all components are healthy
    if db_status == "healthy" and storage_status == "healthy":
        overall_status = "healthy"
    else:
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        version="0.1.0",
        database=db_status,
        storage=storage_status,
    )


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(session: Session = Depends(get_session)) -> MetricsResponse:
    """
    Metrics endpoint for system statistics.
    
    Returns key metrics including:
    - Total counts for users, binders, tasks, and documents
    - Task status breakdown (open, done, overdue)
    - Storage usage in bytes
    """
    # Get counts using efficient SQL queries
    users_total = session.exec(select(func.count()).select_from(User)).first() or 0
    binders_total = session.exec(select(func.count()).select_from(Binder)).first() or 0
    tasks_total = session.exec(select(func.count()).select_from(Task)).first() or 0
    documents_total = session.exec(select(func.count()).select_from(Document)).first() or 0
    
    # Task status breakdown
    tasks_open = session.exec(
        select(func.count()).select_from(Task).where(Task.status == "open")
    ).first() or 0
    tasks_done = session.exec(
        select(func.count()).select_from(Task).where(Task.status == "done")
    ).first() or 0
    
    # Overdue tasks (open tasks with due_date in the past)
    today = date.today()
    tasks_overdue = session.exec(
        select(func.count()).select_from(Task).where(
            Task.status == "open",
            Task.due_date != None,  # noqa: E711
            Task.due_date < today
        )
    ).first() or 0
    
    storage_bytes = _get_storage_size()
    
    return MetricsResponse(
        timestamp=datetime.utcnow().isoformat(),
        users_total=users_total,
        binders_total=binders_total,
        tasks_total=tasks_total,
        tasks_open=tasks_open,
        tasks_done=tasks_done,
        tasks_overdue=tasks_overdue,
        documents_total=documents_total,
        storage_bytes=storage_bytes,
    )


@router.get("/status", response_model=SystemStatusResponse)
def system_status() -> SystemStatusResponse:
    """
    System status dashboard endpoint.
    
    Returns comprehensive system information including:
    - Application version and Python version
    - Uptime in seconds
    - Database and storage status
    - Storage path and usage
    """
    uptime = time.time() - _start_time
    db_status = _check_database_health()
    storage_status = _check_storage_health()
    storage_bytes = _get_storage_size()
    
    return SystemStatusResponse(
        timestamp=datetime.utcnow().isoformat(),
        version="0.1.0",
        python_version=platform.python_version(),
        uptime_seconds=round(uptime, 2),
        database_status=db_status,
        storage_status=storage_status,
        storage_path=str(Path(settings.upload_dir).absolute()),
        storage_bytes=storage_bytes,
    )
