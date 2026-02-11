# schemas/audit_log.py
from datetime import datetime
from pydantic import BaseModel

class AuditLogItem(BaseModel):
    id: int
    created_at: datetime
    user_id: int | None

    action: str
    entity_type: str
    entity_id: int | None

    payload: dict | None

    ip: str | None = None
    user_agent: str | None = None
    path: str | None = None
    method: str | None = None


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
