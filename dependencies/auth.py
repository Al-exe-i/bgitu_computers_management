# dependencies/auth.py
from typing import Annotated

from fastapi import Cookie, Depends
from fastapi.security import OAuth2PasswordBearer

from core.exceptions import HTTP401, HTTP403
from core.security import verify_access_token
from dependencies.user import user_service_dep
from modules.identity.public import AuthenticatedUser, UserOut, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token", auto_error=False)


async def _validate_token_and_get_user(
    token: str,
    service: user_service_dep,
) -> UserOut:
    credentials_exception = HTTP401("Couldn't validate credentials")

    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception

    try:
        sub = int(payload.get("sub"))
        token_version = int(payload["token_version"])
    except (KeyError, TypeError, ValueError):
        raise credentials_exception

    if payload.get("token_type") != "access":
        raise credentials_exception

    user = await service.get_for_authentication(sub)
    if user is None:
        raise credentials_exception

    if token_version != user.access_token_version:
        raise credentials_exception

    return user


async def get_current_user(
    service: user_service_dep,
    access_token_cookie: str | None = Cookie(None, alias="access_token"),
    access_token_header: str | None = Depends(oauth2_scheme),
) -> UserOut:
    token = get_access_token(access_token_cookie, access_token_header)
    user = await _validate_token_and_get_user(token, service)
    return user


def get_access_token(
    access_token_cookie: str | None = Cookie(None, alias="access_token"),
    access_token_header: str | None = Depends(oauth2_scheme),
) -> str:
    token = access_token_cookie or access_token_header
    if token is None:
        raise HTTP401("Not authenticated")
    return token


async def get_current_superuser(
    current_user: Annotated[UserOut, Depends(get_current_user)],
) -> AuthenticatedUser:
    if not current_user.is_superuser:
        raise HTTP403("Not enough permissions")
    return current_user


async def get_admin(
    current_user: Annotated[UserOut, Depends(get_current_user)],
) -> UserOut:
    if current_user.role.value > UserRole.admin.value:
        raise HTTP403("Not enough permissions")
    return current_user


user_dep = Annotated[UserOut, Depends(get_current_user)]
superuser_dep = Annotated[UserOut, Depends(get_current_superuser)]
admin_dep = Annotated[UserOut, Depends(get_admin)]
