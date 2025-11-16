# app/dependencies/auth.py
from typing import Annotated, Literal
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import verify_token
from repositories.user import get_user
from db.session import session_dep
from models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")


async def _validate_token_and_get_user(db: AsyncSession, token: str, token_type: Literal["access", "refresh"]) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token, token_type)

    if payload is None:
        raise credentials_exception

    sub: int = int(payload.get("sub"))
    user = await get_user(db, user_id=sub)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user(
        db: session_dep,
        token: str = Depends(oauth2_scheme)
) -> User:
    user = await _validate_token_and_get_user(db, token, "access")
    return user


async def get_current_refresh_user(
        db: session_dep,
        refresh_token: str | None = Cookie(None, alias="refresh_token")
) -> User:
    if refresh_token is None:
        raise HTTPException(401, "Could not find a refresh token", {"WWW-Authenticate": "Bearer"})

    user = await _validate_token_and_get_user(db, refresh_token, "refresh")
    return user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


user_dep = Annotated[User, Depends(get_current_user)]
superuser_dep = Annotated[User, Depends(get_current_superuser)]
