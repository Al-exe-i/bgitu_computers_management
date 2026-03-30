from datetime import timedelta, datetime, timezone
from typing import Literal
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from jwt import PyJWTError
import jwt
from argon2 import PasswordHasher
from core.config import settings
from core.exceptions import TokenException

_password_hasher = PasswordHasher()

def get_password_hash(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (InvalidHashError, VerifyMismatchError):
        return False


def generate_token(data: dict, token_type: Literal["access", "refresh"]) -> str:
    if token_type not in ("access", "refresh"):
        raise TokenException("Invalid token type")

    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    key = settings.jwt.ACCESS_SECRET_KEY if token_type == "access" else settings.jwt.REFRESH_SECRET_KEY

    if token_type == "access":
        expire = now + timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = now + timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "iat": now, "nbf": now, "type": token_type})
    encoded_jwt = jwt.encode(to_encode, key, algorithm=settings.jwt.ALGORITHM)

    return encoded_jwt


def verify_token(token: str, token_type: Literal["access", "refresh"]) -> dict | None:
    try:
        key = settings.jwt.ACCESS_SECRET_KEY if token_type == "access" else settings.jwt.REFRESH_SECRET_KEY
        payload = jwt.decode(token, key, algorithms=[settings.jwt.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except PyJWTError:
        return None
