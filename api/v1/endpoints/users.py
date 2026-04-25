import mimetypes
import os
import uuid

import aiofiles
from fastapi import APIRouter, BackgroundTasks, File, UploadFile, status
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy.exc import IntegrityError

from core.config import settings
from core.exceptions import HTTP400, HTTP403, HTTP404, HTTP409
from core.security import verify_password
from dependencies.audit_actor import (
    admin_audit_actor_dep,
    superuser_audit_actor_dep,
    user_audit_actor_dep,
)
from dependencies.auth import admin_dep, user_dep
from dependencies.user import user_service_dep
from models.user import UserRole
from schemas.user import ChangePasswordSchema, UserCreate, UserOut, UserUpdate
from utils.audit import changed_fields
from utils.permissions import can_change_other_su
from utils.telegram_notifications import enqueue_auth_security_notification

router = APIRouter()


def _role_name(role) -> str | None:
    return role.name if hasattr(role, "name") else role


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    service: user_service_dep,
    user_in: UserCreate,
    audit: admin_audit_actor_dep,
):
    try:
        user = await service.create(user_in)
        logger.info("User created: user_id={} email={}", user.id, user.email)

        await audit.log(
            action="user.create",
            entity_type="user",
            entity_id=user.id,
            payload={
                "target_user_id": user.id,
                "email": user.email,
                "role": _role_name(user.role),
            },
        )
        return user
    except IntegrityError:
        logger.warning("User creation failed due to duplicate email={}", user_in.email)
        raise HTTP409("User already exists")


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: user_dep):
    return current_user


@router.get("/all", response_model=list[UserOut])
async def get_all_users(
    service: user_service_dep,
    user: admin_dep,
):
    return await service.get_all()


@router.get("/{user_id}", response_model=UserOut)
async def read_user(
    service: user_service_dep,
    user_id: int,
    current_user: user_dep,
):
    if current_user.id != user_id and current_user.role != UserRole.admin:
        logger.warning(
            "User read rejected: actor_id={} target_user_id={}",
            current_user.id,
            user_id,
        )
        raise HTTP403("Not enough permissions")
    user = await service.get(user_id)
    if not user:
        logger.warning("User read failed: target_user_id={} not found", user_id)
        raise HTTP404("User not found")
    return user


@router.get("/me/photo")
async def get_user_photo(user: user_dep):
    if not user.photo:
        logger.warning("User photo not found: user_id={} no photo assigned", user.id)
        raise HTTP404("Photo not found")

    file_path = os.path.join(settings.static.avatars_dir, user.photo)

    if not os.path.exists(file_path):
        logger.warning("User photo missing on disk: user_id={} path={}", user.id, file_path)
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
    audit: user_audit_actor_dep,
    background_tasks: BackgroundTasks,
):
    if not verify_password(data.current_password, audit.user.password):
        logger.warning("Password change rejected: invalid current password for user_id={}", audit.user.id)
        raise HTTP400("Неверный текущий пароль")

    if data.current_password == data.new_password:
        logger.warning("Password change rejected: new password equals old for user_id={}", audit.user.id)
        raise HTTP400("Новый пароль не должен совпадать со старым")

    await service.update(audit.user.id, UserUpdate(password=data.new_password))
    logger.info("Password changed for user_id={}", audit.user.id)

    await audit.log(
        action="user.password_change",
        entity_type="user",
        entity_id=audit.user.id,
        payload={"target_user_id": audit.user.id},
    )
    enqueue_auth_security_notification(
        background_tasks,
        user_id=audit.user.id,
        event_name="Изменён пароль аккаунта",
        ip=audit.meta.get("ip"),
        user_agent=audit.meta.get("user_agent"),
    )

    return {"message": "Password updated successfully"}


@router.delete("/{user_id}")
async def delete_user(
    service: user_service_dep,
    user_id: int,
    audit: superuser_audit_actor_dep,
):
    user = await service.get(user_id)

    if not user:
        logger.warning("User deletion failed: target_user_id={} not found", user_id)
        raise HTTP404("User not found")

    if audit.user.id == user_id:
        logger.warning("User deletion rejected: self-delete attempt user_id={}", user_id)
        raise HTTP400("You can't delete yourself")

    if user.is_superuser:
        logger.warning(
            "User deletion rejected: target_user_id={} is superuser actor_id={}",
            user_id,
            audit.user.id,
        )
        raise HTTP400("You can't delete superuser")

    await service.delete(user_id)
    logger.info("User deleted: actor_id={} target_user_id={}", audit.user.id, user_id)

    await audit.log(
        action="user.delete",
        entity_type="user",
        entity_id=user_id,
        payload={
            "target_user_id": user_id,
            "email": user.email,
            "role": _role_name(user.role),
        },
    )

    return {"msg": "User deleted successfully"}


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    service: user_service_dep,
    user_id: int,
    user_in: UserUpdate,
    audit: user_audit_actor_dep,
):
    current_user = audit.user
    if current_user.id != user_id and current_user.role != UserRole.admin and not current_user.is_superuser:
        logger.warning(
            "User update rejected: actor_id={} target_user_id={}",
            current_user.id,
            user_id,
        )
        raise HTTP403("Not enough permissions")

    user = await service.get(user_id)
    if not user:
        logger.warning("User update failed: target_user_id={} not found", user_id)
        raise HTTP404("User not found")

    try:
        can_change_other_su(current_user, user)
    except HTTP403:
        logger.warning(
            "User update rejected by superuser protection: actor_id={} target_user_id={}",
            current_user.id,
            user_id,
        )
        raise

    if current_user.id == user_id and current_user.role != UserRole.admin and not current_user.is_superuser:
        user_in = UserUpdate(**user_in.model_dump(exclude={"role"}, exclude_unset=True))

    updated_user = await service.update(user_id, user_in)
    logger.info(
        "User updated: actor_id={} target_user_id={} changed_fields={}",
        current_user.id,
        user_id,
        changed_fields(user_in),
    )

    await audit.log(
        action="user.update",
        entity_type="user",
        entity_id=user_id,
        payload={
            "target_user_id": user_id,
            "changed_fields": changed_fields(user_in),
        },
    )

    return updated_user


@router.post("/{user_id}/photo", response_model=UserOut)
async def upload_user_photo(
    user_id: int,
    service: user_service_dep,
    audit: user_audit_actor_dep,
    file: UploadFile = File(),
):
    current_user = audit.user
    if current_user.id != user_id and current_user.role != UserRole.admin and not current_user.is_superuser:
        logger.warning(
            "User photo upload rejected: actor_id={} target_user_id={}",
            current_user.id,
            user_id,
        )
        raise HTTP403("Not enough permissions")

    user = await service.get(user_id)
    if not user:
        logger.warning("User photo upload failed: target_user_id={} not found", user_id)
        raise HTTP404("User not found")

    try:
        can_change_other_su(current_user, user)
    except HTTP403:
        logger.warning(
            "User photo upload rejected by superuser protection: actor_id={} target_user_id={}",
            current_user.id,
            user_id,
        )
        raise

    if not file.content_type.startswith("image/"):
        logger.warning(
            "User photo upload rejected: invalid content type user_id={} filename={} content_type={}",
            user_id,
            file.filename,
            file.content_type,
        )
        raise HTTP400("File must be an image")

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

    if user.photo:
        try:
            os.remove(os.path.join(settings.static.avatars_dir, user.photo))
        except FileNotFoundError as exc:
            logger.error(f"Ошибка в {__name__}: {exc}")

    updated_user = await service.update(user_id, update_data)

    await audit.log(
        action="user.photo_upload",
        entity_type="user",
        entity_id=user_id,
        payload={
            "target_user_id": user_id,
            "replaced_existing": bool(user.photo),
        },
    )
    logger.info(
        "User photo uploaded: actor_id={} target_user_id={} replaced_existing={}",
        current_user.id,
        user_id,
        bool(user.photo),
    )

    return updated_user


@router.delete("/{user_id}/photo", response_model=UserOut)
async def delete_user_photo(
    user_id: int,
    service: user_service_dep,
    audit: user_audit_actor_dep,
):
    current_user = audit.user
    if current_user.id != user_id and current_user.role != UserRole.admin and not current_user.is_superuser:
        logger.warning(
            "User photo delete rejected: actor_id={} target_user_id={}",
            current_user.id,
            user_id,
        )
        raise HTTP403("Not enough permissions")

    user = await service.get(user_id)
    if not user:
        logger.warning("User photo delete failed: target_user_id={} not found", user_id)
        raise HTTP404("User not found")

    try:
        can_change_other_su(current_user, user)
    except HTTP403:
        logger.warning(
            "User photo delete rejected by superuser protection: actor_id={} target_user_id={}",
            current_user.id,
            user_id,
        )
        raise
    had_photo = bool(user.photo)

    if user.photo:
        file_path = os.path.join(settings.static.avatars_dir, user.photo)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as exc:
                logger.error(f"Ошибка в {__name__}: {exc}")

    updated_user = await service.update(user_id, UserUpdate(photo=None))

    await audit.log(
        action="user.photo_delete",
        entity_type="user",
        entity_id=user_id,
        payload={
            "target_user_id": user_id,
            "had_photo": had_photo,
        },
    )
    logger.info(
        "User photo deleted: actor_id={} target_user_id={} had_photo={}",
        current_user.id,
        user_id,
        had_photo,
    )

    return updated_user
