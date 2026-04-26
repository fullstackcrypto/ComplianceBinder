from datetime import datetime, timedelta
from typing import Any, Optional

from jose import jwt
from passlib.context import CryptContext

from .config import settings


BCRYPT_MAX_PASSWORD_BYTES = 72
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def password_byte_length(password: str) -> int:
    return len(password.encode("utf-8"))


def password_fits_bcrypt(password: str) -> bool:
    return password_byte_length(password) <= BCRYPT_MAX_PASSWORD_BYTES


def hash_password(password: str) -> str:
    if not password_fits_bcrypt(password):
        raise ValueError("Password must be at most 72 bytes when UTF-8 encoded")
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if not password_fits_bcrypt(password):
        return False
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
