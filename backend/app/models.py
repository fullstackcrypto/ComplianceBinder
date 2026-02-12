from __future__ import annotations

from datetime import datetime, date
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from typing import List


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    binders: "List[Binder]" = Relationship(back_populates="owner")


class Binder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    industry: str = "general"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    owner_id: int = Field(foreign_key="user.id")
    owner: "User" = Relationship(back_populates="binders")

    tasks: "List[Task]" = Relationship(back_populates="binder")
    documents: "List[Document]" = Relationship(back_populates="binder")


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    status: str = "open"  # open | done
    due_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    binder_id: int = Field(foreign_key="binder.id")
    binder: "Binder" = Relationship(back_populates="tasks")


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    original_name: str
    content_type: str = "application/octet-stream"
    note: str = ""
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    binder_id: int = Field(foreign_key="binder.id")
    binder: "Binder" = Relationship(back_populates="documents")
