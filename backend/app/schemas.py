from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class BinderCreate(BaseModel):
    name: str
    industry: str = "general"


class BinderOut(BaseModel):
    id: int
    name: str
    industry: str
    created_at: datetime


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    due_date: Optional[date] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    due_date: Optional[date]
    created_at: datetime
    is_overdue: bool = False


class DocumentOut(BaseModel):
    id: int
    original_name: str
    content_type: str
    note: str
    uploaded_at: datetime
