from fastapi import APIRouter, File, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from loguru import logger

from api.v1.application_events import dispatch_result_events
from core.exceptions import (
    HTTP404,
)
from dependencies.audit_actor import (
    admin_audit_actor_dep,
    superuser_audit_actor_dep,
    user_audit_actor_dep,
)
from dependencies.auth import admin_dep, user_dep
from dependencies.events import identity_event_dispatcher_dep
from dependencies.identity import identity_user_use_cases_dep
from schemas.user import ChangePasswordSchema, UserCreate, UserOut, UserUpdate
from utils.file_responses import secure_file_headers
from utils.tokens import clear_auth_cookies

router = APIRouter()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    use_cases: identity_user_use_cases_dep,
    user_in: UserCreate,
    audit: admin_audit_actor_dep,
):
    result = await use_cases.create_user(
        data=user_in,
        audit=audit,
    )

    return result.user


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: user_dep):
    return current_user


@router.get("/all", response_model=list[UserOut])
async def get_all_users(
    use_cases: identity_user_use_cases_dep,
    _user: admin_dep,
):
    return await use_cases.list_users()


@router.get("/{user_id}", response_model=UserOut)
async def read_user(
    use_cases: identity_user_use_cases_dep,
    user_id: int,
    current_user: user_dep,
):
    return await use_cases.read_user(
        user_id=user_id,
        actor=current_user,
    )


@router.get("/me/photo")
async def get_user_photo(
    user: user_dep,
    use_cases: identity_user_use_cases_dep,
):
    photo = await use_cases.get_user_photo(user_id=user.id, actor=user)
    if photo is None:
        logger.warning("User photo not found: user_id={} no photo assigned", user.id)
        raise HTTP404("Photo not found")

    return StreamingResponse(
        photo.iter_file(),
        media_type=photo.media_type,
        headers=secure_file_headers(photo.filename),
    )


@router.get("/{user_id}/photo")
async def get_user_photo_by_id(
    user_id: int,
    current_user: user_dep,
    use_cases: identity_user_use_cases_dep,
):
    photo = await use_cases.get_user_photo(
        user_id=user_id,
        actor=current_user,
    )
    if photo is None:
        logger.warning("User photo not found: user_id={} no photo assigned", user_id)
        raise HTTP404("Photo not found")

    return StreamingResponse(
        photo.iter_file(),
        media_type=photo.media_type,
        headers=secure_file_headers(photo.filename),
    )


@router.post("/me/password", status_code=200)
async def change_password(
    data: ChangePasswordSchema,
    response: Response,
    use_cases: identity_user_use_cases_dep,
    audit: user_audit_actor_dep,
    events: identity_event_dispatcher_dep,
):
    await dispatch_result_events(
        await use_cases.change_password(
            data=data,
            actor=audit.user,
            audit=audit,
            ip=audit.meta.get("ip"),
            user_agent=audit.meta.get("user_agent"),
        ),
        events,
    )

    clear_auth_cookies(response)

    return {"message": "Password updated successfully"}


@router.delete("/{user_id}")
async def delete_user(
    use_cases: identity_user_use_cases_dep,
    user_id: int,
    audit: superuser_audit_actor_dep,
):
    await use_cases.delete_user(
        user_id=user_id,
        actor=audit.user,
        audit=audit,
    )

    return {"msg": "User deleted successfully"}


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    use_cases: identity_user_use_cases_dep,
    user_id: int,
    user_in: UserUpdate,
    audit: user_audit_actor_dep,
):
    result = await use_cases.update_user(
        user_id=user_id,
        data=user_in,
        actor=audit.user,
        audit=audit,
    )

    return result.user


@router.post("/{user_id}/photo", response_model=UserOut)
async def upload_user_photo(
    user_id: int,
    use_cases: identity_user_use_cases_dep,
    audit: user_audit_actor_dep,
    file: UploadFile = File(),
):
    result = await use_cases.upload_user_photo(
        user_id=user_id,
        file=file,
        actor=audit.user,
        audit=audit,
    )

    return result.user


@router.delete("/{user_id}/photo", response_model=UserOut)
async def delete_user_photo(
    user_id: int,
    use_cases: identity_user_use_cases_dep,
    audit: user_audit_actor_dep,
):
    result = await use_cases.delete_user_photo(
        user_id=user_id,
        actor=audit.user,
        audit=audit,
    )

    return result.user
