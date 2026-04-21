from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from loguru import logger

from core.config import settings
from core.exceptions import HTTP403, HTTP404
from dependencies.audit_actor import admin_audit_actor_dep
from dependencies.audit_log import audit_log_service_dep
from dependencies.auth import admin_dep
from dependencies.invite import invite_service_dep
from schemas.audit_log import AuditLogListResponse
from schemas.invite import InviteCreateBatch, InviteCreateOne, InviteCreateResult, InviteListItem

router = APIRouter(prefix="")


def _role_name(role) -> str | None:
    return role.name if hasattr(role, "name") else role


@router.get("/files/{file_path:path}")
async def get_protected_file(
    file_path: str,
    user: admin_dep,
):
    base_dir = Path(settings.static.root).resolve()
    safe_file_path = file_path.lstrip("/")
    requested_path = (base_dir / safe_file_path).resolve()

    try:
        requested_path.relative_to(base_dir)
    except ValueError:
        logger.warning(
            "Protected file access denied: requested_path={} base_dir={}",
            requested_path,
            base_dir,
        )
        raise HTTP403("Access Denied")

    if not requested_path.is_file():
        logger.warning("Protected file not found: {}", requested_path)
        raise HTTP404("File Not Found")

    return FileResponse(requested_path)


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
    service: invite_service_dep,
    audit: admin_audit_actor_dep,
):
    result = await service.create_one(created_by_user_id=audit.user.id, schema=data)

    await audit.log(
        action="invite.create",
        entity_type="invite",
        entity_id=result.id,
        payload={
            "target_email": result.target_email,
            "target_role": _role_name(result.target_role),
            "expires_at": result.expires_at.isoformat(),
        },
    )

    return result


@router.post("/invites/batch", response_model=list[InviteCreateResult])
async def create_invite_batch(
    data: InviteCreateBatch,
    service: invite_service_dep,
    audit: admin_audit_actor_dep,
):
    result = await service.create_batch(created_by_user_id=audit.user.id, schema=data)

    await audit.log(
        action="invite.create_batch",
        entity_type="invite",
        payload={
            "created_count": len(result),
            "target_role": _role_name(data.target_role),
            "targeted": bool(data.emails),
            "targeted_emails_count": len(data.emails or []),
            "expires_at": data.expires_at.isoformat(),
        },
    )

    return result


@router.get("/invites", response_model=list[InviteListItem])
async def list_invites(
    service: invite_service_dep,
    user: admin_dep,
):
    return await service.list_all()


@router.post("/invites/{invite_id}/revoke", response_model=InviteListItem)
async def revoke_invite(
    invite_id: int,
    service: invite_service_dep,
    audit: admin_audit_actor_dep,
):
    result = await service.revoke(invite_id)

    await audit.log(
        action="invite.revoke",
        entity_type="invite",
        entity_id=invite_id,
        payload={
            "target_email": result.target_email,
            "target_role": _role_name(result.target_role),
        },
    )

    return result


@router.delete("/invites/{invite_id}", status_code=204)
async def delete_invite(
    invite_id: int,
    service: invite_service_dep,
    audit: admin_audit_actor_dep,
):
    await service.delete(invite_id)

    await audit.log(
        action="invite.delete",
        entity_type="invite",
        entity_id=invite_id,
        payload={"invite_id": invite_id},
    )
