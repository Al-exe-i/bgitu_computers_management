from datetime import timedelta, datetime, timezone
from typing import Optional, Literal
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from jose import jwt, JWTError
from argon2 import PasswordHasher
from core.config import settings
from utils.decorators import validate_literal_parameters

_password_hasher = PasswordHasher()

def get_password_hash(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (InvalidHashError, VerifyMismatchError):
        return False


@validate_literal_parameters
def generate_token(data: dict, token_type: Literal["access", "refresh"]) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if token_type == "access":
        expire = now + timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = now + timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": token_type})
    encoded_jwt = jwt.encode(to_encode, settings.jwt.SECRET_KEY, algorithm=settings.jwt.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: Literal["access", "refresh"]) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt.SECRET_KEY, algorithms=[settings.jwt.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None
