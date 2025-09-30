# app/dependencies/auth.py
from typing import Annotated
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from core.config import settings
from core.security import verify_token
from crud.user import get_user
from db.session import session_dep
from schemas.token import TokenData
from models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")


async def get_current_user(
        db: session_dep,
        token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token, token_type="access")

    if payload is None:
        raise credentials_exception

    sub: int = int(payload.get("sub"))
    email: str = payload.get("email")
    if email is None:
        raise credentials_exception

    token_data = TokenData(id=sub, email=email)

    user = await get_user(db, user_id=int(token_data.id))
    if user is None:
        raise credentials_exception
    return user


async def get_current_refresh_user(
        db: session_dep,
        refresh_token: str | None = Cookie(None, alias="refresh_token")
) -> User:
    if refresh_token is None:
        raise HTTPException(401, "Could not find a refresh token")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(refresh_token, token_type="refresh")
    if payload is None:
        raise credentials_exception

    sub: int = int(payload.get("sub"))

    user = await get_user(db, user_id=sub)
    if user is None:
        raise credentials_exception

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
