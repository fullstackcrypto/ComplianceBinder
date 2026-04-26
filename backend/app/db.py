from __future__ import annotations

from sqlmodel import SQLModel, Session, create_engine

from .config import settings


def _engine_kwargs() -> dict:
    if settings.database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


engine = create_engine(settings.database_url, **_engine_kwargs())


def init_db() -> None:
    """Create database tables for the current SQLModel metadata."""
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
