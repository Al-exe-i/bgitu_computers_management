from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from dependencies.administration import (
    administration_audit_log_queries_dep,
    administration_protected_file_queries_dep,
)
from dependencies.auth import admin_dep
from modules.administration.schemas import AuditLogListResponse
from utils.file_responses import secure_file_headers

router = APIRouter(prefix="")


@router.get("/files/{file_path:path}")
async def get_protected_file(
    file_path: str,
    _user: admin_dep,
    queries: administration_protected_file_queries_dep,
):
    file = await queries.get_file(file_path=file_path)

    return StreamingResponse(
        file.content,
        media_type=file.media_type,
        headers=secure_file_headers(
            file.filename,
            as_attachment=True,
        ),
    )


@router.get("/audit-log", response_model=AuditLogListResponse)
async def get_audit_log(
    queries: administration_audit_log_queries_dep,
    _user: admin_dep,
    q: str | None = None,
    user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await queries.list_entries(
        q=q,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
