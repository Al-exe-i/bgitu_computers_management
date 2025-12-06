# api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, status, Cookie
from fastapi.responses import StreamingResponse
import mimetypes
from core.config import settings
from core.exceptions import HTTP403, HTTP401, HTTP404, HTTP400
from dependencies.user import user_service_dep
from models.user import User
from schemas.token import Token
from schemas.user import UserCreate, UserOut, UserUpdate
from dependencies.auth import get_current_refresh_user, superuser_dep, user_dep
from utils.tokens import create_token_pair_and_build_response
import os

router = APIRouter()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
        service: user_service_dep,
        user_in: UserCreate,
        current_user: superuser_dep
):
    existing_user = await service.get_by_email(user_in.email)
    if existing_user:
        raise HTTP400("User already exists")
    user = await service.create(user_in)
    return user


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: user_dep):
    return current_user


@router.get("/{user_id}", response_model=UserOut)
async def read_user(service: user_service_dep, user_id: int, current_user: user_dep):
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTP403("Not enough permissions")
    user = await service.get(user_id)
    if not user:
        raise HTTP404("User not found")
    return user


@router.get("/me/photo")
async def get_user_photo(user: user_dep):
    if not user.photo:
        raise HTTP404("Photo not found")

    file_path = os.path.join(settings.static.upload_dir, user.photo)

    if not os.path.exists(file_path):
        raise HTTP404("Photo not found")

    media_type, _ = mimetypes.guess_type(file_path)
    if media_type is None:
        media_type = "image/*"

    def file_iterator(path):
        with open(path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(file_iterator(file_path), media_type=media_type)


@router.delete("/{user_id}")
async def delete_user(service: user_service_dep, user_id: int,
                      current_user: superuser_dep
                      ):
    user = await service.delete(user_id)
    if not user:
        raise HTTP404("User not found")
    return {"msg": "User deleted successfully"}


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
        service: user_service_dep,
        user_id: int,
        user_in: UserUpdate,
        current_user: user_dep
):
    # Разрешить редактировать только себя, если не SU
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTP403("Not enough permissions")

    user = await service.get(user_id)
    if not user:
        raise HTTP404("User not found")
    updated_user = await service.update(user_id, user_in)
    return updated_user


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
        current_user: User = Depends(get_current_refresh_user),
        refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    if not refresh_token:
        raise HTTP401("No refresh token provided")
    return await create_token_pair_and_build_response(user=current_user)
