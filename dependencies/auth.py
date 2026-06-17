# dependencies/auth.py
from typing import Annotated

from fastapi import Cookie, Depends
from fastapi.security import OAuth2PasswordBearer

from core.exceptions import HTTP401, HTTP403
from core.security import verify_access_token
from dependencies.user import user_service_dep
from models.user import User, UserRole
from schemas.user import UserOut

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
        token_version = int(payload.get("token_version", 0))
    except (TypeError, ValueError):
        raise credentials_exception

    user = await service.get(sub)
    if user is None:
        raise credentials_exception

    user_token_version = await _get_current_access_token_version(service, user)
    if user_token_version is None or token_version != user_token_version:
        raise credentials_exception

    return user


async def _get_current_access_token_version(
    service: user_service_dep,
    user: UserOut,
) -> int | None:
    get_version = getattr(service, "get_access_token_version", None)
    if get_version is not None:
        version = await get_version(user.id)
        return int(version) if version is not None else None

    return int(getattr(user, "access_token_version", 0) or 0)


async def get_current_user(
    service: user_service_dep,
    access_token_cookie: str | None = Cookie(None, alias="access_token"),
    access_token_header: str | None = Depends(oauth2_scheme),
) -> UserOut:
    token = access_token_cookie if access_token_cookie else access_token_header

    if token is None:
        raise HTTP401("Not authenticated")

    user = await _validate_token_and_get_user(token, service)
    return user


async def get_optional_user(
    service: user_service_dep,
    access_token_cookie: str | None = Cookie(None, alias="access_token"),
    access_token_header: str | None = Depends(oauth2_scheme),
) -> User | None:
    """Возвращает пользователя, если он авторизован, иначе None (без ошибки).

    Используется для эндпоинтов, доступных гостям, где часть данных нужно скрыть.
    """
    token = access_token_cookie if access_token_cookie else access_token_header
    if token is None:
        return None

    try:
        return await _validate_token_and_get_user(token, service)
    except Exception:
        return None


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTP403("Not enough permissions")
    return current_user


async def get_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.value > UserRole.admin.value:
        raise HTTP403("Not enough permissions")
    return current_user


user_dep = Annotated[User, Depends(get_current_user)]
optional_user_dep = Annotated[User | None, Depends(get_optional_user)]
superuser_dep = Annotated[User, Depends(get_current_superuser)]
admin_dep = Annotated[User, Depends(get_admin)]
