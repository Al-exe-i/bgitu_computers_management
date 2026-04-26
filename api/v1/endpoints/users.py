from fastapi import APIRouter, BackgroundTasks, File, UploadFile, status
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.exc import IntegrityError

from core.exceptions import (
    HTTP400,
    HTTP403,
    HTTP404,
    HTTP409,
    InvalidCurrentPasswordError,
    InvalidUserPhotoError,
    SamePasswordError,
    SelfDeleteForbiddenError,
    SuperuserDeleteForbiddenError,
    UserNotFoundError,
    UserPermissionDeniedError,
)
from dependencies.audit_actor import (
    admin_audit_actor_dep,
    superuser_audit_actor_dep,
    user_audit_actor_dep,
)
from dependencies.auth import admin_dep, user_dep
from dependencies.identity import identity_user_use_cases_dep
from dependencies.user import user_service_dep
from schemas.user import ChangePasswordSchema, UserCreate, UserOut, UserUpdate
from modules.identity.adapters.fastapi_events import dispatch_identity_events

router = APIRouter()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    use_cases: identity_user_use_cases_dep,
    user_in: UserCreate,
    audit: admin_audit_actor_dep,
):
    try:
        result = await use_cases.create_user(
            data=user_in,
            audit=audit,
        )
    except IntegrityError:
        logger.warning("User creation failed due to duplicate email={}", user_in.email)
        raise HTTP409("User already exists")

    return result.user


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
    use_cases: identity_user_use_cases_dep,
    user_id: int,
    current_user: user_dep,
):
    try:
        return await use_cases.read_user(
            user_id=user_id,
            actor=current_user,
        )
    except UserPermissionDeniedError as exc:
        raise HTTP403(exc.detail)
    except UserNotFoundError as exc:
        raise HTTP404(exc.detail)


@router.get("/me/photo")
async def get_user_photo(
    user: user_dep,
    service: user_service_dep,
):
    photo = service.get_photo(user)
    if photo is None:
        logger.warning("User photo not found: user_id={} no photo assigned", user.id)
        raise HTTP404("Photo not found")

    return FileResponse(photo.path, media_type=photo.media_type)


@router.post("/me/password", status_code=200)
async def change_password(
    data: ChangePasswordSchema,
    use_cases: identity_user_use_cases_dep,
    audit: user_audit_actor_dep,
    background_tasks: BackgroundTasks,
):
    try:
        result = await use_cases.change_password(
            data=data,
            actor=audit.user,
            audit=audit,
            ip=audit.meta.get("ip"),
            user_agent=audit.meta.get("user_agent"),
        )
    except (InvalidCurrentPasswordError, SamePasswordError) as exc:
        raise HTTP400(exc.detail)

    dispatch_identity_events(background_tasks, result.events)

    return {"message": "Password updated successfully"}


@router.delete("/{user_id}")
async def delete_user(
    use_cases: identity_user_use_cases_dep,
    user_id: int,
    audit: superuser_audit_actor_dep,
):
    try:
        await use_cases.delete_user(
            user_id=user_id,
            actor=audit.user,
            audit=audit,
        )
    except UserNotFoundError as exc:
        raise HTTP404(exc.detail)
    except (SelfDeleteForbiddenError, SuperuserDeleteForbiddenError) as exc:
        raise HTTP400(exc.detail)

    return {"msg": "User deleted successfully"}


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    use_cases: identity_user_use_cases_dep,
    user_id: int,
    user_in: UserUpdate,
    audit: user_audit_actor_dep,
):
    try:
        result = await use_cases.update_user(
            user_id=user_id,
            data=user_in,
            actor=audit.user,
            audit=audit,
        )
    except UserPermissionDeniedError as exc:
        raise HTTP403(exc.detail)
    except UserNotFoundError as exc:
        raise HTTP404(exc.detail)

    return result.user


@router.post("/{user_id}/photo", response_model=UserOut)
async def upload_user_photo(
    user_id: int,
    use_cases: identity_user_use_cases_dep,
    audit: user_audit_actor_dep,
    file: UploadFile = File(),
):
    try:
        result = await use_cases.upload_user_photo(
            user_id=user_id,
            file=file,
            actor=audit.user,
            audit=audit,
        )
    except InvalidUserPhotoError as exc:
        raise HTTP400(exc.detail)
    except UserPermissionDeniedError as exc:
        raise HTTP403(exc.detail)
    except UserNotFoundError as exc:
        raise HTTP404(exc.detail)

    return result.user


@router.delete("/{user_id}/photo", response_model=UserOut)
async def delete_user_photo(
    user_id: int,
    use_cases: identity_user_use_cases_dep,
    audit: user_audit_actor_dep,
):
    try:
        result = await use_cases.delete_user_photo(
            user_id=user_id,
            actor=audit.user,
            audit=audit,
        )
    except UserPermissionDeniedError as exc:
        raise HTTP403(exc.detail)
    except UserNotFoundError as exc:
        raise HTTP404(exc.detail)

    return result.user
