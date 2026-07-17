import mimetypes
from pathlib import PurePosixPath

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from core.exceptions import (
    HTTP403,
    HTTP404,
)
from dependencies.audit_actor import admin_audit_actor_dep
from dependencies.audit_log import audit_log_service_dep
from dependencies.auth import admin_dep
from dependencies.identity import identity_invite_use_cases_dep
from dependencies.storage import object_storage_dep
from schemas.audit_log import AuditLogListResponse
from schemas.invite import InviteCreateBatch, InviteCreateOne, InviteCreateResult, InviteListItem
from utils.file_responses import secure_file_headers

router = APIRouter(prefix="")


@router.get("/files/{file_path:path}")
async def get_protected_file(
    file_path: str,
    user: admin_dep,
    storage: object_storage_dep,
):
    object_key = str(PurePosixPath(file_path.replace("\\", "/").lstrip("/")))
    if object_key.startswith("../") or "/../" in object_key:
        logger.warning("Protected file access denied: object_key={}", object_key)
        raise HTTP403("Access Denied")

    if not storage.exists(object_key):
        logger.warning("Protected file not found: {}", object_key)
        raise HTTP404("File Not Found")

    media_type, _ = mimetypes.guess_type(PurePosixPath(object_key).name)

    return StreamingResponse(
        storage.iter_range(object_key),
        media_type=media_type or "application/octet-stream",
        headers=secure_file_headers(
            PurePosixPath(object_key).name,
            as_attachment=True,
        ),
    )


@router.get("/audit-log", response_model=AuditLogListResponse)
async def get_audit_log(
    service: audit_log_service_dep,
    user: admin_dep,
    q: str | None = None,
    user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items, total = await service.list(
        q=q,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total}


@router.post("/invites/one", response_model=InviteCreateResult)
async def create_invite_one(
    data: InviteCreateOne,
    use_cases: identity_invite_use_cases_dep,
    audit: admin_audit_actor_dep,
):
    result = await use_cases.create_one(
        data=data,
        created_by_user_id=audit.user.id,
        audit=audit,
    )
    return result.invite


@router.post("/invites/batch", response_model=list[InviteCreateResult])
async def create_invite_batch(
    data: InviteCreateBatch,
    use_cases: identity_invite_use_cases_dep,
    audit: admin_audit_actor_dep,
):
    result = await use_cases.create_batch(
        data=data,
        created_by_user_id=audit.user.id,
        audit=audit,
    )

    return result.invites


@router.get("/invites", response_model=list[InviteListItem])
async def list_invites(
    use_cases: identity_invite_use_cases_dep,
    user: admin_dep,
):
    return await use_cases.list_invites()


@router.post("/invites/{invite_id}/revoke", response_model=InviteListItem)
async def revoke_invite(
    invite_id: int,
    use_cases: identity_invite_use_cases_dep,
    audit: admin_audit_actor_dep,
):
    result = await use_cases.revoke(
        invite_id=invite_id,
        audit=audit,
    )

    return result.invite


@router.delete("/invites/{invite_id}", status_code=204)
async def delete_invite(
    invite_id: int,
    use_cases: identity_invite_use_cases_dep,
    audit: admin_audit_actor_dep,
):
    await use_cases.delete(
        invite_id=invite_id,
        audit=audit,
    )
