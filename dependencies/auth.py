# app/dependencies/auth.py

from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from core.config import settings
from core.security import verify_token
from crud.user import get_user_by_email
from db.session import session_dep
from schemas.token import TokenData
from models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")  # путь к эндпоинту логина

async def get_current_user(
        db: session_dep,
        token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt.SECRET_KEY, algorithms=[settings.jwt.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = await get_user_by_email(db, email=token_data.email)
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

    payload = verify_token(refresh_token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    token_type: str = payload.get("type")

    if email is None or token_type != "refresh":
        raise credentials_exception

    user = await get_user_by_email(db, email=email)
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