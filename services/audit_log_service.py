from models.audit_log import AuditLog
from repositories.audit_log_repo import AuditLogRepository

SENSITIVE_KEYS = {"password", "access_token", "refresh_token", "token", "secret", "api_key"}

def kill_sensitive_data(payload: dict | None) -> dict | None:
    if not payload:
        return payload
    clean = {}
    for k, v in payload.items():
        if k.lower() in SENSITIVE_KEYS:
            clean[k] = "***"
        else:
            clean[k] = v
    return clean

class AuditLogService:
    def __init__(self, repo: AuditLogRepository):
        self.repo = repo

    async def log(
        self,
        *,
        user_id: int | None,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        payload: dict | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
        path: str | None = None,
        method: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=kill_sensitive_data(payload),
            ip=ip,
            user_agent=user_agent,
            path=path,
            method=method,
        )
        return await self.repo.add(entry)

    async def list(self, **kwargs):
        return await self.repo.list(**kwargs)