# dependencies/auth.py
from typing import Annotated, Literal
from fastapi import Depends, Cookie
from fastapi.security import OAuth2PasswordBearer
from core.exceptions import HTTP403, HTTP401
from core.security import verify_token
from dependencies.user import user_service_dep
from models.user import User, UserRole
from schemas.user import UserOut

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")


async def _validate_token_and_get_user(
        token: str,
        token_type: Literal["access", "refresh"],
        service: user_service_dep
) -> UserOut:
    credentials_exception = HTTP401("Couldn't validate credentials")

    payload = verify_token(token, token_type)

    if payload is None:
        raise credentials_exception

    sub: int = int(payload.get("sub"))
    user = await service.get(sub)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user(
        service: user_service_dep,
        token: str = Depends(oauth2_scheme)
) -> UserOut:
    user = await _validate_token_and_get_user(token, "access", service)
    return user


async def get_current_refresh_user(
        service: user_service_dep,
        refresh_token: str | None = Cookie(None, alias="refresh_token")
) -> UserOut:
    if refresh_token is None:
        raise HTTP401("Couldn't find a refresh token")

    user = await _validate_token_and_get_user(refresh_token, "refresh", service)
    return user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTP403("Not enough permissions")
    return current_user


async def get_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.value > UserRole.admin.value:
        raise HTTP403("Not enough permissions")
    return current_user

user_dep = Annotated[User, Depends(get_current_user)]
superuser_dep = Annotated[User, Depends(get_current_superuser)]
admin_dep = Annotated[User, Depends(get_admin)]
