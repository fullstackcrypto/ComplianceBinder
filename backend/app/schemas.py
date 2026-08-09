from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


BCRYPT_MAX_PASSWORD_BYTES = 72


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)

    @field_validator("password")
    @classmethod
    def password_must_fit_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            raise ValueError("Password must be at most 72 bytes when encoded")
        return value


class BinderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    industry: str = Field(default="general", min_length=1, max_length=80)


class BinderOut(BaseModel):
    id: int
    name: str
    industry: str
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
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
