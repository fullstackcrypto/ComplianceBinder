from __future__ import annotations

from sqlmodel import SQLModel, Session, create_engine

from .config import settings


def _engine_kwargs() -> dict:
    if settings.database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


engine = create_engine(settings.database_url, **_engine_kwargs())


def init_db() -> None:
    """Create tables automatically only for local/dev-style environments.

    Staging and production should run Alembic migrations instead of relying on
    SQLModel.create_all. This prevents silent schema drift once the product has
    real users.
    """
    if settings.env.lower() in {"dev", "development", "test", "ci"}:
        SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
