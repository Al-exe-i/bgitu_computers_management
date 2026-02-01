# api/v1/endpoints/users.py
import aiofiles
import uuid
from fastapi import APIRouter, Depends, status, Cookie, UploadFile, File
from fastapi.responses import StreamingResponse
import mimetypes
from core.config import settings
from core.exceptions import HTTP403, HTTP401, HTTP404, HTTP400
from core.security import verify_password
from dependencies.user import user_service_dep
from models.user import User
from schemas.token import Token
from schemas.user import UserCreate, UserOut, UserUpdate, ChangePasswordSchema
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
    if current_user.id != user_id and not current_user.role.admin:
        raise HTTP403("Not enough permissions")
    user = await service.get(user_id)
    if not user:
        raise HTTP404("User not found")
    return user


@router.get("/me/photo")
async def get_user_photo(user: user_dep):
    if not user.photo:
        raise HTTP404("Photo not found")

    file_path = os.path.join(settings.static.avatars_dir, user.photo)

    if not os.path.exists(file_path):
        raise HTTP404("Photo not found")

    media_type, _ = mimetypes.guess_type(file_path)
    if media_type is None:
        media_type = "image/*"

    def file_iterator(path):
        with open(path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(file_iterator(file_path), media_type=media_type)


@router.post("/me/password", status_code=200)
async def change_password(
        data: ChangePasswordSchema,
        service: user_service_dep,
        current_user: user_dep
):
    """
    Смена пароля с проверкой старого.
    """

    if not verify_password(data.current_password, current_user.password):
        raise HTTP400("Неверный текущий пароль")

    if data.current_password == data.new_password:
        raise HTTP400("Новый пароль не должен совпадать со старым")

    await service.update(current_user.id, UserUpdate(password=data.new_password))

    return {"message": "Password updated successfully"}


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
    # Разрешить редактировать только себя, если не admin
    if not current_user.role.admin and current_user.id != user_id:
        raise HTTP403("Not enough permissions")

    user = await service.get(user_id)
    if not user:
        raise HTTP404("User not found")
    updated_user = await service.update(user_id, user_in)
    return updated_user


@router.post("/{user_id}/photo", response_model=UserOut)
async def upload_user_photo(
        user_id: int,
        service: user_service_dep,
        current_user: user_dep,
        file: UploadFile = File(),
):
    if not current_user.role.admin and current_user.id != user_id:
        raise HTTP403("Not enough permissions")

    if not file.content_type.startswith("image/"):
        raise HTTP400("File must be an image")

    # Генерация уникального имени файла
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4()}.{file_ext}"

    file_path = os.path.join(settings.static.avatars_dir, unique_filename)

    try:
        async with aiofiles.open(file_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)
    finally:
        file.file.close()

    update_data = UserUpdate(photo=unique_filename)

    user = await service.get(user_id)
    # Старую фотку надо удалить
    if user.photo:
        try:
            os.remove(os.path.join(settings.static.avatars_dir, user.photo))
        except FileNotFoundError: pass

    updated_user = await service.update(user_id, update_data)

    return updated_user


@router.delete("/{user_id}/photo", response_model=UserOut)
async def delete_user_photo(
        user_id: int,
        service: user_service_dep,
        current_user: user_dep
):
    if not current_user.role.admin and current_user.id != user_id:
        raise HTTP403("Not enough permissions")

    user = await service.get(user_id)
    if not user:
        raise HTTP404("User not found")

    if user.photo:
        file_path = os.path.join(settings.static.avatars_dir, user.photo)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    updated_user = await service.update(user_id, UserUpdate(photo=None))

    return updated_user


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
        current_user: User = Depends(get_current_refresh_user),
        refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    if not refresh_token:
        raise HTTP401("No refresh token provided")
    return await create_token_pair_and_build_response(user=current_user)
