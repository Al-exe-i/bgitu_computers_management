import os
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
        user: admin_dep
):
    full_path = os.path.join(settings.static.root, file_path)

    # Безопасность: проверяем, что файл действительно находится ВНУТРИ разрешенной папки
    abs_protected_dir = os.path.abspath(settings.static.root)
    abs_requested_path = os.path.abspath(full_path)

    if not abs_requested_path.startswith(abs_protected_dir):
        raise HTTP403("Доступ запрещен")

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTP404("Файл не найден")

    return FileResponse(full_path)


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
