from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from jwt import PyJWTError

from core.config import settings

_password_hasher = PasswordHasher()


def get_password_hash(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (InvalidHashError, VerifyMismatchError):
        return False


def generate_access_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "nbf": now,
            "token_type": "access",
        }
    )

    return jwt.encode(
        payload=to_encode,
        key=settings.jwt.ACCESS_SECRET_KEY,
        algorithm=settings.jwt.ALGORITHM,
    )


def verify_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.jwt.ACCESS_SECRET_KEY,
            algorithms=[settings.jwt.ALGORITHM],
            options={"require": ["exp", "iat", "nbf", "sub", "token_type"]},
        )
    except PyJWTError:
        return None
