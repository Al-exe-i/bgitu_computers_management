# schemas/audit_log.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogActor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None = None
    name: str | None = None
    surname: str | None = None


class AuditLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    user_id: int | None

    # Инициатор действия (если пользователь ещё существует) — для отображения логина
    user: AuditLogActor | None = None

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
