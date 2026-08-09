"""Monitoring endpoints with a minimal public health surface."""

from __future__ import annotations

import logging
import platform
import time
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, func, select

from .config import settings
from .db import engine, get_session
from .hardening import require_monitoring_secret
from .models import Binder, Document, Task, User
from .reminders import router as reminders_router


logger = logging.getLogger("compliancebinder.monitoring")
router = APIRouter(tags=["monitoring"])
_start_time: float = time.time()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class MetricsResponse(BaseModel):
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
    timestamp: str
    version: str
    python_version: str
    uptime_seconds: float
    database_status: str
    storage_status: str
    storage_bytes: int


def _check_database_health() -> str:
    try:
        with Session(engine) as session:
            session.exec(select(func.count()).select_from(User)).first()
        return "healthy"
    except Exception:
        logger.exception("Database health check failed")
        return "unhealthy"


def _check_storage_health() -> str:
    try:
        upload_path = Path(settings.upload_dir)
        if not upload_path.exists():
            return "not_configured"
        test_file = upload_path / ".health_check"
        test_file.touch(mode=0o600)
        test_file.unlink()
        return "healthy"
    except Exception:
        logger.exception("Storage health check failed")
        return "unhealthy"


def _get_storage_size() -> int:
    try:
        upload_path = Path(settings.upload_dir)
        if not upload_path.exists():
            return 0
        return sum(f.stat().st_size for f in upload_path.iterdir() if f.is_file())
    except Exception:
        logger.exception("Storage size calculation failed")
        return 0


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    db_status = _check_database_health()
    storage_status = _check_storage_health()
    overall_status = "healthy" if db_status == "healthy" and storage_status == "healthy" else "degraded"
    return HealthResponse(status=overall_status, timestamp=datetime.utcnow().isoformat(), version="0.3.0")


@router.get("/metrics", response_model=MetricsResponse, dependencies=[Depends(require_monitoring_secret)])
def get_metrics(session: Session = Depends(get_session)) -> MetricsResponse:
    users_total = session.exec(select(func.count()).select_from(User)).first() or 0
    binders_total = session.exec(select(func.count()).select_from(Binder)).first() or 0
    tasks_total = session.exec(select(func.count()).select_from(Task)).first() or 0
    documents_total = session.exec(select(func.count()).select_from(Document)).first() or 0
    tasks_open = session.exec(select(func.count()).select_from(Task).where(Task.status == "open")).first() or 0
    tasks_done = session.exec(select(func.count()).select_from(Task).where(Task.status == "done")).first() or 0
    today = date.today()
    tasks_overdue = session.exec(select(func.count()).select_from(Task).where(Task.status == "open", Task.due_date.is_not(None), Task.due_date < today)).first() or 0
    return MetricsResponse(timestamp=datetime.utcnow().isoformat(), users_total=users_total, binders_total=binders_total, tasks_total=tasks_total, tasks_open=tasks_open, tasks_done=tasks_done, tasks_overdue=tasks_overdue, documents_total=documents_total, storage_bytes=_get_storage_size())


@router.get("/status", response_model=SystemStatusResponse, dependencies=[Depends(require_monitoring_secret)])
def system_status() -> SystemStatusResponse:
    return SystemStatusResponse(timestamp=datetime.utcnow().isoformat(), version="0.3.0", python_version=platform.python_version(), uptime_seconds=round(time.time() - _start_time, 2), database_status=_check_database_health(), storage_status=_check_storage_health(), storage_bytes=_get_storage_size())


router.include_router(reminders_router)
