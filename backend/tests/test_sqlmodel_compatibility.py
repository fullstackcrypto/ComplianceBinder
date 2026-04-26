from __future__ import annotations

from sqlmodel import SQLModel

from app.models import Binder, Document, Task, User


def test_sqlmodel_relationships_configure_under_sqlalchemy_2() -> None:
    """Regression test for SQLModel/SQLAlchemy relationship annotation issues."""
    tables = SQLModel.metadata.tables

    assert "user" in tables
    assert "binder" in tables
    assert "task" in tables
    assert "document" in tables

    assert User.__mapper__.relationships["binders"].mapper.class_ is Binder
    assert Binder.__mapper__.relationships["owner"].mapper.class_ is User
    assert Binder.__mapper__.relationships["tasks"].mapper.class_ is Task
    assert Binder.__mapper__.relationships["documents"].mapper.class_ is Document
    assert Task.__mapper__.relationships["binder"].mapper.class_ is Binder
    assert Document.__mapper__.relationships["binder"].mapper.class_ is Binder
