from pathlib import Path
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from core.config import settings
from core.exceptions import HTTP403, HTTP404
from dependencies.audit_log import audit_log_service_dep
from dependencies.auth import admin_dep
from schemas.audit_log import AuditLogListResponse

router = APIRouter(prefix="")


@router.get("/files/{file_path:path}")
async def get_protected_file(
        file_path: str,
        user=admin_dep
):
    base_dir = Path(settings.static.root).resolve()

    safe_file_path = file_path.lstrip("/")

    requested_path = (base_dir / safe_file_path).resolve()

    try:
        requested_path.relative_to(base_dir)
    except ValueError:
        raise HTTP403("Access Denied")

    if not requested_path.is_file():
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

