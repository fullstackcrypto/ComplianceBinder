from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    pass


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    binders: List["Binder"] = Relationship(back_populates="owner", sa_relationship_kwargs={"lazy": "select"})


class Binder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    industry: str = "general"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    owner_id: int = Field(foreign_key="user.id")
    owner: Optional["User"] = Relationship(back_populates="binders", sa_relationship_kwargs={"lazy": "select"})

    tasks: List["Task"] = Relationship(back_populates="binder", sa_relationship_kwargs={"lazy": "select"})
    documents: List["Document"] = Relationship(back_populates="binder", sa_relationship_kwargs={"lazy": "select"})


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    status: str = "open"  # open | done
    due_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    binder_id: int = Field(foreign_key="binder.id")
    binder: Optional["Binder"] = Relationship(back_populates="tasks", sa_relationship_kwargs={"lazy": "select"})


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    original_name: str
    content_type: str = "application/octet-stream"
    note: str = ""
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    binder_id: int = Field(foreign_key="binder.id")
    binder: Optional["Binder"] = Relationship(back_populates="documents", sa_relationship_kwargs={"lazy": "select"})
